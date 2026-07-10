"""SQLAlchemy declarative base and shared model mixins."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class TimestampMixin:
    """Adds `created_at` and `updated_at` columns managed by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IdMixin:
    """Adds a standard auto-increment BIGINT primary key."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class AuditMixin:
    """Adds `created_by` and `updated_by` FK columns referencing users.id.

    Both columns are nullable so system-generated or migration-seeded rows
    can omit an author. Application services are responsible for populating
    these values on write.
    """

    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
