"""Pluggable object storage for uploaded videos.

Two backends are supported, selected by `STORAGE_BACKEND`:

* ``local`` — files live under ``STORAGE_ROOT/VIDEOS_SUBDIR`` on disk. This is
  the default for local dev and ``docker-compose``.
* ``r2``  — files live in a Cloudflare R2 bucket (or any S3-compatible store).
  Uploads stream straight to the bucket; the streaming endpoint redirects the
  browser to a presigned (or public CDN) URL instead of proxying the bytes.

Seeded-on-disk content keeps working under the ``r2`` backend: when a key is
also present on the local filesystem we serve it locally. This lets the
``storage/videos/`` folder bundled in the Docker image keep working without
having to upload every seed file to R2.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("-", name.strip()) or "file"
    return cleaned[:200]


@dataclass(frozen=True)
class StreamTarget:
    """How the streaming endpoint should serve a stored object."""
    local_path: Optional[Path] = None
    redirect_url: Optional[str] = None

    @property
    def is_local(self) -> bool:
        return self.local_path is not None


def _videos_dir() -> Path:
    return (Path(settings.STORAGE_ROOT) / settings.VIDEOS_SUBDIR).resolve()


def _safe_local_path(key: str) -> Path:
    base = _videos_dir()
    candidate = (base / key).resolve()
    if base not in candidate.parents and candidate != base:
        raise ValueError("Resolved path escapes the videos directory")
    return candidate


class _LocalBackend:
    """Disk-backed implementation. Identical to the legacy behaviour."""

    def save_upload(
        self,
        course_slug: str,
        section_slug: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> str:
        base = _videos_dir() / course_slug / section_slug
        base.mkdir(parents=True, exist_ok=True)
        safe = sanitize_filename(filename)
        stem, _, ext = safe.rpartition(".")
        if not stem:
            stem, ext = safe, "mp4"
        candidate = base / f"{stem}.{ext}"
        counter = 1
        while candidate.exists():
            candidate = base / f"{stem}-{counter}.{ext}"
            counter += 1
        with candidate.open("wb") as out:
            shutil.copyfileobj(file_obj, out)
        return candidate.relative_to(_videos_dir()).as_posix()

    def delete(self, key: str) -> None:
        try:
            path = _safe_local_path(key)
        except ValueError:
            return
        if path.exists():
            try:
                path.unlink()
            except OSError:
                logger.warning("Failed to remove %s", path, exc_info=True)

    def get_stream_target(self, key: str) -> StreamTarget:
        path = _safe_local_path(key)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Video file not found: {key}")
        return StreamTarget(local_path=path)


class _R2Backend:
    """Cloudflare R2 (S3-compatible) implementation.

    Falls back to the local backend when the object key happens to exist on
    disk (useful for seeded content shipped inside the Docker image).
    """

    def __init__(self) -> None:
        import boto3
        from botocore.config import Config

        missing = [
            name
            for name, val in (
                ("R2_ENDPOINT_URL", settings.R2_ENDPOINT_URL),
                ("R2_BUCKET", settings.R2_BUCKET),
                ("R2_ACCESS_KEY_ID", settings.R2_ACCESS_KEY_ID),
                ("R2_SECRET_ACCESS_KEY", settings.R2_SECRET_ACCESS_KEY),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(
                "STORAGE_BACKEND=r2 but the following env vars are unset: "
                + ", ".join(missing)
            )

        self._bucket = settings.R2_BUCKET
        self._public_base = settings.R2_PUBLIC_BASE_URL.rstrip("/") or None
        self._ttl = settings.R2_PRESIGN_TTL_SECONDS
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name=settings.R2_REGION,
            config=Config(signature_version="s3v4"),
        )
        self._local_fallback = _LocalBackend()
        logger.info("R2 storage backend initialised (bucket=%s)", self._bucket)

    def _object_key(self, key: str) -> str:
        # Mirror the local layout exactly so the same DB string works in both
        # modes: `videos/<course>/<section>/<file>`.
        return f"{settings.VIDEOS_SUBDIR.strip('/')}/{key.lstrip('/')}"

    def save_upload(
        self,
        course_slug: str,
        section_slug: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> str:
        safe = sanitize_filename(filename)
        stem, _, ext = safe.rpartition(".")
        if not stem:
            stem, ext = safe, "mp4"
        candidate_key = f"{course_slug}/{section_slug}/{stem}.{ext}"
        counter = 1
        while self._exists(candidate_key):
            candidate_key = f"{course_slug}/{section_slug}/{stem}-{counter}.{ext}"
            counter += 1
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self._client.upload_fileobj(
                file_obj,
                self._bucket,
                self._object_key(candidate_key),
                ExtraArgs={"ContentType": _guess_content_type(filename)},
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Upload to R2 failed: {exc}") from exc
        return candidate_key

    def _exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=self._object_key(key))
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def delete(self, key: str) -> None:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self._client.delete_object(Bucket=self._bucket, Key=self._object_key(key))
        except (BotoCoreError, ClientError):
            logger.warning("Failed to delete R2 object %s", key, exc_info=True)
        # Also clean any local copy (e.g. legacy seeded file).
        self._local_fallback.delete(key)

    def get_stream_target(self, key: str) -> StreamTarget:
        # Prefer a local copy if the bundled disk has it — avoids a round-trip
        # to R2 for seeded content.
        try:
            return self._local_fallback.get_stream_target(key)
        except FileNotFoundError:
            pass

        object_key = self._object_key(key)
        if self._public_base:
            return StreamTarget(redirect_url=f"{self._public_base}/{object_key}")

        from botocore.exceptions import BotoCoreError, ClientError

        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": object_key},
                ExpiresIn=self._ttl,
            )
        except (BotoCoreError, ClientError) as exc:
            raise FileNotFoundError(f"Cannot sign URL for {key}: {exc}") from exc
        return StreamTarget(redirect_url=url)


_MIME_BY_EXT = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".m4v": "video/x-m4v",
}


def _guess_content_type(filename: str) -> str:
    return _MIME_BY_EXT.get(Path(filename).suffix.lower(), "application/octet-stream")


_backend: _LocalBackend | _R2Backend | None = None


def get_storage_backend() -> _LocalBackend | _R2Backend:
    """Lazily build (and cache) the configured backend."""
    global _backend
    if _backend is not None:
        return _backend
    kind = (settings.STORAGE_BACKEND or "local").strip().lower()
    if kind == "r2":
        _backend = _R2Backend()
    elif kind == "local":
        _backend = _LocalBackend()
    else:
        raise RuntimeError(
            f"Unknown STORAGE_BACKEND={settings.STORAGE_BACKEND!r}. "
            "Expected one of: local, r2."
        )
    return _backend
