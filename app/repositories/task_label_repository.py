# [Ngày 6] Repository quản lý mối quan hệ gán/bỏ label cho task (bảng task_labels)

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label
from app.models.task_label import TaskLabel


class TaskLabelRepository:
    """Repository thao tác bảng nối task_labels."""

    async def get_by_task_and_label(
        self, db: AsyncSession, task_id: int, label_id: int
    ) -> Optional[TaskLabel]:
        """Lấy bản ghi gán label cho task nếu tồn tại."""
        stmt = select(TaskLabel).where(
            TaskLabel.task_id == task_id,
            TaskLabel.label_id == label_id,
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def assign_label(
        self, db: AsyncSession, task_id: int, label_id: int
    ) -> TaskLabel:
        """Gán label vào task."""
        existing = await self.get_by_task_and_label(db, task_id=task_id, label_id=label_id)
        if existing:
            return existing

        db_obj = TaskLabel(task_id=task_id, label_id=label_id)
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def remove_label(
        self, db: AsyncSession, task_id: int, label_id: int
    ) -> bool:
        """Bỏ label khỏi task."""
        existing = await self.get_by_task_and_label(db, task_id=task_id, label_id=label_id)
        if not existing:
            return False

        await db.delete(existing)
        await db.commit()
        return True

    async def list_labels_by_task(
        self, db: AsyncSession, task_id: int
    ) -> List[Label]:
        """Danh sách label đã được gán cho task."""
        stmt = (
            select(Label)
            .join(TaskLabel, Label.id == TaskLabel.label_id)
            .where(TaskLabel.task_id == task_id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


task_label_repository = TaskLabelRepository()
