"""Repositories package.

Each repository encapsulates persistence logic for a single aggregate.
Services depend on repositories — routers must NOT use SQLAlchemy directly.
"""
from app.repositories.base import BaseRepository

__all__ = ["BaseRepository"]
