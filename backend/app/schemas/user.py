"""User-related Pydantic schemas."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    picture_url: Optional[str] = None
    role: str = "learner"
    # L&D-portal fields (Phase 0).
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    has_local_password: bool = False
    created_at: datetime
    updated_at: datetime


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google-issued ID token (JWT) from the client SDK.")
    role: Optional[Literal["learner", "instructor"]] = Field(
        default=None,
        description=(
            "Role chosen during sign-up. Only applied for brand-new accounts. "
            "Existing accounts keep their stored role. Admins (set via the "
            "ADMIN_EMAILS env var) always override this."
        ),
    )


class RoleChoiceRequest(BaseModel):
    role: Literal["learner", "instructor"] = Field(
        ..., description="Role to switch to. Only allowed while the account is unassigned."
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Lifetime of the access token in seconds.")
    user: UserRead


# ---- Local (email/password) auth schemas (Phase 1) ----


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=120)
    job_title: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=32)
    role: Literal["learner", "instructor"] = Field(
        default="learner",
        description=(
            "Self-service role during public registration. Only learner or "
            "instructor is allowed; admins can only be created by another admin."
        ),
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Always returns success to avoid leaking which emails exist.

    In development (or until email delivery is wired) the reset token is
    returned inline so the flow can be exercised end-to-end.
    """

    message: str = "If the email exists, a reset link has been sent."
    reset_token: Optional[str] = Field(
        default=None,
        description="Only populated in non-production environments.",
    )


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
