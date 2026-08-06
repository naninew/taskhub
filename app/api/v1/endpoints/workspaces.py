# [Ngày 4] Workspace endpoints: POST/GET workspace, POST/DELETE member

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    CurrentUserDep,
    DbDep,
    get_workspace_service,
    require_workspace_role,
)
from app.models.enums import WorkspaceMemberRole
from app.schemas.workspace import MemberInvite, MemberRead, WorkspaceCreate, WorkspaceRead
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post(
    "",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo workspace mới",
    description="Tạo một workspace mới. Người tạo tự động được gán quyền OWNER.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
    },
)
async def create_workspace(
    data: WorkspaceCreate,
    db: DbDep,
    current_user: CurrentUserDep,
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceRead:
    """Tạo workspace — người tạo tự động trở thành OWNER."""
    workspace = await service.create_workspace(db=db, user=current_user, data=data)
    return WorkspaceRead.model_validate(workspace)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceRead,
    status_code=status.HTTP_200_OK,
    summary="Chi tiết workspace",
    description="Lấy chi tiết không gian làm việc. Yêu cầu có quyền thành viên trong workspace.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không có quyền truy cập workspace (chưa là member)"},
        404: {"description": "Workspace không tồn tại"},
    },
)
async def get_workspace(
    workspace_id: int,
    db: DbDep,
    current_user: CurrentUserDep,
    service: WorkspaceService = Depends(get_workspace_service),
    _member=Depends(
        require_workspace_role(
            WorkspaceMemberRole.OWNER,
            WorkspaceMemberRole.EDITOR,
            WorkspaceMemberRole.VIEWER,
        )
    ),
) -> WorkspaceRead:
    """Lấy thông tin workspace — yêu cầu là member."""
    workspace = await service.get_workspace(
        db=db, workspace_id=workspace_id, user=current_user
    )
    return WorkspaceRead.model_validate(workspace)


@router.post(
    "/{workspace_id}/members",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Mời member vào workspace",
    description="Mời người dùng vào workspace bằng email (Chỉ Workspace OWNER có quyền).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Yêu cầu quyền Workspace OWNER"},
        404: {"description": "Không tìm thấy user với email được mời"},
        409: {"description": "User đã là thành viên của workspace"},
    },
)
async def invite_member(
    workspace_id: int,
    data: MemberInvite,
    db: DbDep,
    current_user: CurrentUserDep,
    service: WorkspaceService = Depends(get_workspace_service),
    _owner=Depends(require_workspace_role(WorkspaceMemberRole.OWNER)),
) -> MemberRead:
    """Mời user vào workspace — chỉ OWNER."""
    member, invited_user = await service.invite_member(
        db=db,
        workspace_id=workspace_id,
        inviter=current_user,
        data=data,
    )
    return MemberRead(
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        role=member.role,
        email=invited_user.email,
        full_name=invited_user.full_name,
    )


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Xoá member khỏi workspace",
    description="Xoá thành viên khỏi workspace (Chỉ Workspace OWNER; không thể xoá OWNER duy nhất còn lại).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Yêu cầu quyền Workspace OWNER"},
        404: {"description": "Thành viên không tồn tại trong workspace"},
        409: {"description": "Không thể xoá OWNER duy nhất còn lại của workspace"},
    },
)
async def remove_member(
    workspace_id: int,
    user_id: int,
    db: DbDep,
    current_user: CurrentUserDep,
    service: WorkspaceService = Depends(get_workspace_service),
    _owner=Depends(require_workspace_role(WorkspaceMemberRole.OWNER)),
) -> dict[str, str]:
    """Xoá member — chỉ OWNER; không xoá được OWNER cuối cùng."""
    await service.remove_member(
        db=db,
        workspace_id=workspace_id,
        target_user_id=user_id,
        actor=current_user,
    )
    return {"message": "Member removed successfully."}
