"""Quiz endpoints (learner-facing).

Instructor-side quiz editing lives in `app.api.v1.instructor`.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.schemas.quiz import QuizAttemptRead, QuizAttemptSubmit, QuizRead
from app.services.quiz_service import QuizService

router = APIRouter(tags=["quizzes"])


@router.get(
    "/sections/{section_id}/quiz",
    response_model=QuizRead,
    summary="Get the quiz for a section (no answers)",
)
def get_quiz_for_section(
    section_id: int,
    db: Session = Depends(db_session),
) -> QuizRead:
    return QuizService(db).get_quiz_for_section(section_id)


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizRead,
    summary="Get a quiz by id (no answers)",
)
def get_quiz(quiz_id: int, db: Session = Depends(db_session)) -> QuizRead:
    return QuizService(db).get_quiz(quiz_id)


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an attempt for a quiz",
)
def submit_attempt(
    quiz_id: int,
    payload: QuizAttemptSubmit,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptRead:
    return QuizService(db).submit_attempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        answers=payload.answers,
    )


@router.get(
    "/quizzes/{quiz_id}/my-attempt",
    response_model=QuizAttemptRead,
    summary="Latest attempt by the current user on this quiz",
)
def get_my_attempt(
    quiz_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptRead:
    result: Optional[QuizAttemptRead] = QuizService(db).get_my_latest_attempt(
        user_id=current_user.id, quiz_id=quiz_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No attempt found"
        )
    return result
