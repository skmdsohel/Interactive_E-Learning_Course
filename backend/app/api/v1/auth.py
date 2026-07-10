"""Auth endpoints — Google sign-in, local email/password auth, current-user introspection."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.core.config import settings
from app.models.user import ROLE_ADMIN, ROLE_INSTRUCTOR, ROLE_LEARNER, User
from app.schemas.user import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
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


# ---- Local (email/password) auth (Phase 1) ----


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account with email/password",
)
def register_local(payload: RegisterRequest, db: Session = Depends(db_session)) -> TokenResponse:
    return AuthService(db).register_local(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
        department=payload.department,
        job_title=payload.job_title,
        phone=payload.phone,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email/password",
)
def login_local(payload: LoginRequest, db: Session = Depends(db_session)) -> TokenResponse:
    return AuthService(db).login_local(email=payload.email, password=payload.password)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (stateless — client discards the token)",
)
def logout() -> Response:
    # JWTs are stateless: the client drops the token. This endpoint exists
    # so the frontend has a single logout entry point and so we can bolt on
    # server-side blacklisting later without changing the client contract.
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change the current user's password",
)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    AuthService(db).change_password(
        current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request a password-reset token (delivery over email once wired)",
)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(db_session)
) -> ForgotPasswordResponse:
    token, _user = AuthService(db).request_password_reset(email=payload.email)
    # In production the token should ONLY be emailed. Until email delivery
    # is wired we surface it in non-production environments so the flow can
    # be exercised end-to-end. Production responses stay generic.
    if token is not None and settings.APP_ENV.lower() not in {"prod", "production"}:
        return ForgotPasswordResponse(reset_token=token)
    return ForgotPasswordResponse()


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset the password using a token from /auth/forgot-password",
)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(db_session)
) -> Response:
    AuthService(db).reset_password(
        reset_token=payload.reset_token, new_password=payload.new_password
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- Session introspection ----


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
