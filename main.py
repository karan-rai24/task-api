import sqlite3
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

DB_FILE = "tasks.db"

app = FastAPI(title="Task API", version="1.0")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.on_event("startup")
def startup():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT NOT NULL,"
        "done INTEGER NOT NULL DEFAULT 0)"
    )
    count = conn.execute("SELECT COUNT(*) AS cnt FROM tasks").fetchone()["cnt"]
    if count == 0:
        conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?), (?, ?), (?, ?)",
            ("Buy groceries", 0, "Read a book", 1, "Learn FastAPI", 0),
        )
        conn.commit()
    conn.close()


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
    conn = get_db()
    query = "SELECT * FROM tasks"
    conditions = []
    params = []
    if done is not None:
        conditions.append("done = ?")
        params.append(int(done))
    if search:
        conditions.append("title LIKE ?")
        params.append(f"%{search}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [to_task(row) for row in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return to_task(row)


@app.post("/tasks", status_code=201)
def create_task(body: TaskCreate):
    conn = get_db()
    cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (body.title,))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return to_task(row)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate):
    if body.title is None and body.done is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    new_title = body.title if body.title is not None else row["title"]
    new_done = body.done if body.done is not None else bool(row["done"])
    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, int(new_done), task_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return to_task(updated)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


@app.get("/stats")
def stats():
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(done) AS done FROM tasks"
    ).fetchone()
    conn.close()
    total = row["total"]
    done_count = row["done"] or 0
    return {"total": total, "done": done_count, "open": total - done_count}


@app.post("/reset")
def reset():
    conn = get_db()
    conn.execute("DELETE FROM tasks")
    conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?), (?, ?), (?, ?)",
        ("Buy groceries", 0, "Read a book", 1, "Learn FastAPI", 0),
    )
    conn.commit()
    conn.close()
    return {"message": "Tasks reset to defaults"}
