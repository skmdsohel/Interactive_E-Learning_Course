"""Filesystem → database sync for course content.

Scans `storage/videos/` and upserts Course / Section / Video rows so that
the catalog reflects whatever is on disk. Used by both:

  * FastAPI startup lifespan (when `AUTO_SEED_ON_STARTUP=true`)
  * The CLI helper `scripts/seed_sample_courses.py`

Two on-disk layouts are supported:

  storage/videos/<course-slug>/<NN-section>/<NN-video>.mp4   (nested)
  storage/videos/<course-slug>/<NN-video>.mp4                (flat → "Lessons")

The optional leading `NN-` (digits + separator) sets `order_index` and is
stripped from the displayed title.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.course import Course, Section, Video
from app.utils.storage import thumbnails_dir, videos_dir

logger = get_logger(__name__)

VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".m4v"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_SECTION_TITLE = "Lessons"

_PREFIX_RE = re.compile(r"^\d+[-_ ]+")


def _humanize(name: str) -> str:
    return _PREFIX_RE.sub("", name).replace("-", " ").replace("_", " ").strip().title() or name


def _order_index(name: str, fallback: int) -> int:
    match = re.match(r"^(\d+)", name)
    return int(match.group(1)) if match else fallback


def _find_thumbnail(slug: str) -> str | None:
    for ext in IMAGE_EXTS:
        candidate = thumbnails_dir() / f"{slug}{ext}"
        if candidate.exists():
            return candidate.name
    return None


@dataclass
class SyncStats:
    courses_added: int = 0
    courses_updated: int = 0
    courses_removed: int = 0
    videos_indexed: int = 0


def sync_content(db: Session, *, prune_missing_courses: bool = False) -> SyncStats:
    """Mirror the on-disk video tree into the database.

    Idempotent. Re-running replaces each course's sections/videos so the DB
    always reflects the filesystem. Courses that no longer have a directory
    are removed only when `prune_missing_courses=True`.
    """
    root = videos_dir()
    if not root.exists():
        logger.info("Storage directory %s does not exist; skipping content sync.", root)
        return SyncStats()

    course_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    seen_slugs: set[str] = set()
    stats = SyncStats()

    for course_dir in course_dirs:
        slug = course_dir.name
        title = _humanize(slug)
        seen_slugs.add(slug)

        course = db.execute(select(Course).where(Course.slug == slug)).scalar_one_or_none()
        if course is None:
            course = Course(
                slug=slug,
                title=title,
                instructor="LMS Instructor",
                description=f"Auto-synced from {slug}/",
                thumbnail_path=_find_thumbnail(slug),
            )
            db.add(course)
            db.flush()
            stats.courses_added += 1
        else:
            course.title = title
            course.thumbnail_path = _find_thumbnail(slug) or course.thumbnail_path
            stats.courses_updated += 1

        # Replace sections/videos to keep this simple and idempotent.
        for s in list(course.sections):
            db.delete(s)
        db.flush()

        section_dirs = sorted(p for p in course_dir.iterdir() if p.is_dir())

        if section_dirs:
            # Nested layout: course/<section>/<video>
            for s_idx, section_dir in enumerate(section_dirs, start=1):
                videos = sorted(
                    p for p in section_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS
                )
                if not videos:
                    continue
                section = Section(
                    course_id=course.id,
                    title=_humanize(section_dir.name),
                    order_index=_order_index(section_dir.name, s_idx),
                )
                db.add(section)
                db.flush()
                _add_videos(db, section, videos, root)
                stats.videos_indexed += len(videos)
        else:
            # Flat layout: course/<video>
            videos = sorted(p for p in course_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS)
            if videos:
                section = Section(
                    course_id=course.id,
                    title=DEFAULT_SECTION_TITLE,
                    order_index=1,
                )
                db.add(section)
                db.flush()
                _add_videos(db, section, videos, root)
                stats.videos_indexed += len(videos)

    if prune_missing_courses:
        existing = db.execute(select(Course)).scalars().all()
        for c in existing:
            if c.slug not in seen_slugs:
                db.delete(c)
                stats.courses_removed += 1

    db.commit()
    logger.info(
        "Content sync: +%d courses, ~%d updated, -%d removed, %d videos indexed",
        stats.courses_added,
        stats.courses_updated,
        stats.courses_removed,
        stats.videos_indexed,
    )
    return stats


def _add_videos(db: Session, section: Section, files: list[Path], root: Path) -> None:
    for v_idx, vf in enumerate(files, start=1):
        rel = vf.relative_to(root).as_posix()
        db.add(
            Video(
                section_id=section.id,
                title=_humanize(vf.stem),
                file_path=rel,
                order_index=_order_index(vf.stem, v_idx),
            )
        )
    db.flush()
