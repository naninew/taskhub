# [Ngày 5] Task endpoints — CRUD trong project, assign, status, priority/due_date

from typing import List

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    CurrentUserDep,
    DbDep,
    get_task_service,
    require_project_access,
)
from app.models.enums import WorkspaceMemberRole
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter()

TaskEditorDep = Depends(
    require_project_access(
        WorkspaceMemberRole.OWNER,
        WorkspaceMemberRole.EDITOR,
    )
)
TaskReaderDep = Depends(
    require_project_access(
        WorkspaceMemberRole.OWNER,
        WorkspaceMemberRole.EDITOR,
        WorkspaceMemberRole.VIEWER,
    )
)


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo task trong project",
)
async def create_task(
    data: TaskCreate,
    db: DbDep,
    current_user: CurrentUserDep,
    project: Project = TaskEditorDep,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Tạo task — OWNER/EDITOR."""
    task = await service.create_task(
        db, project=project, creator=current_user, data=data
    )
    return TaskRead.model_validate(task)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[TaskRead],
    status_code=status.HTTP_200_OK,
    summary="Danh sách task trong project",
)
async def list_tasks(
    db: DbDep,
    project: Project = TaskReaderDep,
    service: TaskService = Depends(get_task_service),
) -> List[TaskRead]:
    """List task — mọi member workspace (chưa filter/pagination — Ngày 6)."""
    tasks = await service.list_tasks(db, project_id=project.id)
    return [TaskRead.model_validate(t) for t in tasks]


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật task (assign, status, priority, due_date...)",
)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: DbDep,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """PATCH task — validate RBAC qua project của task."""
    task = await service.get_task(db, task_id=task_id)
    check_editor = require_project_access(
        WorkspaceMemberRole.OWNER,
        WorkspaceMemberRole.EDITOR,
    )
    await check_editor(
        project_id=task.project_id, db=db, current_user=current_user
    )
    updated = await service.update_task(
        db, task=task, data=data, actor=current_user
    )
    return TaskRead.model_validate(updated)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Xoá task",
)
async def delete_task(
    task_id: int,
    db: DbDep,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_task_service),
) -> dict[str, str]:
    """Xoá task — OWNER/EDITOR."""
    task = await service.get_task(db, task_id=task_id)
    check_editor = require_project_access(
        WorkspaceMemberRole.OWNER,
        WorkspaceMemberRole.EDITOR,
    )
    await check_editor(
        project_id=task.project_id, db=db, current_user=current_user
    )
    await service.delete_task(db, task_id=task_id)
    return {"message": "Task deleted successfully."}
