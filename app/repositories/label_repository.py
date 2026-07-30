# [Ngày 2] Repository SQLAlchemy kết nối DB thật cho resource Label

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label
from app.repositories.base import BaseRepository
from app.schemas.label import LabelCreate, LabelUpdate


# [Ngày 2] thay repository in-memory Ngày 1 bằng SQLAlchemy
class LabelRepository(BaseRepository[Label]):
    def __init__(self) -> None:
        super().__init__(Label)

    async def create_label(
        self, db: AsyncSession, project_id: int, label_in: LabelCreate
    ) -> Label:
        """Tạo Label mới thuộc project."""
        db_obj = Label(
            project_id=project_id,
            name=label_in.name,
            color=label_in.color,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_name_and_project(
        self, db: AsyncSession, name: str, project_id: int
    ) -> Optional[Label]:
        """Tìm Label theo tên (không phân biệt hoa thường) trong cùng 1 project."""
        stmt = select(Label).where(
            Label.project_id == project_id,
            func.lower(Label.name) == name.lower(),
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_by_project(
        self, db: AsyncSession, project_id: int
    ) -> List[Label]:
        """Lấy danh sách Label thuộc 1 project."""
        stmt = select(Label).where(Label.project_id == project_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update_label(
        self, db: AsyncSession, label_id: int, label_in: LabelUpdate
    ) -> Optional[Label]:
        """Cập nhật thông tin Label."""
        db_obj = await self.get_by_id(db, label_id)
        if not db_obj:
            return None
        return await self.update(db, db_obj=db_obj, obj_in=label_in)

    async def delete_label(self, db: AsyncSession, label_id: int) -> bool:
        """Xoá Label theo ID."""
        return await self.delete(db, id=label_id)


# Instance label_repository dùng chung
label_repository = LabelRepository()
