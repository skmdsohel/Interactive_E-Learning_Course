"""Pydantic schemas package (request/response DTOs)."""
from app.schemas.common import ErrorResponse, HealthResponse, Message

__all__ = ["ErrorResponse", "HealthResponse", "Message"]
