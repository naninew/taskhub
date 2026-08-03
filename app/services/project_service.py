# [Ngày 5] ProjectService — create, update, archive (soft archive via status)

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import ProjectStatus
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self.project_repo = project_repo

    async def create_project(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        data: ProjectCreate,
    ) -> Project:
        """Tạo project mới trong workspace — mặc định status=ACTIVE."""
        return await self.project_repo.create(
            db,
            obj_in={
                "workspace_id": workspace_id,
                "name": data.name,
                "description": data.description,
                "status": ProjectStatus.ACTIVE,
            },
        )

    async def list_projects(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        include_archived: bool = False,
    ) -> List[Project]:
        """Danh sách project — mặc định chỉ ACTIVE."""
        return await self.project_repo.list_by_workspace(
            db,
            workspace_id=workspace_id,
            include_archived=include_archived,
        )

    async def get_project(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        project_id: int,
    ) -> Project:
        """Lấy chi tiết project theo workspace."""
        project = await self.project_repo.get_by_workspace_and_id(
            db, workspace_id=workspace_id, project_id=project_id
        )
        if project is None:
            raise NotFoundException(
                message="Project not found",
                detail=f"Project id={project_id} not found in workspace id={workspace_id}.",
            )
        return project

    async def update_project(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        project_id: int,
        data: ProjectUpdate,
    ) -> Project:
        """Cập nhật name/description của project."""
        project = await self.get_project(
            db, workspace_id=workspace_id, project_id=project_id
        )
        if project.status == ProjectStatus.ARCHIVED:
            raise ConflictException(
                message="Cannot update archived project",
                detail="Unarchive the project before making changes.",
            )
        return await self.project_repo.update(db, db_obj=project, obj_in=data)

    async def archive_project(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        project_id: int,
    ) -> Project:
        """Archive project — đổi status, không xoá bản ghi."""
        project = await self.get_project(
            db, workspace_id=workspace_id, project_id=project_id
        )
        if project.status == ProjectStatus.ARCHIVED:
            raise ConflictException(
                message="Project already archived",
                detail=f"Project id={project_id} is already ARCHIVED.",
            )
        return await self.project_repo.update(
            db,
            db_obj=project,
            obj_in={"status": ProjectStatus.ARCHIVED},
        )
