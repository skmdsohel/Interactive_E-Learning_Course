"""JWT issuance and verification for the app's own session tokens.

Google issues an ID token to the client; we verify it once during sign-in
and then mint our own short-lived JWT that the SPA uses for subsequent
requests. This module owns that JWT.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings


class TokenError(Exception):
    """Raised when an access token cannot be decoded or has expired."""


def create_access_token(*, subject: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, int]:
    """Return `(jwt_string, expires_in_seconds)`."""
    expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    now = datetime.now(tz=timezone.utc)
    exp = now + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc
