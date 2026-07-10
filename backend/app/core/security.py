"""JWT issuance and verification for the app's own session tokens.

Google issues an ID token to the client; we verify it once during sign-in
and then mint our own short-lived JWT that the SPA uses for subsequent
requests. This module owns that JWT.

It also owns bcrypt password hashing helpers used by the local-login
flow (Phase 1). Google-only accounts keep `password_hash` NULL.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


class TokenError(Exception):
    """Raised when an access token cannot be decoded or has expired."""


# ---- Password hashing (bcrypt, called directly — no passlib) ----
#
# bcrypt has a hard 72-byte input limit and silently truncates longer
# inputs, which is a footgun. Django's approach is used here: pre-hash
# the password with SHA-256 (base64-encoded => 44 bytes) so any input
# length is safely reduced under the 72-byte ceiling before bcrypt sees
# it. This is the same construction Django ships in
# `BCryptSHA256PasswordHasher` and does not weaken bcrypt's security.
#
# NOTE: passwords hashed here can only be verified by this module — do
# not port these hashes to a system that expects raw bcrypt.

_BCRYPT_ROUNDS = 12  # ~200ms on modern hardware, standard OWASP baseline


def _prehash(password: str) -> bytes:
    """SHA-256 the password so we never exceed bcrypt's 72-byte cap."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    # Hex-encode so the value is printable and stays well under 72 bytes.
    return digest.hex().encode("ascii")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash for the given plain-text password."""
    salted = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(_prehash(plain_password), salted)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """Constant-time password check. Returns False if hash is missing/malformed."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(_prehash(plain_password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
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
