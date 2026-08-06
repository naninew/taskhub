# [Ngày 5] Task endpoints — CRUD trong project, assign, status, priority/due_date
# [Ngày 6] NÂNG CẤP từ Ngày 5: GET /projects/{id}/tasks hỗ trợ filter (status, priority, assignee) + pagination (PaginatedResponse)
# [Ngày 7] NÂNG CẤP từ Ngày 5-6: thêm BackgroundTasks gửi email khi assign task

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.api.v1.deps import (
    CurrentUserDep,
    DbDep,
    get_task_service,
    require_project_access,
)
from app.models.enums import TaskPriority, TaskStatus, WorkspaceMemberRole
from app.models.project import Project
from app.repositories.user_repository import user_repository
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService
from app.tasks.email_tasks import send_assignment_email

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
    description="Tạo một task mới trong dự án. Tự động xóa Redis Cache danh sách task của project.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền (Cần vai trò OWNER hoặc EDITOR trong workspace)"},
        404: {"description": "Project không tồn tại"},
    },
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


# [Ngày 6, 7] GET /projects/{id}/tasks hỗ trợ filter, pagination & Redis Cache (TTL 60s)
@router.get(
    "/projects/{project_id}/tasks",
    response_model=PaginatedResponse[TaskRead],
    status_code=status.HTTP_200_OK,
    summary="Danh sách task trong project (filter & pagination)",
    description="Lấy danh sách task phân trang và hỗ trợ lọc theo status, priority, assignee_id. Tích hợp Redis async cache.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không có quyền truy cập project"},
        404: {"description": "Project không tồn tại"},
    },
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


# [Ngày 7] NÂNG CẤP từ Ngày 5: thêm tham số BackgroundTasks để gửi email notification khi gán task
@router.patch(
    "/tasks/{task_id}",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật task (assign, status, priority, due_date...)",
    description="Cập nhật task (chuyển trạng thái theo state machine, đổi độ ưu tiên, assign member). Tự động xóa Redis Cache và gửi Background Email nếu đổi người được gán.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền cập nhật task"},
        404: {"description": "Task hoặc Project không tồn tại"},
        409: {"description": "Chuyển trạng thái task không hợp lệ hoặc assignee không phải thành viên workspace"},
    },
)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: DbDep,
    current_user: CurrentUserDep,
    background_tasks: BackgroundTasks,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """PATCH task — validate RBAC qua project của task và gửi email background khi assign."""
    task = await service.get_task(db, task_id=task_id)
    check_editor = require_project_access(
        WorkspaceMemberRole.OWNER,
        WorkspaceMemberRole.EDITOR,
    )
    await check_editor(
        project_id=task.project_id, db=db, current_user=current_user
    )

    old_assignee_id = task.assignee_id
    updated = await service.update_task(
        db, task=task, data=data, actor=current_user
    )

    # [Ngày 7] Gọi background task gửi email nếu task được assign cho user mới
    if data.assignee_id is not None and data.assignee_id != old_assignee_id:
        assignee_user = await user_repository.get_by_id(db, data.assignee_id)
        if assignee_user and assignee_user.email:
            background_tasks.add_task(
                send_assignment_email,
                user_email=assignee_user.email,
                task_title=updated.title,
            )

    return TaskRead.model_validate(updated)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Xoá task",
    description="Xoá một task khỏi dự án. Tự động xóa Redis Cache danh sách task.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền xóa task"},
        404: {"description": "Task không tồn tại"},
    },
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
