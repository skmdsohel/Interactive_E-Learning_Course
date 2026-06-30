"""Application configuration.

Loads settings from environment variables (.env) using Pydantic Settings.
All runtime configuration must be read from this module — never hardcode
values inside routers, services, or repositories.
"""
from functools import lru_cache
from typing import List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Query params that managed MySQL providers include in their copy-paste URLs
# but PyMySQL/SQLAlchemy don't understand. Stripped silently during
# normalization so the URL parses cleanly.
_DROP_QUERY_PARAMS = {"sslaccept", "sslmode", "ssl-mode", "ssl_mode"}


def _normalize_mysql_url(url: str) -> str:
    """Convert a user-pasted MySQL URL into a SQLAlchemy/PyMySQL-friendly form.

    * ``mysql://`` is rewritten to ``mysql+pymysql://``.
    * Provider-specific SSL hints (``sslaccept=strict`` etc.) are dropped.
      Actual TLS enablement happens in ``app.database.session`` via
      ``connect_args`` so it works uniformly across providers.
    * Ensures ``charset=utf8mb4`` is set if no charset was supplied.
    """
    if not url:
        return url
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme == "mysql":
        scheme = "mysql+pymysql"
    elif scheme.startswith("mysql+") is False and scheme.startswith("mysql"):
        # e.g. "mysqldb" - leave alone; user knows what they're doing.
        pass
    query_pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _DROP_QUERY_PARAMS
    ]
    if not any(k.lower() == "charset" for k, _ in query_pairs):
        query_pairs.append(("charset", "utf8mb4"))
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "LearnSphere API"
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
    # When set, takes precedence over the individual DB_* fields. This is the
    # only safe way to wire a connection string from a managed provider on
    # Render / Aiven / PlanetScale (which expose a single DATABASE_URL).
    DATABASE_URL_OVERRIDE: str = Field(default="", alias="DATABASE_URL")
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "lms_user"
    DB_PASSWORD: str = "lms_password"
    DB_NAME: str = "lms_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False
    # Force TLS for the MySQL connection. Auto-enabled when the URL host
    # matches a known managed provider (PlanetScale, Aiven, Clever Cloud).
    DB_SSL: bool = False

    # ---- Storage ----
    # `local` keeps everything on disk under STORAGE_ROOT (dev / Docker-compose).
    # `r2` writes uploaded videos to Cloudflare R2 (or any S3-compatible bucket).
    # `azure` writes uploaded videos to an Azure Blob Storage container.
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = "storage"
    VIDEOS_SUBDIR: str = "videos"
    THUMBNAILS_SUBDIR: str = "thumbnails"
    # Bytes per chunk for video range streaming (default 1 MiB).
    VIDEO_STREAM_CHUNK_SIZE: int = 1024 * 1024
    # Public URL prefix for static thumbnails (served by FastAPI StaticFiles).
    THUMBNAILS_URL_PREFIX: str = "/static/thumbnails"

    # ---- Cloudflare R2 / S3-compatible storage ----
    # Required when STORAGE_BACKEND=r2. The endpoint URL for R2 looks like
    # https://<account-id>.r2.cloudflarestorage.com (no path).
    R2_ENDPOINT_URL: str = ""
    R2_BUCKET: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_REGION: str = "auto"
    # Optional. If you've attached a public custom domain (or enabled
    # r2.dev access), set it here so video <source> tags hit the CDN
    # directly instead of redirecting through a presigned URL each time.
    # Example: "https://media.learnsphere.app".
    R2_PUBLIC_BASE_URL: str = ""
    # TTL for presigned GET URLs when no public base URL is configured.
    R2_PRESIGN_TTL_SECONDS: int = 3600

    # ---- Azure Blob Storage ----
    # Required when STORAGE_BACKEND=azure.
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONTAINER: str = ""
    # Optional override (e.g. for Azurite or a sovereign cloud). Defaults to
    # https://<account>.blob.core.windows.net.
    AZURE_STORAGE_ACCOUNT_URL: str = ""
    # Optional. Public CDN / custom domain in front of the container; when
    # set the streaming endpoint redirects directly here instead of issuing
    # SAS URLs. Example: "https://media.learnsphere.app".
    AZURE_PUBLIC_BASE_URL: str = ""
    # TTL for SAS GET URLs when no public base URL is configured.
    AZURE_SAS_TTL_SECONDS: int = 3600

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
        if self.DATABASE_URL_OVERRIDE:
            return _normalize_mysql_url(self.DATABASE_URL_OVERRIDE)
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