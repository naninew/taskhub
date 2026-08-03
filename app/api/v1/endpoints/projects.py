# [Ngày 5] Project endpoints — CRUD trong workspace + archive

from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    CurrentUserDep,
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
