"""Auth service — verifies Google ID tokens, upserts users, issues JWTs."""
from __future__ import annotations

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.models.user import (
    ROLE_ADMIN,
    ROLE_INSTRUCTOR,
    ROLE_LEARNER,
    ROLE_PENDING,
    User,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserRead

logger = get_logger(__name__)

_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class AuthConfigError(AppException):
    status_code = 500
    error_code = "auth_not_configured"


class GoogleTokenInvalid(AppException):
    status_code = 401
    error_code = "invalid_google_token"


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def authenticate_with_google(
        self,
        id_token_str: str,
        *,
        requested_role: str | None = None,
    ) -> TokenResponse:
        if not settings.GOOGLE_CLIENT_ID:
            raise AuthConfigError("GOOGLE_CLIENT_ID is not configured on the server")

        try:
            claims = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            logger.warning("Google ID token verification failed: %s", exc)
            raise GoogleTokenInvalid("Google ID token verification failed") from exc

        if claims.get("iss") not in _GOOGLE_ISSUERS:
            raise GoogleTokenInvalid("Unexpected token issuer")
        if not claims.get("email_verified", False):
            raise GoogleTokenInvalid("Google account email is not verified")

        google_sub = claims["sub"]
        email = claims["email"]
        name = claims.get("name")
        picture = claims.get("picture")

        user = self.users.get_by_google_sub(google_sub)
        is_new_user = False
        if user is None:
            # Allow linking by email if a prior row exists (e.g. seeded data).
            user = self.users.get_by_email(email)
            if user is None:
                user = User(
                    google_sub=google_sub,
                    email=email,
                    name=name,
                    picture_url=picture,
                    role=ROLE_PENDING,
                )
                self.db.add(user)
                self.db.flush()
                is_new_user = True
            else:
                user.google_sub = google_sub
                user.name = name or user.name
                user.picture_url = picture or user.picture_url
        else:
            user.email = email
            user.name = name or user.name
            user.picture_url = picture or user.picture_url

        # Role assignment:
        #   1. ADMIN_EMAILS always wins — promote to admin every login.
        #   2. For a brand-new account, keep it pending so the frontend can
        #      prompt the user to pick learner/instructor. If the client
        #      already supplied a valid role, honor it immediately.
        #   3. For an existing account, keep whatever role is in the DB.
        if email.lower() in settings.admin_emails_set:
            if user.role != ROLE_ADMIN:
                user.role = ROLE_ADMIN
        elif is_new_user and requested_role in {ROLE_LEARNER, ROLE_INSTRUCTOR}:
            user.role = requested_role

        self.db.commit()
        self.db.refresh(user)

        token, expires_in = create_access_token(subject=str(user.id))
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserRead.model_validate(user),
        )
