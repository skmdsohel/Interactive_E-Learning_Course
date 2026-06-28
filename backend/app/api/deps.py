"""FastAPI shared dependencies.

Add reusable `Depends(...)` providers here (e.g. db session wrappers,
pagination, auth).
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

DBSession = Depends(get_db)


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


# `auto_error=False` lets us emit a uniform 401 with our own error payload.
_bearer_required = HTTPBearer(auto_error=False, description="App-issued JWT")
_bearer_optional = HTTPBearer(auto_error=False, description="App-issued JWT (optional)")


def _user_from_credentials(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: Session,
    *,
    required: bool,
) -> Optional[User]:
    if credentials is None or not credentials.credentials:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    try:
        user = UserRepository(db).get(int(user_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_required),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_credentials(credentials, db, required=True)
    assert user is not None  # narrowed by `required=True`
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    return _user_from_credentials(credentials, db, required=False)
