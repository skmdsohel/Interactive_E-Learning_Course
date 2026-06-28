"""Video endpoints — metadata and range-aware streaming."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.course import VideoRead
from app.services.video_service import VideoService
from app.utils.streaming import stream_file_with_range

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/{video_id}", response_model=VideoRead, summary="Get video metadata")
def get_video(video_id: int, db: Session = Depends(db_session)) -> VideoRead:
    return VideoService(db).get_metadata(video_id)


@router.get(
    "/{video_id}/stream",
    summary="Stream a video (HTTP Range supported)",
    response_class=None,
    responses={
        200: {"content": {"video/*": {}}, "description": "Full content"},
        206: {"content": {"video/*": {}}, "description": "Partial content"},
        404: {"description": "Video not found"},
        416: {"description": "Requested range not satisfiable"},
    },
)
def stream_video(video_id: int, request: Request, db: Session = Depends(db_session)):
    video, path = VideoService(db).resolve_file(video_id)
    return stream_file_with_range(request, path, filename=path.name)
