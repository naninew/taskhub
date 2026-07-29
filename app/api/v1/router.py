# [Ngày 1] Router tổng hợp cho API v1

from fastapi import APIRouter
from app.api.v1.endpoints import labels

api_router = APIRouter()
api_router.include_router(labels.router, tags=["labels"])
