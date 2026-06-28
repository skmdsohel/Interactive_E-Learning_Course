"""User-related Pydantic schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    picture_url: Optional[str] = None
    role: str = "user"
    created_at: datetime
    updated_at: datetime


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google-issued ID token (JWT) from the client SDK.")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Lifetime of the access token in seconds.")
    user: UserRead
