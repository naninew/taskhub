# [Ngày 5] Project endpoints — CRUD trong workspace + archive

from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    DbDep,
    get_project_service,
    require_workspace_role,
)
from app.models.enums import WorkspaceMemberRole
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo project trong workspace",
    description="Tạo một dự án mới thuộc workspace (Chỉ Workspace OWNER hoặc EDITOR có quyền).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền (Cần vai trò OWNER hoặc EDITOR trong workspace)"},
    },
)
async def create_project(
    workspace_id: int,
    data: ProjectCreate,
    db: DbDep,
    _member=Depends(
        require_workspace_role(
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
        )
    ),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Tạo project — OWNER/EDITOR; VIEWER chỉ đọc."""
    project = await service.create_project(
        db, workspace_id=workspace_id, data=data
    )
    return ProjectRead.model_validate(project)


@router.get(
    "/{workspace_id}/projects",
    response_model=List[ProjectRead],
    status_code=status.HTTP_200_OK,
    summary="Danh sách project trong workspace",
    description="Lấy danh sách các project thuộc workspace. Hỗ trợ query flag include_archived để xem dự án đã lưu trữ.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không có quyền truy cập workspace"},
    },
)
async def list_projects(
    workspace_id: int,
    db: DbDep,
    include_archived: bool = Query(
        default=False,
        description="Bao gồm project đã archive",
    ),
    _member=Depends(
        require_workspace_role(
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
            WorkspaceMemberRole.VIEWER,
        )
    ),
    service: ProjectService = Depends(get_project_service),
) -> List[ProjectRead]:
    """List project — mặc định chỉ ACTIVE."""
    projects = await service.list_projects(
        db,
        workspace_id=workspace_id,
        include_archived=include_archived,
    )
    return [ProjectRead.model_validate(p) for p in projects]


@router.get(
    "/{workspace_id}/projects/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Chi tiết project",
    description="Lấy chi tiết một dự án thuộc workspace.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không có quyền truy cập workspace"},
        404: {"description": "Project không tồn tại trong workspace"},
    },
)
async def get_project(
    workspace_id: int,
    project_id: int,
    db: DbDep,
    _member=Depends(
        require_workspace_role(
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
            WorkspaceMemberRole.VIEWER,
        )
    ),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Lấy chi tiết project — mọi member workspace."""
    project = await service.get_project(
        db, workspace_id=workspace_id, project_id=project_id
    )
    return ProjectRead.model_validate(project)


@router.patch(
    "/{workspace_id}/projects/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật project",
    description="Cập nhật tên hoặc mô tả dự án (Chỉ Workspace OWNER hoặc EDITOR có quyền).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền cập nhật project"},
        404: {"description": "Project không tồn tại"},
        409: {"description": "Không thể cập nhật project đã bị archive"},
    },
)
async def update_project(
    workspace_id: int,
    project_id: int,
    data: ProjectUpdate,
    db: DbDep,
    _member=Depends(
        require_workspace_role(
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
        )
    ),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Cập nhật project — OWNER/EDITOR."""
    project = await service.update_project(
        db,
        workspace_id=workspace_id,
        project_id=project_id,
        data=data,
    )
    return ProjectRead.model_validate(project)


@router.patch(
    "/{workspace_id}/projects/{project_id}/archive",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Archive project",
    description="Chuyển trạng thái dự án sang ARCHIVED (Soft delete/Archive, không xóa dữ liệu).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền archive project"},
        404: {"description": "Project không tồn tại"},
        409: {"description": "Project đã ở trạng thái ARCHIVED từ trước"},
    },
)
async def archive_project(
    workspace_id: int,
    project_id: int,
    db: DbDep,
    _member=Depends(
        require_workspace_role(
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
        )
    ),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Archive project — đổi status ARCHIVED, không xoá bản ghi."""
    project = await service.archive_project(
        db, workspace_id=workspace_id, project_id=project_id
    )
    return ProjectRead.model_validate(project)
