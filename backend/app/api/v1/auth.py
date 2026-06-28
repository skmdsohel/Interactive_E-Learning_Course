"""Auth endpoints — Google sign-in + current-user introspection."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.schemas.user import GoogleAuthRequest, TokenResponse, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse, summary="Exchange a Google ID token for an app JWT")
def google_signin(payload: GoogleAuthRequest, db: Session = Depends(db_session)) -> TokenResponse:
    return AuthService(db).authenticate_with_google(payload.id_token)


@router.get("/me", response_model=UserRead, summary="Get the current authenticated user")
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
