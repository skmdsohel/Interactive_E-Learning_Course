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

Sync is **upsert by natural key** so DB ids stay stable across restarts:
  * Section is keyed by (course_id, title)
  * Video   is keyed by (section_id, file_path)
This matters because user progress rows reference video.id.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.course import Course, Section, Video
from app.models.quiz import Quiz, QuizQuestion
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
    sections_added: int = 0
    sections_removed: int = 0
    videos_added: int = 0
    videos_removed: int = 0
    videos_indexed: int = 0
    quizzes_added: int = 0


def sync_content(db: Session, *, prune_missing_courses: bool = False) -> SyncStats:
    """Mirror the on-disk video tree into the database.

    Idempotent and id-stable: existing sections/videos are kept and only the
    metadata (title, order_index) is refreshed. New entries are inserted,
    and entries whose files no longer exist are removed.
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
                instructor="LearnSphere Instructor",
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

        _sync_course_tree(db, course, course_dir, root, stats)

    if prune_missing_courses:
        existing = db.execute(select(Course)).scalars().all()
        for c in existing:
            if c.slug in seen_slugs:
                continue
            # Never prune courses authored through the instructor UI — they
            # don't exist on disk by design.
            if c.instructor_id is not None:
                continue
            db.delete(c)
            stats.courses_removed += 1

    db.commit()
    logger.info(
        "Content sync: +%d courses, ~%d updated, -%d removed, "
        "+%d sections / -%d, +%d videos / -%d (indexed %d), +%d quizzes",
        stats.courses_added,
        stats.courses_updated,
        stats.courses_removed,
        stats.sections_added,
        stats.sections_removed,
        stats.videos_added,
        stats.videos_removed,
        stats.videos_indexed,
        stats.quizzes_added,
    )
    return stats


def _sync_course_tree(
    db: Session,
    course: Course,
    course_dir: Path,
    root: Path,
    stats: SyncStats,
) -> None:
    """Build the desired (section_title -> [video_files]) map and reconcile."""
    desired: dict[str, tuple[int, list[Path]]] = {}

    section_dirs = sorted(p for p in course_dir.iterdir() if p.is_dir())
    if section_dirs:
        for s_idx, section_dir in enumerate(section_dirs, start=1):
            videos = sorted(
                p for p in section_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS
            )
            if not videos:
                continue
            desired[_humanize(section_dir.name)] = (
                _order_index(section_dir.name, s_idx),
                videos,
            )
    else:
        videos = sorted(
            p for p in course_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS
        )
        if videos:
            desired[DEFAULT_SECTION_TITLE] = (1, videos)

    existing_sections = {s.title: s for s in course.sections}

    # Remove sections that no longer exist on disk (cascades to their videos).
    for stale_title in set(existing_sections) - set(desired):
        db.delete(existing_sections[stale_title])
        stats.sections_removed += 1
    db.flush()

    for sec_title, (sec_order, files) in desired.items():
        section = existing_sections.get(sec_title)
        if section is None:
            section = Section(
                course_id=course.id,
                title=sec_title,
                order_index=sec_order,
            )
            db.add(section)
            db.flush()
            stats.sections_added += 1
        else:
            section.order_index = sec_order

        _sync_section_videos(db, section, files, root, stats)
        stats.videos_indexed += len(files)
        _ensure_section_quiz(db, section, stats)


def _sync_section_videos(
    db: Session,
    section: Section,
    files: list[Path],
    root: Path,
    stats: SyncStats,
) -> None:
    desired_paths = {f.relative_to(root).as_posix(): (idx, f) for idx, f in enumerate(files, 1)}
    existing = {v.file_path: v for v in section.videos}

    for stale_path in set(existing) - set(desired_paths):
        db.delete(existing[stale_path])
        stats.videos_removed += 1
    db.flush()

    for rel, (idx, vf) in desired_paths.items():
        title = _humanize(vf.stem)
        order = _order_index(vf.stem, idx)
        video = existing.get(rel)
        if video is None:
            db.add(
                Video(
                    section_id=section.id,
                    title=title,
                    file_path=rel,
                    order_index=order,
                )
            )
            stats.videos_added += 1
        else:
            video.title = title
            video.order_index = order
    db.flush()


# Generic placeholder questions seeded for every new section. The instructor
# replaces these with real content later.
_DUMMY_QUESTIONS: list[dict] = [
    {
        "text": "Which of the following best describes the focus of this section?",
        "options": [
            "Hands-on practical lessons",
            "Theory and concepts",
            "Reference material only",
            "All of the above",
        ],
        "correct_index": 3,
    },
    {
        "text": "What is the most effective way to absorb new material in a video lesson?",
        "options": [
            "Watch every video in one sitting without breaks",
            "Pause, take notes, and rewatch difficult parts",
            "Skip ahead to the conclusion",
            "Only watch the introduction",
        ],
        "correct_index": 1,
    },
    {
        "text": "Why do short quizzes after a section improve long-term retention?",
        "options": [
            "They make the course longer",
            "Active recall reinforces memory",
            "They replace the need to watch videos",
            "They are required by the platform",
        ],
        "correct_index": 1,
    },
    {
        "text": "After finishing a section, the recommended next step is to:",
        "options": [
            "Immediately move to a different course",
            "Take the section quiz to check understanding",
            "Skip the next section entirely",
            "Delete your progress and start over",
        ],
        "correct_index": 1,
    },
]


def _ensure_section_quiz(db: Session, section: Section, stats: SyncStats) -> None:
    """Make sure each section has a placeholder quiz with 4 questions."""
    existing = db.execute(
        select(Quiz).where(Quiz.section_id == section.id)
    ).scalar_one_or_none()
    if existing is not None:
        return

    quiz = Quiz(section_id=section.id, title=f"{section.title} quiz")
    db.add(quiz)
    db.flush()
    for idx, q in enumerate(_DUMMY_QUESTIONS):
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                position=idx,
                text=q["text"],
                option_a=q["options"][0],
                option_b=q["options"][1],
                option_c=q["options"][2],
                option_d=q["options"][3],
                correct_index=q["correct_index"],
            )
        )
    db.flush()
    stats.quizzes_added += 1
