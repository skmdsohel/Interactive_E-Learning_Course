"""Aggregator for v1 routers."""
from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)

# Future routers register here, e.g.:
# from app.api.v1 import courses
# api_router.include_router(courses.router)
