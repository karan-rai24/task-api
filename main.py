from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

app = FastAPI(title="Task API", version="1.0")

try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        use_pure=True,
    )
    cursor = db.cursor(dictionary=True)
except mysql.connector.Error:
    raise RuntimeError("Database connection failed. Check your .env settings and ensure MySQL is running.")


def to_task(row):
    row["done"] = bool(row["done"])
    return row


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        field = ".".join(str(l) for l in err["loc"])
        msg = err["msg"]
        messages.append(f"{field}: {msg}")
    return JSONResponse(status_code=400, content={"error": "; ".join(messages)})


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
    query = "SELECT * FROM api_tasks"
    conditions = []
    params = []
    if done is not None:
        conditions.append("done = %s")
        params.append(int(done))
    if search:
        conditions.append("title LIKE %s")
        params.append(f"%{search}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cursor.execute(query, params)
    return [to_task(row) for row in cursor.fetchall()]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    cursor.execute("SELECT * FROM api_tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return to_task(task)


@app.post("/tasks", status_code=201)
def create_task(body: TaskCreate):
    cursor.execute(
        "INSERT INTO api_tasks (title, done) VALUES (%s, 0)",
        (body.title,),
    )
    db.commit()
    task_id = cursor.lastrowid
    cursor.execute("SELECT * FROM api_tasks WHERE id = %s", (task_id,))
    return to_task(cursor.fetchone())


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate):
    if body.title is None and body.done is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    cursor.execute("SELECT * FROM api_tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    new_title = body.title if body.title is not None else task["title"]
    new_done = body.done if body.done is not None else bool(task["done"])
    cursor.execute(
        "UPDATE api_tasks SET title = %s, done = %s WHERE id = %s",
        (new_title, int(new_done), task_id),
    )
    db.commit()
    cursor.execute("SELECT * FROM api_tasks WHERE id = %s", (task_id,))
    return to_task(cursor.fetchone())


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    cursor.execute("SELECT * FROM api_tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    cursor.execute("DELETE FROM api_tasks WHERE id = %s", (task_id,))
    db.commit()


@app.get("/stats")
def stats():
    cursor.execute(
        "SELECT COUNT(*) AS total, SUM(done) AS done FROM api_tasks"
    )
    row = cursor.fetchone()
    total = row["total"]
    done = row["done"] or 0
    return {"total": total, "done": done, "open": total - done}


@app.post("/reset")
def reset():
    cursor.execute("TRUNCATE TABLE api_tasks")
    cursor.execute(
        "INSERT INTO api_tasks (title, done) VALUES (%s, %s), (%s, %s), (%s, %s)",
        ("Buy groceries", 0, "Read a book", 1, "Learn FastAPI", 0),
    )
    db.commit()
    return {"message": "Tasks reset to defaults"}
