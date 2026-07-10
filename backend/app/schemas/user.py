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
