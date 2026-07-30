# [Ngày 2] BaseRepository generic cho Async CRUD thao tác với SQLAlchemy 2.x

from typing import Any, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]) -> None:
        """BaseRepository nhận vào SQLAlchemy model class."""
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Truy vấn entity theo ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def list(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Lấy danh sách entity có phân trang (skip, limit)."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, *, obj_in: Union[dict[str, Any], BaseModel]
    ) -> ModelType:
        """Tạo mới 1 entity trong database."""
        if isinstance(obj_in, BaseModel):
            obj_in_data = obj_in.model_dump(exclude_unset=True)
        elif isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = dict(obj_in)

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[dict[str, Any], BaseModel]
    ) -> ModelType:
        """Cập nhật thông tin entity."""
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Any) -> bool:
        """Xoá 1 entity theo ID."""
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

    async def count(self, db: AsyncSession) -> int:
        """Đếm tổng số bản ghi trong bảng."""
        result = await db.execute(select(func.count()).select_from(self.model))
        return result.scalar_one() or 0
