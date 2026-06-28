"""User model (Google-authenticated accounts)."""
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, IdMixin, TimestampMixin

# Allowed role values stored in `users.role`.
ROLE_USER = "user"
ROLE_ADMIN = "admin"


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # Google's stable, unique subject identifier (`sub` claim).
    google_sub: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=ROLE_USER, server_default=ROLE_USER)

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN
