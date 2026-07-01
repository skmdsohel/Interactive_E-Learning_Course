"""Public (learner-facing) interactive activity endpoints.

Returns full payloads so learners can play them. No answer-hiding is required
— matching pairs, flashcard backs, and ordering sequences are the content the
learner is meant to see while attempting the activity.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.activity import ActivityRead
from app.services.activity_service import ActivityService

router = APIRouter(tags=["activities"])


@router.get(
    "/sections/{section_id}/activities",
    response_model=List[ActivityRead],
    summary="List interactive activities for a section",
)
def list_activities(
    section_id: int,
    db: Session = Depends(db_session),
) -> List[ActivityRead]:
    return ActivityService(db).list_for_section(section_id)


@router.get(
    "/activities/{activity_id}",
    response_model=ActivityRead,
    summary="Get a single activity by id",
)
def get_activity(
    activity_id: int,
    db: Session = Depends(db_session),
) -> ActivityRead:
    return ActivityService(db).get(activity_id)
