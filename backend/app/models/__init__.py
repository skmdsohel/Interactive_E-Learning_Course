"""ORM models package.

Import every model module here so Alembic's autogenerate discovers
all tables via `Base.metadata`.
"""
from app.models.course import Course, Section, Video

__all__ = ["Course", "Section", "Video"]
