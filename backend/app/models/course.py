"""Course, Section, Video ORM models."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class Course(IdMixin, TimestampMixin, Base):
    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    sections: Mapped[List["Section"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Section.order_index",
        lazy="selectin",
    )


class Section(IdMixin, TimestampMixin, Base):
    __tablename__ = "sections"
    __table_args__ = (
        Index("ix_sections_course_order", "course_id", "order_index"),
    )

    course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    course: Mapped["Course"] = relationship(back_populates="sections")
    videos: Mapped[List["Video"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Video.order_index",
        lazy="selectin",
    )


class Video(IdMixin, TimestampMixin, Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_section_order", "section_id", "order_index"),
    )

    section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    section: Mapped["Section"] = relationship(back_populates="videos")
