# [Ngày 5] ProjectRepository kế thừa BaseRepository[Project]

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ProjectStatus
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self) -> None:
        super().__init__(Project)

    async def list_by_workspace(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        include_archived: bool = False,
    ) -> List[Project]:
        """Danh sách project trong workspace — mặc định chỉ ACTIVE."""
        stmt = select(Project).where(Project.workspace_id == workspace_id)
        if not include_archived:
            stmt = stmt.where(Project.status == ProjectStatus.ACTIVE)
        stmt = stmt.order_by(Project.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_workspace_and_id(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        project_id: int,
    ) -> Optional[Project]:
        """Lấy project theo workspace_id + project_id."""
        result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        return result.scalars().first()


project_repository = ProjectRepository()
