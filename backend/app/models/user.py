"""User model (Google-authenticated OR local-password accounts)."""
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, IdMixin, TimestampMixin

# Allowed role values stored in `users.role`.
# `pending` is a sentinel applied to brand-new accounts before they choose
# learner or instructor; it is NOT part of ALL_ROLES so the admin role
# endpoint will refuse to set it.
ROLE_PENDING = "pending"
ROLE_LEARNER = "learner"
ROLE_INSTRUCTOR = "instructor"
ROLE_ADMIN = "admin"

ALL_ROLES = {ROLE_LEARNER, ROLE_INSTRUCTOR, ROLE_ADMIN}

# L&D-domain display aliases (used by UI labels; DO NOT change stored role
# values -- they remain learner/instructor/admin internally).
ROLE_DISPLAY_NAMES = {
    ROLE_LEARNER: "Employee",
    ROLE_INSTRUCTOR: "Trainer",
    ROLE_ADMIN: "Admin",
    ROLE_PENDING: "Pending",
}

# Account activation states.
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
ALL_STATUSES = {STATUS_ACTIVE, STATUS_INACTIVE}


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # Google's stable, unique subject identifier (`sub` claim). Nullable to
    # support local-password accounts that never went through Google sign-in.
    google_sub: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ROLE_LEARNER, server_default=ROLE_LEARNER
    )

    # ---- L&D-portal fields (Phase 0) ----
    # bcrypt hash for local-login users; NULL for Google-only accounts.
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Free-text department (e.g. "Engineering", "HR"). Optional.
    department: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    # Free-text job title (e.g. "Senior Engineer"). Optional.
    job_title: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    # Phone number, kept as free-text so we don't over-constrain formats.
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # Account activation status. Inactive users cannot log in.
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=STATUS_ACTIVE,
        server_default=STATUS_ACTIVE,
        index=True,
    )

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_instructor(self) -> bool:
        return self.role == ROLE_INSTRUCTOR

    @property
    def can_manage_courses(self) -> bool:
        return self.role in (ROLE_ADMIN, ROLE_INSTRUCTOR)

    @property
    def is_active(self) -> bool:
        return self.status == STATUS_ACTIVE

    @property
    def has_local_password(self) -> bool:
        return bool(self.password_hash)

    @property
    def role_display(self) -> str:
        return ROLE_DISPLAY_NAMES.get(self.role, self.role.title())
