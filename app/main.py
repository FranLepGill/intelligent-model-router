from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import get_settings
from app.db import SessionLocal
from app.seed import seed_demo_data

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.seed_demo_data:
        async with SessionLocal() as session:
            try:
                await seed_demo_data(session)
            except Exception:
                logger.exception("seed.failed")
    yield


app = FastAPI(
    title="Intelligent AI Model Routing Platform",
    description=(
        "AI inference gateway that automatically selects the most cost-effective "
        "language model based on quality, latency, privacy and budget constraints."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
