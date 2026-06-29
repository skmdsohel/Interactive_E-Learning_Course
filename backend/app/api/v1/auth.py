"""Auth endpoints — Google sign-in + current-user introspection."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import ROLE_ADMIN, ROLE_INSTRUCTOR, ROLE_LEARNER, User
from app.schemas.user import (
    GoogleAuthRequest,
    RoleChoiceRequest,
    TokenResponse,
    UserRead,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse, summary="Exchange a Google ID token for an app JWT")
def google_signin(payload: GoogleAuthRequest, db: Session = Depends(db_session)) -> TokenResponse:
    return AuthService(db).authenticate_with_google(
        payload.id_token, requested_role=payload.role
    )


@router.get("/me", response_model=UserRead, summary="Get the current authenticated user")
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/me/role",
    response_model=UserRead,
    summary="Choose your role (only available while the account has no instructor/learner role yet)",
)
def choose_role(
    payload: RoleChoiceRequest,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if current_user.role == ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin accounts cannot change their own role.",
        )
    if current_user.role in {ROLE_LEARNER, ROLE_INSTRUCTOR}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role has already been assigned. Ask an admin to change it.",
        )
    current_user.role = payload.role
    db.commit()
    db.refresh(current_user)
    return UserRead.model_validate(current_user)
