# [Ngày 1] Dependency injection cho API v1
# [Ngày 2] thay stub Ngày 1: get_db() giờ yield AsyncSession thật từ SQLAlchemy

from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.repositories.label_repository import label_repository
from app.services.label_service import LabelService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection trả về AsyncSession SQLAlchemy thật.
    
    [Ngày 2] thay stub Ngày 1 (yield None) bằng session thật từ AsyncSessionLocal.
    Session tự động commit/rollback và đóng khi request kết thúc.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbDep = Annotated[AsyncSession, Depends(get_db)]


def get_label_service() -> LabelService:
    """Dependency injection trả về instance LabelService."""
    return LabelService(repo=label_repository)
