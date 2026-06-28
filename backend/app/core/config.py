"""Application configuration.

Loads settings from environment variables (.env) using Pydantic Settings.
All runtime configuration must be read from this module — never hardcode
values inside routers, services, or repositories.
"""
from functools import lru_cache
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "LMS API"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ---- Server ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ---- CORS ----
    # Comma-separated origins (e.g. "http://localhost:5173,http://localhost:3000")
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ---- Database (MySQL) ----
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "lms_user"
    DB_PASSWORD: str = "lms_password"
    DB_NAME: str = "lms_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # ---- Storage ----
    STORAGE_ROOT: str = "storage"
    VIDEOS_SUBDIR: str = "videos"
    THUMBNAILS_SUBDIR: str = "thumbnails"
    # Bytes per chunk for video range streaming (default 1 MiB).
    VIDEO_STREAM_CHUNK_SIZE: int = 1024 * 1024
    # Public URL prefix for static thumbnails (served by FastAPI StaticFiles).
    THUMBNAILS_URL_PREFIX: str = "/static/thumbnails"

    # ---- Content sync ----
    # When true, on every app startup the videos directory is scanned and the
    # database catalog is rebuilt to match it. Disable in production.
    AUTO_SEED_ON_STARTUP: bool = True
    # When true, courses whose folder was removed from disk are deleted from the DB.
    AUTO_SEED_PRUNE_MISSING: bool = True

    # ---- Auth (Google Sign-In) ----
    # OAuth 2.0 Web client ID from Google Cloud Console.
    # Must be identical on backend and frontend (VITE_GOOGLE_CLIENT_ID).
    GOOGLE_CLIENT_ID: str = ""
    # Secret used to sign the app's own JWT session tokens. Override in production.
    JWT_SECRET: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    # Comma-separated list of emails that are promoted to admin on every
    # successful Google sign-in. Anyone NOT in this list is a normal user.
    ADMIN_EMAILS: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @computed_field  # type: ignore[misc]
    @property
    def admin_emails_set(self) -> set[str]:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()