# [Ngày 5] TaskService — CRUD, assign, status state machine, priority/due_date

from typing import Dict, List, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import TaskPriority, TaskStatus, WorkspaceMemberRole
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.schemas.task import TaskCreate, TaskUpdate

# [Ngày 5] State machine chuyển trạng thái task
ALLOWED_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.IN_REVIEW, TaskStatus.TODO},
    TaskStatus.IN_REVIEW: {TaskStatus.DONE, TaskStatus.IN_PROGRESS},
    TaskStatus.DONE: set(),
}


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        member_repo: WorkspaceMemberRepository,
    ) -> None:
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.member_repo = member_repo

    async def create_task(
        self,
        db: AsyncSession,
        *,
        project: Project,
        creator: User,
        data: TaskCreate,
    ) -> Task:
        """Tạo task — mặc định status=TODO, priority=MEDIUM (hoặc theo request)."""
        priority = data.priority if data.priority is not None else TaskPriority.MEDIUM
        return await self.task_repo.create(
            db,
            obj_in={
                "project_id": project.id,
                "title": data.title,
                "description": data.description,
                "status": TaskStatus.TODO,
                "priority": priority,
                "due_date": data.due_date,
                "created_by": creator.id,
            },
        )

    async def list_tasks(
        self, db: AsyncSession, *, project_id: int
    ) -> List[Task]:
        """Danh sách task trong project (chưa filter/pagination — Ngày 6)."""
        return await self.task_repo.list_by_project(db, project_id=project_id)

    async def get_task(self, db: AsyncSession, *, task_id: int) -> Task:
        """Lấy task theo ID."""
        task = await self.task_repo.get_by_id(db, task_id)
        if task is None:
            raise NotFoundException(
                message="Task not found",
                detail=f"Task id={task_id} does not exist.",
            )
        return task

    async def update_task(
        self,
        db: AsyncSession,
        *,
        task: Task,
        data: TaskUpdate,
        actor: User,
    ) -> Task:
        """PATCH task — validate assignee và status transition khi có."""
        update_data = data.model_dump(exclude_unset=True)

        if "assignee_id" in update_data and update_data["assignee_id"] is not None:
            await self._validate_assignee(
                db,
                project_id=task.project_id,
                assignee_id=update_data["assignee_id"],
            )

        if "status" in update_data:
            new_status = update_data["status"]
            await self._validate_status_transition(
                db,
                task=task,
                new_status=new_status,
                actor=actor,
            )

        return await self.task_repo.update(db, db_obj=task, obj_in=update_data)

    async def delete_task(self, db: AsyncSession, *, task_id: int) -> None:
        """Xoá task theo ID."""
        deleted = await self.task_repo.delete(db, id=task_id)
        if not deleted:
            raise NotFoundException(
                message="Task not found",
                detail=f"Task id={task_id} does not exist.",
            )

    async def _validate_assignee(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        assignee_id: int,
    ) -> None:
        """Assignee phải là thành viên workspace chứa project."""
        project = await self.project_repo.get_by_id(db, project_id)
        if project is None:
            raise NotFoundException(
                message="Project not found",
                detail=f"Project id={project_id} does not exist.",
            )

        membership = await self.member_repo.get_membership(
            db, workspace_id=project.workspace_id, user_id=assignee_id
        )
        if membership is None:
            raise ConflictException(
                message="Assignee is not a workspace member",
                detail=(
                    f"User id={assignee_id} is not a member of workspace "
                    f"id={project.workspace_id}."
                ),
            )

    async def _validate_status_transition(
        self,
        db: AsyncSession,
        *,
        task: Task,
        new_status: TaskStatus,
        actor: User,
    ) -> None:
        """Validate chuyển trạng thái theo ALLOWED_TRANSITIONS."""
        current = task.status
        if current == new_status:
            return

        allowed = ALLOWED_TRANSITIONS.get(current, set())

        # [Ngày 5] OWNER được reopen DONE → IN_PROGRESS
        if current == TaskStatus.DONE and new_status == TaskStatus.IN_PROGRESS:
            project = await self.project_repo.get_by_id(db, task.project_id)
            if project is not None:
                membership = await self.member_repo.get_membership(
                    db,
                    workspace_id=project.workspace_id,
                    user_id=actor.id,
                )
                if membership and membership.role == WorkspaceMemberRole.OWNER:
                    return

        if new_status not in allowed:
            raise ConflictException(
                message="Invalid status transition",
                detail=(
                    f"Cannot transition from {current.value} to {new_status.value}."
                ),
            )
