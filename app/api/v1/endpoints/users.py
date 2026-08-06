# [Ngày 1] Stub router cho Users API (sẽ bổ sung ở Ngày 3)
# [Ngày 3] User endpoints: GET/PATCH /users/me, POST /users/me/change-password

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import CurrentUserDep, DbDep, get_user_service
from app.schemas.user import ChangePasswordRequest, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Lấy profile user hiện tại",
    description="Trả về thông tin chi tiết tài khoản của người dùng đang đăng nhập.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
    },
)
async def get_me(current_user: CurrentUserDep) -> UserRead:
    """Trả về thông tin profile của user đang đăng nhập."""
    return UserRead.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật profile user hiện tại",
    description="Cập nhật tên đầy đủ hoặc email của người dùng đang đăng nhập.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        409: {"description": "Email mới đã tồn tại trên tài khoản khác"},
    },
)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUserDep,
    db: DbDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Cập nhật full_name hoặc email của user đang đăng nhập."""
    updated = await service.update_profile(db=db, user=current_user, data=data)
    return UserRead.model_validate(updated)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Đổi mật khẩu",
    description="Đổi mật khẩu người dùng hiện tại (yêu cầu xác thực mật khẩu cũ).",
    responses={
        400: {"description": "Mật khẩu cũ không chính xác"},
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
    },
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUserDep,
    db: DbDep,
    service: UserService = Depends(get_user_service),
) -> dict[str, str]:
    """Đổi mật khẩu — yêu cầu nhập mật khẩu cũ để xác thực."""
    await service.change_password(db=db, user=current_user, data=data)
    return {"message": "Password changed successfully."}
