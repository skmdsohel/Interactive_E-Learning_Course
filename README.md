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

## Deploying to Render

The repo ships a `render.yaml` blueprint that creates two services from this
single repo: a Dockerised backend Web Service and a static React frontend.
Render has no managed MySQL, so the database lives in **PlanetScale** and
uploaded video files live in **Cloudflare R2** (the free tier's ephemeral
disk would otherwise lose every upload on restart).

Local dev is unchanged — `docker compose up -d` still runs MySQL + backend +
frontend the way it always has. The new env vars all default to "local mode".

### 1. Prepare external services

#### PlanetScale (MySQL)
1. Create a database (any region, defaults are fine).
2. **Settings → Restrict branch FK creation**: leave OFF. The migrations use
   foreign keys with `ON DELETE CASCADE`, and PlanetScale supports them.
3. **Branches → main → Connect → Connect with: General**. Copy the URL — it
   looks like `mysql://USER:PASSWORD@aws.connect.psdb.cloud/DBNAME?sslaccept=strict`.
   You'll paste this into Render as `DATABASE_URL`; the backend auto-rewrites
   it for PyMySQL and enables TLS based on the `*.psdb.cloud` hostname.

#### Cloudflare R2 (object storage)
1. Create a bucket.
2. **Manage R2 API Tokens → Create API token** with R/W permissions on the
   bucket. Note the access key ID, secret, and the account endpoint
   `https://<account-id>.r2.cloudflarestorage.com`.
3. *(Optional)* Attach a public custom domain to the bucket for direct CDN
   reads — set it as `R2_PUBLIC_BASE_URL` to skip presigned URLs.

#### Google OAuth
In your existing OAuth client, add the deployed frontend origin (e.g.
`https://learnsphere-frontend.onrender.com`) to *Authorized JavaScript
origins*.

### 2. Apply the blueprint

In Render: **New → Blueprint** → point at this repo. Render reads
`render.yaml` and creates `learnsphere-backend` and `learnsphere-frontend`
but does not start them until secrets are set.

### 3. Set secrets in the dashboard

Backend (`learnsphere-backend` → Environment):

| Key | Value |
| --- | --- |
| `DATABASE_URL` | PlanetScale URL pasted as-is, e.g. `mysql://...@aws.connect.psdb.cloud/db?sslaccept=strict` |
| `GOOGLE_CLIENT_ID` | OAuth web client ID |
| `ADMIN_EMAILS` | comma-separated emails to auto-promote |
| `CORS_ORIGINS` | `https://learnsphere-frontend.onrender.com` |
| `R2_ENDPOINT_URL` | `https://<account-id>.r2.cloudflarestorage.com` |
| `R2_BUCKET` | bucket name |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | R2 token credentials |
| `R2_PUBLIC_BASE_URL` | *(optional)* custom domain on the bucket |

`JWT_SECRET` is auto-generated. `STORAGE_BACKEND=r2` is already wired.
`DB_SSL` is auto-enabled because the PlanetScale hostname is detected.

Frontend (`learnsphere-frontend` → Environment):

| Key | Value |
| --- | --- |
| `VITE_API_BASE_URL` | `https://learnsphere-backend.onrender.com/api/v1` |
| `VITE_GOOGLE_CLIENT_ID` | same value as backend `GOOGLE_CLIENT_ID` |

### 4. Deploy

Trigger **Manual Deploy** on both services. The backend container runs
`alembic upgrade head` automatically before starting Uvicorn. Watch the logs
for `Uvicorn running on http://0.0.0.0:10000`. Visit the frontend URL and
sign in.

> **Tip — first sign-in as admin:** the admin role is granted on every
> successful sign-in if the user's email matches `ADMIN_EMAILS`. So you can
> add yourself to `ADMIN_EMAILS` before deploying, sign in once, and you're
> an admin instantly.

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
