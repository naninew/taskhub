# [Ngày 5] TaskService — CRUD, assign, status state machine, priority/due_date
# [Ngày 6] nâng cấp từ Ngày 5: thêm list_tasks hỗ trợ filter (status, priority, assignee) + pagination (PaginatedResponse)
# [Ngày 7] nâng cấp từ Ngày 6: tích hợp Redis cache (TTL 60s) cho list_tasks và invalidate cache khi create/update/delete task

import json
from typing import Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import logger
from app.db.redis import get_redis, invalidate_project_tasks_cache
from app.models.enums import TaskPriority, TaskStatus, WorkspaceMemberRole
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

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
        """Tạo task — mặc định status=TODO, priority=MEDIUM (hoặc theo request) + invalidate cache."""
        priority = data.priority if data.priority is not None else TaskPriority.MEDIUM
        task = await self.task_repo.create(
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
        # [Ngày 7] Invalidate cache sau khi tạo task thành công
        await invalidate_project_tasks_cache(project.id)
        return task

    # [Ngày 6] nâng cấp từ Ngày 5: thêm filter (status, priority, assignee) + pagination
    # [Ngày 7] nâng cấp từ Ngày 6: cache Redis key "tasks:{project_id}:{status}:{priority}:{assignee_id}:{page}:{limit}" TTL 60s
    async def list_tasks(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[TaskRead]:
        """Danh sách task trong project trả về PaginatedResponse[TaskRead] với Redis Cache."""
        status_str = status.value if status else "all"
        priority_str = priority.value if priority else "all"
        assignee_str = str(assignee_id) if assignee_id is not None else "all"
        cache_key = f"tasks:{project_id}:{status_str}:{priority_str}:{assignee_str}:{page}:{limit}"

        redis = await get_redis()
        if redis:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    logger.info(f"[CACHE HIT] Key: {cache_key}")
                    data = json.loads(cached)
                    return PaginatedResponse[TaskRead].model_validate(data)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        logger.info(f"[CACHE MISS] Key: {cache_key} — Fetching from DB")
        items, total = await self.task_repo.list_tasks_filtered(
            db,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            page=page,
            limit=limit,
        )
        task_reads = [TaskRead.model_validate(t) for t in items]
        result = PaginatedResponse[TaskRead](
            items=task_reads,
            total=total,
            page=page,
            limit=limit,
        )

        if redis:
            try:
                await redis.setex(cache_key, 60, result.model_dump_json())
                logger.info(f"[CACHE SET] Key: {cache_key} (TTL 60s)")
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        return result

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
        """PATCH task — validate assignee và status transition khi có + invalidate cache."""
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

        updated_task = await self.task_repo.update(db, db_obj=task, obj_in=update_data)
        # [Ngày 7] Invalidate cache sau khi cập nhật task
        await invalidate_project_tasks_cache(task.project_id)
        return updated_task

    async def delete_task(self, db: AsyncSession, *, task_id: int) -> None:
        """Xoá task theo ID + invalidate cache."""
        task = await self.get_task(db, task_id=task_id)
        project_id = task.project_id
        deleted = await self.task_repo.delete(db, id=task_id)
        if not deleted:
            raise NotFoundException(
                message="Task not found",
                detail=f"Task id={task_id} does not exist.",
            )
        # [Ngày 7] Invalidate cache sau khi xoá task
        await invalidate_project_tasks_cache(project_id)


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
