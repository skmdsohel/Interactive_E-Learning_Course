# LearnSphere Backend (FastAPI)

Production-quality FastAPI scaffold for LearnSphere. Phase 1 — **no auth**, **no business logic**, only the architectural foundation.

## Stack

- Python 3.13
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (sync) + PyMySQL
- Alembic
- Pydantic v2 + pydantic-settings
- MySQL 8

## Project layout

```
app/
  api/            # FastAPI routers (versioned under /api/v1)
  core/           # config, logging, exceptions
  database/       # engine, session, declarative Base
  models/         # SQLAlchemy ORM models (empty in Phase 1)
  repositories/   # data access layer
  schemas/        # Pydantic DTOs
  services/       # business orchestration
  utils/          # helpers
  main.py         # FastAPI app factory
alembic/          # migrations
```

### Layering rules

```
router  →  service  →  repository  →  ORM model
```

- Routers **must not** import SQLAlchemy directly.
- Services orchestrate one or more repositories.
- Repositories own all DB access.

## Local development

### 1. Create a virtual environment

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Configure environment

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
```

Edit `.env` to match your local MySQL.

### 3. Start MySQL

Either run `docker compose up mysql -d` from the repo root, or point `.env` at an existing MySQL instance. Create the database and user once:

```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lms_user'@'%' IDENTIFIED BY 'lms_password';
GRANT ALL PRIVILEGES ON lms_db.* TO 'lms_user'@'%';
FLUSH PRIVILEGES;
```

### 4. Run migrations

```bash
alembic upgrade head
```

(No migrations exist yet in Phase 1 — this is a no-op until models are added.)

### 5. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- ReDoc:      <http://localhost:8000/redoc>
- Health:     <http://localhost:8000/api/v1/health>

## Useful commands

```bash
# New migration from model changes
alembic revision --autogenerate -m "add courses table"

# Apply / roll back
alembic upgrade head
alembic downgrade -1

# Lint / type-check
ruff check .
mypy app
```

## Adding a new domain entity (template)

1. Create the model in `app/models/<entity>.py` and import it from `app/models/__init__.py`.
2. Create Pydantic schemas in `app/schemas/<entity>.py`.
3. Create a repository in `app/repositories/<entity>_repository.py` extending `BaseRepository`.
4. Create a service in `app/services/<entity>_service.py`.
5. Create the router in `app/api/v1/<entity>.py` and register it in `app/api/v1/__init__.py`.
6. Run `alembic revision --autogenerate -m "add <entity>"` and `alembic upgrade head`.

## Phase 2 (planned, not in this scaffold)

- Authentication & user management
- Course, lesson, enrollment, progress domain
- File/media handling
- Background workers
