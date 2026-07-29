# [Ngày 1] Khởi tạo FastAPI app instance với lifespan context manager và mount router

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("TaskHub API starting up")
    yield
    logger.info("TaskHub API shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"message": "Welcome to TaskHub API"}
