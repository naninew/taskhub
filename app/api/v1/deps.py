# [Ngày 1] Dependency injection cho API v1 - stub get_db()

from typing import AsyncGenerator
from app.repositories.label_repository import label_repository
from app.services.label_service import LabelService


async def get_db() -> AsyncGenerator[None, None]:
    """Stub dependency get_db().
    
    TODO Ngày 2: Thay bằng AsyncSession thật kết nối SQLAlchemy 2.x mà không đổi chữ ký hàm ở router.
    """
    yield None


def get_label_service() -> LabelService:
    """Dependency injection trả về instance LabelService."""
    return LabelService(repo=label_repository)
