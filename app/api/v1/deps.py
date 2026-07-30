# [Ngày 1] Dependency injection cho API v1
# [Ngày 2] thay stub Ngày 1: get_db() giờ yield AsyncSession thật từ SQLAlchemy
# [Ngày 3] thêm get_current_user — decode Bearer JWT, tra user_repository

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.label_repository import label_repository
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.user_repository import user_repository
from app.services.auth_service import AuthService
from app.services.label_service import LabelService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection trả về AsyncSession SQLAlchemy thật.

    [Ngày 2] thay stub Ngày 1 (yield None) bằng session thật từ AsyncSessionLocal.
    Session tự động commit/rollback và đóng khi request kết thúc.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Decode Bearer access token và trả về User hiện tại — nền tảng RBAC Ngày 4."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_repository.get_by_id(db, int(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_label_service() -> LabelService:
    """Dependency injection trả về instance LabelService."""
    return LabelService(repo=label_repository)


def get_auth_service() -> AuthService:
    """Dependency injection trả về instance AuthService."""
    return AuthService(
        user_repo=user_repository,
        refresh_token_repo=refresh_token_repository,
    )


def get_user_service() -> UserService:
    """Dependency injection trả về instance UserService."""
    return UserService(user_repo=user_repository)
