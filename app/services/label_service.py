# [Ngày 2] Service xử lý business logic cho resource Label với AsyncSession DB thật
# [Ngày 6] nâng cấp từ Ngày 5: bổ sung gán/bỏ label cho task qua task_label_repository

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.db.redis import invalidate_project_tasks_cache
from app.models.enums import WorkspaceMemberRole

from app.models.label import Label
from app.models.user import User
from app.repositories.label_repository import LabelRepository, label_repository
from app.repositories.project_repository import ProjectRepository, project_repository
from app.repositories.task_label_repository import TaskLabelRepository, task_label_repository
from app.repositories.task_repository import TaskRepository, task_repository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository, workspace_member_repository
from app.schemas.label import LabelCreate, LabelUpdate


class LabelService:
    def __init__(
        self,
        repo: LabelRepository = label_repository,
        task_label_repo: TaskLabelRepository = task_label_repository,
        task_repo: TaskRepository = task_repository,
        project_repo: ProjectRepository = project_repository,
        member_repo: WorkspaceMemberRepository = workspace_member_repository,
    ) -> None:
        self.repo = repo
        self.task_label_repo = task_label_repo
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.member_repo = member_repo

    async def create_label(
        self, db: AsyncSession, project_id: int, label_in: LabelCreate
    ) -> Label:
        existing = await self.repo.get_by_name_and_project(
            db=db, name=label_in.name, project_id=project_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label with name '{label_in.name}' already exists in project {project_id}.",
            )
        return await self.repo.create_label(db=db, project_id=project_id, label_in=label_in)

    async def get_label(
        self, db: AsyncSession, project_id: int, label_id: int
    ) -> Label:
        label = await self.repo.get_by_id(db=db, id=label_id)
        if not label or label.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in project {project_id}.",
            )
        return label

    async def list_labels(self, db: AsyncSession, project_id: int) -> List[Label]:
        return await self.repo.list_by_project(db=db, project_id=project_id)

    async def update_label(
        self, db: AsyncSession, project_id: int, label_id: int, label_in: LabelUpdate
    ) -> Label:
        existing = await self.get_label(db=db, project_id=project_id, label_id=label_id)

        if label_in.name is not None and label_in.name.lower() != existing.name.lower():
            duplicate = await self.repo.get_by_name_and_project(
                db=db, name=label_in.name, project_id=project_id
            )
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Label with name '{label_in.name}' already exists in project {project_id}.",
                )

        updated = await self.repo.update_label(
            db=db, label_id=label_id, label_in=label_in
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in project {project_id}.",
            )
        return updated

    async def delete_label(
        self, db: AsyncSession, project_id: int, label_id: int
    ) -> bool:
        await self.get_label(db=db, project_id=project_id, label_id=label_id)
        return await self.repo.delete_label(db=db, label_id=label_id)

    # [Ngày 6] bổ sung gán/bỏ label cho task
    async def assign_label_to_task(
        self, db: AsyncSession, task_id: int, label_id: int, actor: User
    ) -> Label:
        """Gán label vào task."""
        task = await self.task_repo.get_by_id(db, task_id)
        if not task:
            raise NotFoundException(
                message="Task not found", detail=f"Task id={task_id} does not exist."
            )

        label = await self.repo.get_by_id(db, label_id)
        if not label:
            raise NotFoundException(
                message="Label not found", detail=f"Label id={label_id} does not exist."
            )

        if label.project_id != task.project_id:
            raise ConflictException(
                message="Label project mismatch",
                detail="Label does not belong to the same project as the task.",
            )

        # Kiểm tra quyền workspace OWNER / EDITOR
        project = await self.project_repo.get_by_id(db, task.project_id)
        if project is None:
            raise NotFoundException(
                message="Project not found", detail=f"Project id={task.project_id} does not exist."
            )

        membership = await self.member_repo.get_membership(
            db, workspace_id=project.workspace_id, user_id=actor.id
        )
        if not membership or membership.role not in (
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
        ):
            raise ForbiddenException(
                message="Insufficient workspace role",
                detail="Must be workspace OWNER or EDITOR to assign labels to tasks.",
            )

        await self.task_label_repo.assign_label(db, task_id=task_id, label_id=label_id)
        # [Ngày 7] Invalidate cache sau khi gán label cho task
        await invalidate_project_tasks_cache(task.project_id)
        return label

    async def remove_label_from_task(
        self, db: AsyncSession, task_id: int, label_id: int, actor: User
    ) -> bool:
        """Bỏ label khỏi task."""
        task = await self.task_repo.get_by_id(db, task_id)
        if not task:
            raise NotFoundException(
                message="Task not found", detail=f"Task id={task_id} does not exist."
            )

        label = await self.repo.get_by_id(db, label_id)
        if not label:
            raise NotFoundException(
                message="Label not found", detail=f"Label id={label_id} does not exist."
            )

        # Kiểm tra quyền workspace OWNER / EDITOR
        project = await self.project_repo.get_by_id(db, task.project_id)
        if project is None:
            raise NotFoundException(
                message="Project not found", detail=f"Project id={task.project_id} does not exist."
            )

        membership = await self.member_repo.get_membership(
            db, workspace_id=project.workspace_id, user_id=actor.id
        )
        if not membership or membership.role not in (
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
        ):
            raise ForbiddenException(
                message="Insufficient workspace role",
                detail="Must be workspace OWNER or EDITOR to remove labels from tasks.",
            )

        removed = await self.task_label_repo.remove_label(db, task_id=task_id, label_id=label_id)
        # [Ngày 7] Invalidate cache sau khi bỏ label khỏi task
        await invalidate_project_tasks_cache(task.project_id)
        return removed

