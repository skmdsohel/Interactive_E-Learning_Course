"""JWT issuance and verification for the app's own session tokens.

Google issues an ID token to the client; we verify it once during sign-in
and then mint our own short-lived JWT that the SPA uses for subsequent
requests. This module owns that JWT.

It also owns bcrypt password hashing helpers used by the local-login
flow (Phase 1). Google-only accounts keep `password_hash` NULL.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings


class TokenError(Exception):
    """Raised when an access token cannot be decoded or has expired."""


# ---- Password hashing (bcrypt) ----

# Single shared context; bcrypt has a 72-byte input limit which passlib
# handles internally when using the `bcrypt` scheme.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash for the given plain-text password."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """Constant-time password check. Returns False if hash is missing."""
    if not password_hash:
        return False
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except ValueError:
        # Malformed hash on disk — treat as auth failure rather than raise.
        return False


# ---- JWT ----


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


# ---- Password-reset tokens ----
# Short-lived, single-purpose JWTs used by the forgot-password flow. They
# carry the user id as `sub` plus a `purpose="pwreset"` claim so a normal
# access token cannot be replayed against the reset endpoint (and vice
# versa). Default lifetime is 30 minutes.

_RESET_TOKEN_PURPOSE = "pwreset"
_RESET_TOKEN_MINUTES = 30


def create_password_reset_token(*, user_id: int) -> tuple[str, int]:
    """Return `(reset_jwt, expires_in_seconds)`."""
    expires_delta = timedelta(minutes=_RESET_TOKEN_MINUTES)
    now = datetime.now(tz=timezone.utc)
    exp = now + expires_delta
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "purpose": _RESET_TOKEN_PURPOSE,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_password_reset_token(token: str) -> int:
    """Return the user id encoded in a reset token, or raise TokenError."""
    payload = decode_access_token(token)
    if payload.get("purpose") != _RESET_TOKEN_PURPOSE:
        raise TokenError("Token is not a password-reset token")
    sub = payload.get("sub")
    try:
        return int(sub)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TokenError("Invalid token subject") from exc
