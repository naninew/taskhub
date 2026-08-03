# [Ngày 5] TaskRepository kế thừa BaseRepository[Task]

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self) -> None:
        super().__init__(Task)

    async def list_by_project(
        self, db: AsyncSession, *, project_id: int
    ) -> List[Task]:
        """Danh sách task thuộc project (chưa filter/pagination — Ngày 6)."""
        result = await db.execute(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())


task_repository = TaskRepository()
