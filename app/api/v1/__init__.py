from fastapi import APIRouter

from app.api.v1 import evaluations, health, inference, models

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(inference.router, tags=["inference"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(evaluations.router, tags=["evaluations"])
