# [Ngày 1] Khởi tạo FastAPI app instance với lifespan context manager và mount router
# [Ngày 4] Đăng ký exception handler AppException + LoggingMiddleware

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger
from app.middleware.logging_middleware import LoggingMiddleware


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

app.add_middleware(LoggingMiddleware)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    """[Ngày 4] Trả JSON lỗi thống nhất {code, message, detail} cho mọi AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"message": "Welcome to TaskHub API"}
