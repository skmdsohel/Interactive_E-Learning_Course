"""Admin-only endpoints. All routes require role=admin."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_admin
from app.models.course import Course, Section, Video
from app.models.progress import VideoProgress
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead
from app.services.content_sync_service import SyncStats, sync_content

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


class AdminStats(BaseModel):
    users: int
    courses: int
    sections: int
    videos: int
    progress_rows: int


class SyncResponse(BaseModel):
    courses_added: int
    courses_updated: int
    courses_removed: int
    sections_added: int
    sections_removed: int
    videos_added: int
    videos_removed: int
    videos_indexed: int


@router.get("/users", response_model=list[UserRead], summary="List all users")
def list_users(db: Session = Depends(db_session)) -> list[UserRead]:
    rows = UserRepository(db).list_all()
    return [UserRead.model_validate(r) for r in rows]


@router.get("/stats", response_model=AdminStats, summary="High-level catalog and user stats")
def get_stats(db: Session = Depends(db_session)) -> AdminStats:
    def _count(model) -> int:
        return int(db.execute(select(func.count()).select_from(model)).scalar_one())

    return AdminStats(
        users=_count(User),
        courses=_count(Course),
        sections=_count(Section),
        videos=_count(Video),
        progress_rows=_count(VideoProgress),
    )


@router.post(
    "/content/sync",
    response_model=SyncResponse,
    summary="Force a filesystem→DB content sync",
)
def trigger_sync(
    prune: bool = False,
    db: Session = Depends(db_session),
) -> SyncResponse:
    stats: SyncStats = sync_content(db, prune_missing_courses=prune)
    return SyncResponse(**stats.__dict__)
