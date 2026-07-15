from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="Task API", version="1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        field = ".".join(str(l) for l in err["loc"])
        msg = err["msg"]
        messages.append(f"{field}: {msg}")
    return JSONResponse(status_code=400, content={"error": "; ".join(messages)})


tasks_db = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Learn FastAPI", "done": False},
]
next_id = 4


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    done: Optional[bool] = None


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    result = tasks_db
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search:
        result = [t for t in result if search.lower() in t["title"].lower()]
    return result


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=201)
def create_task(body: TaskCreate):
    global next_id
    task = {"id": next_id, "title": body.title, "done": False}
    tasks_db.append(task)
    next_id += 1
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate):
    if body.title is None and body.done is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    for task in tasks_db:
        if task["id"] == task_id:
            if body.title is not None:
                task["title"] = body.title
            if body.done is not None:
                task["done"] = body.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.get("/stats")
def stats():
    total = len(tasks_db)
    done = sum(1 for t in tasks_db if t["done"])
    return {"total": total, "done": done, "open": total - done}


@app.post("/reset")
def reset():
    global tasks_db, next_id
    tasks_db = [
        {"id": 1, "title": "Buy groceries", "done": False},
        {"id": 2, "title": "Read a book", "done": True},
        {"id": 3, "title": "Learn FastAPI", "done": False},
    ]
    next_id = 4
    return {"message": "Tasks reset to defaults"}
