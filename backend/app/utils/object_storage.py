"""Pluggable object storage for uploaded videos.

Two backends are supported, selected by `STORAGE_BACKEND`:

* ``local`` — files live under ``STORAGE_ROOT/VIDEOS_SUBDIR`` on disk. This is
  the default for local dev and ``docker-compose``.
* ``azure`` — files live in an Azure Blob Storage container. Uploads stream
  straight to the container; the streaming endpoint redirects the browser to
  a SAS URL (or a public CDN URL when ``AZURE_PUBLIC_BASE_URL`` is set).

Seeded-on-disk content keeps working under the cloud backend: when a key is
also present on the local filesystem we serve it locally. This lets the
``storage/videos/`` folder bundled in the Docker image keep working without
having to upload every seed file to the remote store.
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


class _AzureBlobBackend:
    """Azure Blob Storage implementation.

    Falls back to the local backend when the object key happens to exist on
    disk (useful for seeded content shipped inside the Docker image).
    """

    def __init__(self) -> None:
        from azure.storage.blob import BlobServiceClient

        missing = [
            name
            for name, val in (
                ("AZURE_STORAGE_ACCOUNT_NAME", settings.AZURE_STORAGE_ACCOUNT_NAME),
                ("AZURE_STORAGE_ACCOUNT_KEY", settings.AZURE_STORAGE_ACCOUNT_KEY),
                ("AZURE_STORAGE_CONTAINER", settings.AZURE_STORAGE_CONTAINER),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(
                "STORAGE_BACKEND=azure but the following env vars are unset: "
                + ", ".join(missing)
            )

        self._account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self._account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        self._container = settings.AZURE_STORAGE_CONTAINER
        self._account_url = (
            settings.AZURE_STORAGE_ACCOUNT_URL.rstrip("/")
            or f"https://{self._account_name}.blob.core.windows.net"
        )
        self._public_base = settings.AZURE_PUBLIC_BASE_URL.rstrip("/") or None
        self._ttl = settings.AZURE_SAS_TTL_SECONDS
        self._service = BlobServiceClient(
            account_url=self._account_url, credential=self._account_key
        )
        self._container_client = self._service.get_container_client(self._container)
        self._local_fallback = _LocalBackend()
        logger.info(
            "Azure Blob storage backend initialised (account=%s, container=%s)",
            self._account_name,
            self._container,
        )

    def _object_key(self, key: str) -> str:
        # Same layout as the local backend so DB rows stay portable:
        # `videos/<course>/<section>/<file>`.
        return f"{settings.VIDEOS_SUBDIR.strip('/')}/{key.lstrip('/')}"

    def _exists(self, key: str) -> bool:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            self._container_client.get_blob_client(self._object_key(key)).get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False

    def save_upload(
        self,
        course_slug: str,
        section_slug: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> str:
        from azure.core.exceptions import AzureError
        from azure.storage.blob import ContentSettings

        safe = sanitize_filename(filename)
        stem, _, ext = safe.rpartition(".")
        if not stem:
            stem, ext = safe, "mp4"
        candidate_key = f"{course_slug}/{section_slug}/{stem}.{ext}"
        counter = 1
        while self._exists(candidate_key):
            candidate_key = f"{course_slug}/{section_slug}/{stem}-{counter}.{ext}"
            counter += 1

        try:
            self._container_client.upload_blob(
                name=self._object_key(candidate_key),
                data=file_obj,
                overwrite=False,
                content_settings=ContentSettings(
                    content_type=_guess_content_type(filename)
                ),
            )
        except AzureError as exc:
            raise RuntimeError(f"Upload to Azure Blob failed: {exc}") from exc
        return candidate_key

    def delete(self, key: str) -> None:
        from azure.core.exceptions import AzureError

        try:
            self._container_client.delete_blob(self._object_key(key))
        except AzureError:
            logger.warning("Failed to delete Azure blob %s", key, exc_info=True)
        # Also clean any local copy (e.g. legacy seeded file).
        self._local_fallback.delete(key)

    def get_stream_target(self, key: str) -> StreamTarget:
        # Prefer a local copy if the bundled disk has it — avoids a round-trip
        # to Azure for seeded content.
        try:
            return self._local_fallback.get_stream_target(key)
        except FileNotFoundError:
            pass

        object_key = self._object_key(key)
        if self._public_base:
            return StreamTarget(redirect_url=f"{self._public_base}/{object_key}")

        from datetime import datetime, timedelta, timezone

        from azure.core.exceptions import AzureError
        from azure.storage.blob import BlobSasPermissions, generate_blob_sas

        try:
            sas = generate_blob_sas(
                account_name=self._account_name,
                container_name=self._container,
                blob_name=object_key,
                account_key=self._account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(seconds=self._ttl),
            )
        except AzureError as exc:
            raise FileNotFoundError(f"Cannot sign URL for {key}: {exc}") from exc
        return StreamTarget(
            redirect_url=f"{self._account_url}/{self._container}/{object_key}?{sas}"
        )


_backend: _LocalBackend | _AzureBlobBackend | None = None


def get_storage_backend() -> _LocalBackend | _AzureBlobBackend:
    """Lazily build (and cache) the configured backend."""
    global _backend
    if _backend is not None:
        return _backend
    kind = (settings.STORAGE_BACKEND or "local").strip().lower()
    if kind == "azure":
        _backend = _AzureBlobBackend()
    elif kind == "local":
        _backend = _LocalBackend()
    else:
        raise RuntimeError(
            f"Unknown STORAGE_BACKEND={settings.STORAGE_BACKEND!r}. "
            "Expected one of: local, azure."
        )
    return _backend
