"""FastAPI shared dependencies.

Add reusable `Depends(...)` providers here (e.g. db session wrappers,
pagination, future auth dependencies).
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db

DBSession = Depends(get_db)


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
