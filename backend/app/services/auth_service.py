"""Auth service — verifies Google ID tokens, upserts users, issues JWTs.

Also owns the local (email/password) auth flow added in Phase 1:
register, login, change-password, forgot-password, reset-password.
"""
from __future__ import annotations

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException, ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.security import (
    TokenError,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.models.user import (
    ROLE_ADMIN,
    ROLE_INSTRUCTOR,
    ROLE_LEARNER,
    ROLE_PENDING,
    STATUS_ACTIVE,
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


class InvalidCredentials(AppException):
    status_code = 401
    error_code = "invalid_credentials"


class InactiveAccount(AppException):
    status_code = 403
    error_code = "account_inactive"


class InvalidResetToken(AppException):
    status_code = 400
    error_code = "invalid_reset_token"


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

    # ---- Local (email/password) auth ----

    def _issue_token_for(self, user: User) -> TokenResponse:
        token, expires_in = create_access_token(subject=str(user.id))
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserRead.model_validate(user),
        )

    def register_local(
        self,
        *,
        email: str,
        password: str,
        name: str | None,
        role: str,
        department: str | None = None,
        job_title: str | None = None,
        phone: str | None = None,
    ) -> TokenResponse:
        """Create a local-password account and immediately issue a session JWT.

        Public self-service registration only allows learner/instructor.
        Admin promotion is handled by the ADMIN_EMAILS override below (which
        keeps existing behavior for Google sign-in), or by an admin via the
        user-management endpoints (Phase 2).
        """
        if role not in {ROLE_LEARNER, ROLE_INSTRUCTOR}:
            raise ValidationError("role must be 'learner' or 'instructor'")

        existing = self.users.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        effective_role = ROLE_ADMIN if email.lower() in settings.admin_emails_set else role

        user = User(
            email=email,
            name=name,
            role=effective_role,
            password_hash=hash_password(password),
            department=department,
            job_title=job_title,
            phone=phone,
            status=STATUS_ACTIVE,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("Local account registered: user_id=%s email=%s role=%s", user.id, user.email, user.role)
        return self._issue_token_for(user)

    def login_local(self, *, email: str, password: str) -> TokenResponse:
        """Verify credentials and return a session JWT."""
        user = self.users.get_by_email(email)
        # Always run bcrypt to keep the response time constant regardless of
        # whether the account exists — mitigates user-enumeration attacks.
        stored_hash = user.password_hash if user else None
        if not verify_password(password, stored_hash):
            raise InvalidCredentials("Invalid email or password")

        assert user is not None  # narrowed by verify_password above

        # ADMIN_EMAILS override — matches Google flow semantics.
        if user.email.lower() in settings.admin_emails_set and user.role != ROLE_ADMIN:
            user.role = ROLE_ADMIN
            self.db.commit()
            self.db.refresh(user)

        if not user.is_active:
            raise InactiveAccount("Account is inactive. Contact an administrator.")

        return self._issue_token_for(user)

    def change_password(
        self, user: User, *, current_password: str, new_password: str
    ) -> None:
        """Change the password of a local-auth account."""
        if not user.has_local_password:
            raise ValidationError(
                "This account has no local password (signed in via Google). "
                "Use the account provider to manage credentials."
            )
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentials("Current password is incorrect")
        if current_password == new_password:
            raise ValidationError("New password must differ from the current one")

        user.password_hash = hash_password(new_password)
        self.db.commit()
        logger.info("Password changed: user_id=%s", user.id)

    def request_password_reset(self, *, email: str) -> tuple[str | None, User | None]:
        """Look up the account and mint a reset token.

        Returns `(reset_token, user)` when a reset was issued, or
        `(None, None)` when no local-auth account with that email exists.
        The router always responds with a generic success message so callers
        cannot enumerate registered emails.
        """
        user = self.users.get_by_email(email)
        if user is None or not user.has_local_password or not user.is_active:
            return None, None
        token, _ = create_password_reset_token(user_id=user.id)
        logger.info("Password-reset token issued: user_id=%s", user.id)
        return token, user

    def reset_password(self, *, reset_token: str, new_password: str) -> None:
        """Consume a reset token and set a new password."""
        try:
            user_id = decode_password_reset_token(reset_token)
        except TokenError as exc:
            raise InvalidResetToken(str(exc)) from exc

        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if not user.has_local_password:
            # Prevent turning a Google-only account into a password account
            # via a stolen reset token that was somehow issued.
            raise InvalidResetToken("Account is not eligible for password reset")
        if not user.is_active:
            raise InactiveAccount("Account is inactive. Contact an administrator.")

        user.password_hash = hash_password(new_password)
        self.db.commit()
        logger.info("Password reset completed: user_id=%s", user.id)
