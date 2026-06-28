"""Seed sample courses, sections, and videos by scanning the storage directory.

Layout expected on disk:

    storage/
      videos/
        <course-slug>/
          <NN-section-title>/
            <NN-video-title>.mp4
      thumbnails/
        <course-slug>.(jpg|png|webp)

Run from the `backend/` directory:

    python -m scripts.seed_sample_courses

This is a development helper. It is idempotent: re-running upserts by slug.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow running as a script from the `backend/` directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.course import Course, Section, Video  # noqa: E402
from app.utils.storage import ensure_storage_dirs, thumbnails_dir, videos_dir  # noqa: E402

VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

_PREFIX_RE = re.compile(r"^\d+[-_ ]*")


def _humanize(name: str) -> str:
    stripped = _PREFIX_RE.sub("", name)
    return stripped.replace("-", " ").replace("_", " ").strip().title()


def _order_index(name: str, fallback: int) -> int:
    match = re.match(r"^(\d+)", name)
    return int(match.group(1)) if match else fallback


def _find_thumbnail(slug: str) -> str | None:
    for ext in IMAGE_EXTS:
        candidate = thumbnails_dir() / f"{slug}{ext}"
        if candidate.exists():
            return candidate.name
    return None


def seed() -> None:
    ensure_storage_dirs()
    root = videos_dir()

    course_dirs = sorted([p for p in root.iterdir() if p.is_dir()])
    if not course_dirs:
        print(f"No course directories found under {root}. Nothing to seed.")
        return

    with SessionLocal() as db:
        for course_dir in course_dirs:
            slug = course_dir.name
            title = _humanize(slug)

            course = db.execute(select(Course).where(Course.slug == slug)).scalar_one_or_none()
            if course is None:
                course = Course(
                    slug=slug,
                    title=title,
                    instructor="LMS Instructor",
                    description=f"Auto-seeded course from {course_dir.name}/",
                    thumbnail_path=_find_thumbnail(slug),
                )
                db.add(course)
                db.flush()
                print(f"+ course {slug}")
            else:
                course.title = title
                course.thumbnail_path = _find_thumbnail(slug) or course.thumbnail_path
                print(f"= course {slug}")

            # Replace sections/videos to keep idempotency simple.
            for s in list(course.sections):
                db.delete(s)
            db.flush()

            section_dirs = sorted([p for p in course_dir.iterdir() if p.is_dir()])
            for s_idx, section_dir in enumerate(section_dirs, start=1):
                section = Section(
                    course_id=course.id,
                    title=_humanize(section_dir.name),
                    order_index=_order_index(section_dir.name, s_idx),
                )
                db.add(section)
                db.flush()

                video_files = sorted(
                    [p for p in section_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS]
                )
                for v_idx, vf in enumerate(video_files, start=1):
                    rel = vf.relative_to(root).as_posix()
                    db.add(
                        Video(
                            section_id=section.id,
                            title=_humanize(vf.stem),
                            file_path=rel,
                            order_index=_order_index(vf.stem, v_idx),
                        )
                    )
                print(f"  + section {section.title} ({len(video_files)} videos)")

        db.commit()
    print("Done.")


if __name__ == "__main__":
    seed()
