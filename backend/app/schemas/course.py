"""Pydantic schemas for Course / Section / Video."""
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.common import ORMModel


class VideoRead(ORMModel):
    id: int
    section_id: int
    title: str
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    order_index: int
    stream_url: Optional[str] = Field(
        default=None,
        description="Relative URL for streaming this video (server-populated).",
    )
    created_at: datetime
    updated_at: datetime


class SectionRead(ORMModel):
    id: int
    course_id: int
    title: str
    order_index: int
    videos: List[VideoRead] = []


class CourseListItem(ORMModel):
    id: int
    title: str
    slug: str
    instructor: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Relative URL to the course thumbnail (server-populated).",
    )
    section_count: int = 0
    video_count: int = 0
    total_duration_seconds: int = 0


class CourseRead(ORMModel):
    id: int
    title: str
    slug: str
    instructor: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    sections: List[SectionRead] = []
    created_at: datetime
    updated_at: datetime
