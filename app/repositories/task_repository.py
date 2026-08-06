# [Ngày 5] TaskRepository kế thừa BaseRepository[Task]
# [Ngày 6] nâng cấp từ Ngày 5: thêm list_tasks_filtered hỗ trợ filter (status, priority, assignee) & pagination

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self) -> None:
        super().__init__(Task)

    async def list_by_project(
        self, db: AsyncSession, *, project_id: int
    ) -> List[Task]:
        """Danh sách task thuộc project (giữ lại từ Ngày 5)."""
        result = await db.execute(
            select(Task)
            .options(selectinload(Task.assignee), selectinload(Task.task_labels))
            .where(Task.project_id == project_id)
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    # [Ngày 6, Refactor Ngày 8] NÂNG CẤP: thêm selectinload(assignee, task_labels) giải quyết triệt để N+1 query
    async def list_tasks_filtered(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Task], int]:
        """Danh sách task thuộc project hỗ trợ filter, phân trang & eager loading quan hệ."""
        stmt = (
            select(Task)
            .options(selectinload(Task.assignee), selectinload(Task.task_labels))
            .where(Task.project_id == project_id)
        )

        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id is not None:
            stmt = stmt.where(Task.assignee_id == assignee_id)

        # Tính tổng số bản ghi khớp filter
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        # Phân trang
        skip = (page - 1) * limit
        paginated_stmt = (
            stmt.order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(paginated_stmt)
        items = list(result.scalars().all())

        return items, total



task_repository = TaskRepository()
