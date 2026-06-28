"""Video service — metadata and file resolution for streaming."""
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.course import Video
from app.repositories.video_repository import VideoRepository
from app.schemas.course import VideoRead
from app.utils.storage import resolve_video_path


class VideoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VideoRepository(db)

    def get_metadata(self, video_id: int) -> VideoRead:
        video = self.repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")
        return VideoRead.model_validate(
            {
                "id": video.id,
                "section_id": video.section_id,
                "title": video.title,
                "description": video.description,
                "duration_seconds": video.duration_seconds,
                "order_index": video.order_index,
                "stream_url": f"/api/v1/videos/{video.id}/stream",
                "created_at": video.created_at,
                "updated_at": video.updated_at,
            }
        )

    def resolve_file(self, video_id: int) -> tuple[Video, Path]:
        video = self.repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")
        try:
            path = resolve_video_path(video.file_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        if not path.exists() or not path.is_file():
            raise NotFoundError(f"Video file for {video_id} not found on disk")
        return video, path
