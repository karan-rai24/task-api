# Task API

A CRUD API for managing a task list, built with FastAPI (Python) and SQLite.

Data persists across server restarts via a `tasks.db` file.

## Why SQLite?

SQLite requires no installation, no server process, and no configuration. The database is a single file (`tasks.db`) created automatically when the application starts. This makes it ideal for development, learning, and small-scale projects.

## How to install & run

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

The `tasks.db` file and the `tasks` table are created automatically on first run. Three sample tasks are inserted if the table is empty.

Open http://localhost:8000 in your browser.

## Endpoints

| Method | Path | Description | Status codes |
|--------|------|-------------|--------------|
| GET | `/` | API info | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{id}` | Get one task | 200, 404 |
| POST | `/tasks` | Create a task | 201, 400 |
| PUT | `/tasks/{id}` | Update a task | 200, 400, 404 |
| DELETE | `/tasks/{id}` | Delete a task | 204, 404 |
| GET | `/stats` | Task statistics | 200 |
| POST | `/reset` | Reset to sample tasks | 200 |

## Swagger UI

Open http://localhost:8000/docs for interactive API documentation.

## Example

```bash
$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Buy groceries","done":false}
```

## curl test outputs

```
$ curl -i http://localhost:8000/
HTTP/1.1 200 OK
content-type: application/json

{"name":"Task API","version":"1.0","endpoints":["/tasks"]}

$ curl -i http://localhost:8000/health
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok"}

$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
content-type: application/json

[{"id":1,"title":"Buy groceries","done":false},{"id":2,"title":"Read a book","done":true},{"id":3,"title":"Learn FastAPI","done":false}]

$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}

$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{}'
HTTP/1.1 400 Bad Request
content-type: application/json

{"error":"body.title: field required"}

$ curl -i -X PUT http://localhost:8000/tasks/1 -H "Content-Type: application/json" -d '{"title":"Updated","done":true}'
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Updated","done":true}

$ curl -i -X DELETE http://localhost:8000/tasks/2
HTTP/1.1 204 No Content

$ curl -i http://localhost:8000/tasks/99
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"Task 99 not found"}
```

## Database file

The database is stored in `tasks.db` in the project root. You can inspect it with any SQLite viewer:

```bash
sqlite3 tasks.db
```

Useful SQL queries:

```sql
-- List every task
SELECT * FROM tasks;

-- Show only completed tasks
SELECT * FROM tasks WHERE done = 1;

-- Count all tasks
SELECT COUNT(*) FROM tasks;

-- Mark every task as completed
UPDATE tasks SET done = 1;

-- Delete all completed tasks
DELETE FROM tasks WHERE done = 1;
```

## Screenshots

![Swagger UI](./screenshot.png)

## Project structure

```
task-api/
├── main.py           # FastAPI app with SQLite CRUD
├── requirements.txt  # Python dependencies
├── tasks.db          # SQLite database (auto-created)
└── README.md
```
