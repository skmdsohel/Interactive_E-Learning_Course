# LearnSphere

A localhost-only Learning Management System. LearnSphere provides a
clean, production-shaped architecture for hosting authentication, courses,
enrollments, and learner progress features.

> Out of scope for the initial scaffold: login, signup, JWT, authentication, user
> management, and any course/business logic.

## Stack

| Layer    | Technology                                                  |
| -------- | ----------------------------------------------------------- |
| Backend  | Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2  |
| Database | MySQL 8                                                     |
| Frontend | React 19, Vite 6, React Router v7, Axios, Tailwind CSS v4   |
| Infra    | Docker, Docker Compose                                      |

## Repository layout

```
.
├── backend/        # FastAPI service (see backend/README.md)
├── frontend/       # React app  (see frontend/README.md)
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Architecture

```
React (Vite, :5173)
        │  axios → /api/v1/*
        ▼
FastAPI (Uvicorn, :8000)
  ├─ api/        routers
  ├─ services/   orchestration
  ├─ repositories/  data access
  └─ models/     SQLAlchemy ORM
        │
        ▼
MySQL 8 (:3306)
```

**Layering rule:** routers → services → repositories → ORM models.
Routers must not touch SQLAlchemy directly.

## Quick start (Docker)

Requires Docker Desktop.

```bash
docker compose up --build
```

- API:        <http://localhost:8000>
- API docs:   <http://localhost:8000/docs>
- Health:     <http://localhost:8000/api/v1/health>
- Frontend:   <http://localhost:5173>
- MySQL:      `localhost:3306` (user `lms_user`, password `lms_password`, db `lms_db`)

Stop:

```bash
docker compose down
```

Wipe the database volume:

```bash
docker compose down -v
```

## Quick start (local, without Docker)

### 1. MySQL

Start a MySQL 8 instance locally (Docker is fine: `docker compose up mysql -d`).
Then create the database and user:

```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lms_user'@'%' IDENTIFIED BY 'lms_password';
GRANT ALL PRIVILEGES ON lms_db.* TO 'lms_user'@'%';
FLUSH PRIVILEGES;
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

## Verifying the stack

1. Open <http://localhost:5173>.
2. Click **Health** in the top nav.
3. You should see `status: ok`, `database: ok`.

## Phase 2 readiness

The scaffold is shaped so that adding auth later requires **no structural
changes**:

- `app/api/deps.py` is the single place to introduce a `current_user`
  dependency — every router already depends on it through the established
  `Depends(...)` pattern.
- `app/core/exceptions.py` already includes `AppException` subclasses
  (`NotFoundError`, `ConflictError`, `ValidationError`) that auth flows can
  raise without touching FastAPI internals.
- `app/repositories/base.py` provides a typed CRUD base; a `UserRepository`
  drops in next to it.
- The frontend `apiClient.js` interceptor and `AppContext` are pre-wired
  injection points for token handling and `currentUser` state.
