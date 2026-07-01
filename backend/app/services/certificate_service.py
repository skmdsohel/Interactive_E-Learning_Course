"""Course-completion certificate service.

A learner becomes eligible for a certificate once they have:
  * marked every video in the course as completed,
  * passed (at any point) every quiz attached to a section of the course, AND
  * completed every interactive activity attached to any section.

PDF is generated on demand from reportlab — no files are written to disk,
and no rows are persisted to the database. The certificate's "completion
date" is the latest of the relevant completion timestamps so it reflects
when the learner actually finished, not when they downloaded it.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.activity import ActivityCompletion
from app.models.course import Course
from app.models.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.quiz_repository import QuizRepository


@dataclass(frozen=True)
class CertificateEligibility:
    eligible: bool
    total_videos: int
    completed_videos: int
    total_quizzes: int
    passed_quizzes: int
    total_activities: int
    completed_activities: int
    completion_date: Optional[datetime]
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "total_videos": self.total_videos,
            "completed_videos": self.completed_videos,
            "total_quizzes": self.total_quizzes,
            "passed_quizzes": self.passed_quizzes,
            "total_activities": self.total_activities,
            "completed_activities": self.completed_activities,
            "completion_date": (
                self.completion_date.isoformat() if self.completion_date else None
            ),
            "reason": self.reason,
        }


class CertificateService:
    def __init__(self, db: Session):
        self.db = db
        self.course_repo = CourseRepository(db)
        self.progress_repo = ProgressRepository(db)
        self.quiz_repo = QuizRepository(db)

    # ---- Eligibility ----

    def get_eligibility(self, *, user: User, course_id: int) -> CertificateEligibility:
        course = self.course_repo.get_with_content(course_id)
        if course is None:
            raise NotFoundError(f"Course {course_id} not found")

        videos = [v for section in course.sections for v in section.videos]
        quizzes = [section.quiz for section in course.sections if section.quiz is not None]
        activities = [
            a for section in course.sections for a in (section.activities or [])
        ]

        total_videos = len(videos)
        total_quizzes = len(quizzes)
        total_activities = len(activities)

        if total_videos == 0:
            return CertificateEligibility(
                eligible=False,
                total_videos=0,
                completed_videos=0,
                total_quizzes=total_quizzes,
                passed_quizzes=0,
                total_activities=total_activities,
                completed_activities=0,
                completion_date=None,
                reason="Course has no videos yet.",
            )

        progress_rows = self.progress_repo.list_for_videos(
            user.id, [v.id for v in videos]
        )
        completed_rows = [row for row in progress_rows if row.completed]
        completed_videos = len(completed_rows)

        passed_attempts = []
        for quiz in quizzes:
            attempt = self.quiz_repo.latest_attempt(user_id=user.id, quiz_id=quiz.id)
            if attempt is not None and attempt.passed:
                passed_attempts.append(attempt)
        passed_quizzes = len(passed_attempts)

        activity_completion_rows: list[ActivityCompletion] = []
        if activities:
            activity_ids = [a.id for a in activities]
            activity_completion_rows = list(
                self.db.execute(
                    select(ActivityCompletion).where(
                        ActivityCompletion.user_id == user.id,
                        ActivityCompletion.activity_id.in_(activity_ids),
                    )
                ).scalars().all()
            )
        completed_activities = len(activity_completion_rows)

        videos_done = completed_videos == total_videos
        quizzes_done = passed_quizzes == total_quizzes
        activities_done = completed_activities == total_activities

        if not (videos_done and quizzes_done and activities_done):
            reasons = []
            if not videos_done:
                reasons.append(
                    f"{total_videos - completed_videos} video(s) still to finish"
                )
            if not quizzes_done:
                reasons.append(
                    f"{total_quizzes - passed_quizzes} quiz(zes) still to pass"
                )
            if not activities_done:
                reasons.append(
                    f"{total_activities - completed_activities} activity(ies) still to complete"
                )
            return CertificateEligibility(
                eligible=False,
                total_videos=total_videos,
                completed_videos=completed_videos,
                total_quizzes=total_quizzes,
                passed_quizzes=passed_quizzes,
                total_activities=total_activities,
                completed_activities=completed_activities,
                completion_date=None,
                reason="; ".join(reasons),
            )

        # Eligible — completion date is the latest meaningful timestamp.
        timestamps: list[datetime] = []
        for row in completed_rows:
            if row.completed_at is not None:
                timestamps.append(row.completed_at)
        for attempt in passed_attempts:
            if attempt.taken_at is not None:
                timestamps.append(attempt.taken_at)
        for ac in activity_completion_rows:
            if ac.completed_at is not None:
                timestamps.append(ac.completed_at)
        completion_date = max(timestamps) if timestamps else datetime.utcnow()

        return CertificateEligibility(
            eligible=True,
            total_videos=total_videos,
            completed_videos=completed_videos,
            total_quizzes=total_quizzes,
            passed_quizzes=passed_quizzes,
            total_activities=total_activities,
            completed_activities=completed_activities,
            completion_date=completion_date,
            reason=None,
        )

    # ---- PDF generation ----

    def build_pdf(self, *, user: User, course_id: int) -> tuple[bytes, str, datetime]:
        """Return (pdf_bytes, filename, completion_date). Raises ValidationError
        when the user isn't eligible yet."""
        eligibility = self.get_eligibility(user=user, course_id=course_id)
        if not eligibility.eligible:
            raise ValidationError(
                eligibility.reason or "Course not completed yet."
            )

        course = self.course_repo.get_with_content(course_id)
        # ``get_with_content`` already returned non-None above, but appease type-checkers.
        assert course is not None

        learner_name = (user.name or user.email or "Learner").strip()
        instructor_name = _resolve_instructor_name(course)
        completion_date = eligibility.completion_date or datetime.utcnow()

        pdf_bytes = _render_certificate_pdf(
            learner_name=learner_name,
            course_title=course.title,
            instructor_name=instructor_name,
            completion_date=completion_date,
        )
        filename = _safe_filename(
            f"{course.slug or 'course'}-certificate-{learner_name}.pdf"
        )
        return pdf_bytes, filename, completion_date


