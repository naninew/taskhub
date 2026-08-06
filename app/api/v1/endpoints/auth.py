# [Ngày 1] Stub router cho Auth API (sẽ bổ sung ở Ngày 3)
# [Ngày 3] Auth endpoints: register, login, refresh, logout

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import DbDep, get_auth_service
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description="Đăng ký tài khoản người dùng mới hệ thống với email, tên đầy đủ và mật khẩu.",
    responses={
        400: {"description": "Dữ liệu không hợp lệ hoặc thiếu thông tin bắt buộc"},
        409: {"description": "Email đã được đăng ký trong hệ thống"},
    },
)
async def register(
    data: RegisterRequest,
    db: DbDep,
    service: AuthService = Depends(get_auth_service),
) -> UserRead:
    """Đăng ký user mới với email, full_name và password."""
    user = await service.register(db=db, data=data)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập — nhận access + refresh token",
    description="Xác thực người dùng bằng email và mật khẩu, trả về cặp JWT Access Token và Refresh Token.",
    responses={
        401: {"description": "Email hoặc mật khẩu không chính xác"},
    },
)
async def login(
    data: LoginRequest,
    db: DbDep,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    """Đăng nhập bằng email/password, trả về cặp JWT token."""
    return await service.login(db=db, data=data)


@router.post(
    "/refresh",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Đổi refresh token lấy cặp token mới",
    description="Xử lý Token Rotation: nhận Refresh Token cũ, thu hồi nó và cấp lại cặp token mới.",
    responses={
        401: {"description": "Refresh token không hợp lệ, đã hết hạn hoặc đã bị thu hồi"},
    },
)
async def refresh_token(
    data: RefreshRequest,
    db: DbDep,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    """Dùng refresh token hợp lệ (chưa revoke) để lấy access + refresh token mới."""
    return await service.refresh(db=db, refresh_token=data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Đăng xuất — revoke refresh token",
    description="Thu hồi Refresh Token hiện tại, vô hiệu hóa việc gia hạn session.",
    responses={
        401: {"description": "Refresh token không hợp lệ hoặc đã thu hồi"},
    },
)
async def logout(
    data: RefreshRequest,
    db: DbDep,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Logout thật sự — đánh dấu refresh token revoked trong DB."""
    await service.logout(db=db, refresh_token=data.refresh_token)
    return {"message": "Logged out successfully."}
