"""Aggregator for v1 routers."""
from fastapi import APIRouter

from app.api.v1 import auth, courses, health, progress, videos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(videos.router)
api_router.include_router(progress.router)
