"""Aggregator for v1 routers."""
from fastapi import APIRouter

from app.api.v1 import courses, health, videos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(courses.router)
api_router.include_router(videos.router)
