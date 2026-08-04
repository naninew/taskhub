# [Ngày 5] Task endpoints — CRUD trong project, assign, status, priority/due_date
# [Ngày 6] NÂNG CẤP từ Ngày 5: GET /projects/{id}/tasks hỗ trợ filter (status, priority, assignee) + pagination (PaginatedResponse)

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    CurrentUserDep,
    DbDep,
    get_task_service,
    require_project_access,
)
from app.models.enums import TaskPriority, TaskStatus, WorkspaceMemberRole
from app.models.project import Project
from app.schemas.common import PaginatedResponse
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


# [Ngày 6] NÂNG CẤP từ Ngày 5: GET /projects/{id}/tasks thêm filter & pagination, trả về PaginatedResponse[TaskRead]
@router.get(
    "/projects/{project_id}/tasks",
    response_model=PaginatedResponse[TaskRead],
    status_code=status.HTTP_200_OK,
    summary="Danh sách task trong project (filter & pagination)",
)
async def list_tasks(
    db: DbDep,
    status: Optional[TaskStatus] = Query(None, description="Lọc theo trạng thái"),
    priority: Optional[TaskPriority] = Query(None, description="Lọc theo độ ưu tiên"),
    assignee_id: Optional[int] = Query(None, description="Lọc theo ID người được gán"),
    page: int = Query(1, ge=1, description="Trang (bắt đầu từ 1)"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng bản ghi mỗi trang"),
    project: Project = TaskReaderDep,
    service: TaskService = Depends(get_task_service),
) -> PaginatedResponse[TaskRead]:
    """List task — filter theo status, priority, assignee + phân trang (page, limit)."""
    return await service.list_tasks(
        db,
        project_id=project.id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        page=page,
        limit=limit,
    )


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
