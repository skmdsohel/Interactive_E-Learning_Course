"""User repository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_google_sub(self, google_sub: str) -> Optional[User]:
        stmt = select(User).where(User.google_sub == google_sub)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self, *, offset: int = 0, limit: int = 200) -> list[User]:
        stmt = select(User).order_by(User.id.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
