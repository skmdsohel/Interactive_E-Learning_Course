"""Storage path helpers for video and thumbnail files.

All paths in the database are *relative* to the configured storage root.
This module is the only place that joins those relative paths with the
absolute on-disk location.
"""
from pathlib import Path

from app.core.config import settings


def storage_root() -> Path:
    return Path(settings.STORAGE_ROOT).resolve()


def videos_dir() -> Path:
    return storage_root() / settings.VIDEOS_SUBDIR


def thumbnails_dir() -> Path:
    return storage_root() / settings.THUMBNAILS_SUBDIR


def ensure_storage_dirs() -> None:
    videos_dir().mkdir(parents=True, exist_ok=True)
    thumbnails_dir().mkdir(parents=True, exist_ok=True)


def resolve_video_path(relative_path: str) -> Path:
    """Resolve a stored relative path to an absolute path, preventing traversal."""
    base = videos_dir()
    candidate = (base / relative_path).resolve()
    if base not in candidate.parents and candidate != base:
        raise ValueError("Resolved path escapes the videos directory")
    return candidate


def thumbnail_url(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    prefix = settings.THUMBNAILS_URL_PREFIX.rstrip("/")
    return f"{prefix}/{relative_path.lstrip('/')}"
