"""VideoProgress repository."""
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course, Section, Video
from app.models.progress import VideoProgress
from app.repositories.base import BaseRepository


class ProgressRepository(BaseRepository[VideoProgress]):
    model = VideoProgress

    def __init__(self, db: Session):
        super().__init__(db, VideoProgress)

    def get_for(self, user_id: int, video_id: int) -> Optional[VideoProgress]:
        stmt = select(VideoProgress).where(
            VideoProgress.user_id == user_id,
            VideoProgress.video_id == video_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_videos(
        self, user_id: int, video_ids: Iterable[int]
    ) -> list[VideoProgress]:
        ids = list(video_ids)
        if not ids:
            return []
        stmt = select(VideoProgress).where(
            VideoProgress.user_id == user_id,
            VideoProgress.video_id.in_(ids),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_user_courses_with_progress(
        self, user_id: int
    ) -> list[tuple[Course, int, int, int, Optional[int]]]:
        """Return (course, total_videos, completed_videos, last_position_seconds, last_video_id)
        for every course the user has any progress on.

        Implemented in two simple steps to keep it portable across MySQL/SQLite.
        """
        # Latest watched row per course for this user.
        latest_per_course_stmt = (
            select(
                Section.course_id.label("course_id"),
                VideoProgress.video_id,
                VideoProgress.position_seconds,
                VideoProgress.last_watched_at,
            )
            .join(Video, Video.id == VideoProgress.video_id)
            .join(Section, Section.id == Video.section_id)
            .where(VideoProgress.user_id == user_id)
            .order_by(VideoProgress.last_watched_at.desc())
        )
        rows = self.db.execute(latest_per_course_stmt).all()

        latest_by_course: dict[int, tuple[int, int]] = {}
        for r in rows:
            if r.course_id not in latest_by_course:
                latest_by_course[r.course_id] = (r.video_id, r.position_seconds)

        if not latest_by_course:
            return []

        course_ids = list(latest_by_course)

        # Per-course completion + total counts.
        from sqlalchemy import case, func

        counts_stmt = (
            select(
                Section.course_id,
                func.count(Video.id).label("total"),
                func.coalesce(
                    func.sum(
                        case((VideoProgress.completed.is_(True), 1), else_=0)
                    ),
                    0,
                ).label("completed"),
            )
            .join(Section, Section.id == Video.section_id)
            .outerjoin(
                VideoProgress,
                (VideoProgress.video_id == Video.id)
                & (VideoProgress.user_id == user_id),
            )
            .where(Section.course_id.in_(course_ids))
            .group_by(Section.course_id)
        )
        counts = {r.course_id: (int(r.total), int(r.completed)) for r in self.db.execute(counts_stmt).all()}

        courses = self.db.execute(select(Course).where(Course.id.in_(course_ids))).scalars().all()
        course_by_id = {c.id: c for c in courses}

        out: list[tuple[Course, int, int, int, Optional[int]]] = []
        for cid, (vid, pos) in latest_by_course.items():
            total, completed = counts.get(cid, (0, 0))
            course = course_by_id.get(cid)
            if course is None:
                continue
            out.append((course, total, completed, pos, vid))
        return out

    def upsert(
        self,
        *,
        user_id: int,
        video_id: int,
        position_seconds: int,
        completed: bool,
        completed_at,
    ) -> VideoProgress:
        existing = self.get_for(user_id, video_id)
        if existing is None:
            row = VideoProgress(
                user_id=user_id,
                video_id=video_id,
                position_seconds=position_seconds,
                completed=completed,
                completed_at=completed_at,
            )
            self.db.add(row)
            self.db.flush()
            return row

        # Position should only move forward (avoid scrub-back from clobbering).
        if position_seconds > existing.position_seconds:
            existing.position_seconds = position_seconds
        if completed and not existing.completed:
            existing.completed = True
            existing.completed_at = completed_at
        self.db.flush()
        return existing
