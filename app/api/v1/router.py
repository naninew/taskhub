# [Ngày 1] Router tổng hợp cho API v1
# [Ngày 3] Mount auth và users router
# [Ngày 4] Mount workspaces router

from fastapi import APIRouter

from app.api.v1.endpoints import auth, labels, users, workspaces

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(labels.router, tags=["labels"])