# ---- Helpers ----------------------------------------------------------------


def _resolve_instructor_name(course: Course) -> str:
    if course.instructor_user is not None:
        name = (course.instructor_user.name or course.instructor_user.email or "").strip()
        if name:
            return name
    if course.instructor:
        return course.instructor.strip()
    return "Course Instructor"


def _safe_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in ("-", "_", ".") else "-" for c in name)
    return safe.strip("-") or "certificate.pdf"


def _render_certificate_pdf(
    *,
    learner_name: str,
    course_title: str,
    instructor_name: str,
    completion_date: datetime,
) -> bytes:
    buf = io.BytesIO()
    page_size = landscape(letter)
    page_w, page_h = page_size
    c = canvas.Canvas(buf, pagesize=page_size)

    # ---- Outer border ----
    border_color = colors.HexColor("#1f3a5f")  # deep navy
    accent_color = colors.HexColor("#c9a227")  # gold
    text_color = colors.HexColor("#1f2937")    # slate-800
    muted_color = colors.HexColor("#6b7280")   # slate-500

    c.setStrokeColor(border_color)
    c.setLineWidth(6)
    c.rect(0.4 * inch, 0.4 * inch, page_w - 0.8 * inch, page_h - 0.8 * inch)

    c.setStrokeColor(accent_color)
    c.setLineWidth(1.5)
    c.rect(0.6 * inch, 0.6 * inch, page_w - 1.2 * inch, page_h - 1.2 * inch)

    # ---- Top emblem / header ----
    center_x = page_w / 2.0

    c.setFillColor(accent_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(center_x, page_h - 1.3 * inch, "LEARNSPHERE")

    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(center_x, page_h - 2.0 * inch, "Certificate of Completion")

    c.setFillColor(muted_color)
    c.setFont("Helvetica", 13)
    c.drawCentredString(
        center_x, page_h - 2.4 * inch, "This certificate is proudly presented to"
    )

    # ---- Learner name ----
    c.setFillColor(border_color)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(center_x, page_h - 3.1 * inch, learner_name)

    # Underline under the learner name.
    name_width = c.stringWidth(learner_name, "Helvetica-Bold", 30)
    underline_x = center_x - max(name_width, 3 * inch) / 2.0
    underline_x2 = center_x + max(name_width, 3 * inch) / 2.0
    c.setStrokeColor(accent_color)
    c.setLineWidth(1.2)
    c.line(underline_x, page_h - 3.25 * inch, underline_x2, page_h - 3.25 * inch)

    # ---- Course recognition ----
    c.setFillColor(muted_color)
    c.setFont("Helvetica", 13)
    c.drawCentredString(
        center_x,
        page_h - 3.8 * inch,
        "for successfully completing all videos and quizzes in the course",
    )

    c.setFillColor(text_color)
    course_font_size = _fit_font_size(c, course_title, "Helvetica-BoldOblique", 24, page_w - 2.5 * inch)
    c.setFont("Helvetica-BoldOblique", course_font_size)
    c.drawCentredString(center_x, page_h - 4.4 * inch, course_title)

    # ---- Footer: date (left) + instructor (right) ----
    footer_y = 1.4 * inch
    line_y = footer_y + 0.45 * inch

    left_x = 1.6 * inch
    right_x = page_w - 1.6 * inch

    c.setStrokeColor(text_color)
    c.setLineWidth(0.8)
    c.line(left_x - 1.1 * inch, line_y, left_x + 1.1 * inch, line_y)
    c.line(right_x - 1.4 * inch, line_y, right_x + 1.4 * inch, line_y)

    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(left_x, footer_y + 0.18 * inch, completion_date.strftime("%B %d, %Y"))
    c.drawCentredString(right_x, footer_y + 0.18 * inch, instructor_name)

    c.setFillColor(muted_color)
    c.setFont("Helvetica", 10)
    c.drawCentredString(left_x, footer_y - 0.05 * inch, "Date of Completion")
    c.drawCentredString(right_x, footer_y - 0.05 * inch, "Instructor")

    # ---- Tiny footer note ----
    c.setFillColor(muted_color)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(
        center_x,
        0.75 * inch,
        f"Issued by LearnSphere on {datetime.utcnow().strftime('%Y-%m-%d')}.",
    )

    c.showPage()
    c.save()
    return buf.getvalue()


def _fit_font_size(c: canvas.Canvas, text: str, font: str, max_size: int, max_width: float) -> int:
    """Shrink the font size for a long course title until it fits within max_width."""
    size = max_size
    while size > 12 and c.stringWidth(text, font, size) > max_width:
        size -= 1
    return size
