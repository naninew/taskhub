# [Ngày 1] Dependency injection cho API v1
# [Ngày 2] thay stub Ngày 1: get_db() giờ yield AsyncSession thật từ SQLAlchemy
# [Ngày 3] thêm get_current_user — decode Bearer JWT, tra user_repository
# [Ngày 4] thêm require_workspace_role — dependency factory kiểm tra RBAC workspace
# [Ngày 5] thêm require_project_access — tái sử dụng RBAC workspace qua project
# [Ngày 6] thêm get_comment_service cho Comment API

from typing import Annotated, Any, AsyncGenerator, Callable, Coroutine

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.enums import WorkspaceMemberRole
from app.models.project import Project
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.repositories.comment_repository import comment_repository
from app.repositories.label_repository import label_repository
from app.repositories.project_repository import project_repository
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.task_label_repository import task_label_repository
from app.repositories.task_repository import task_repository
from app.repositories.user_repository import user_repository
from app.repositories.workspace_member_repository import workspace_member_repository
from app.repositories.workspace_repository import workspace_repository
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.label_service import LabelService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

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
    return LabelService(
        repo=label_repository,
        task_label_repo=task_label_repository,
        task_repo=task_repository,
        project_repo=project_repository,
        member_repo=workspace_member_repository,
    )


def get_auth_service() -> AuthService:
    """Dependency injection trả về instance AuthService."""
    return AuthService(
        user_repo=user_repository,
        refresh_token_repo=refresh_token_repository,
    )


def get_user_service() -> UserService:
    """Dependency injection trả về instance UserService."""
    return UserService(user_repo=user_repository)


def get_workspace_service() -> WorkspaceService:
    """[Ngày 4] Dependency injection trả về instance WorkspaceService."""
    return WorkspaceService(
        workspace_repo=workspace_repository,
        member_repo=workspace_member_repository,
        user_repo=user_repository,
    )


def get_project_service() -> ProjectService:
    """[Ngày 5] Dependency injection trả về instance ProjectService."""
    return ProjectService(project_repo=project_repository)


def get_task_service() -> TaskService:
    """[Ngày 5] Dependency injection trả về instance TaskService."""
    return TaskService(
        task_repo=task_repository,
        project_repo=project_repository,
        member_repo=workspace_member_repository,
    )


def get_comment_service() -> CommentService:
    """[Ngày 6] Dependency injection trả về instance CommentService."""
    return CommentService(
        comment_repo=comment_repository,
        task_repo=task_repository,
        project_repo=project_repository,
        member_repo=workspace_member_repository,
    )


def require_workspace_role(
    *roles: WorkspaceMemberRole,
) -> Callable[..., Coroutine[Any, Any, WorkspaceMember]]:
    """[Ngày 4] Factory dependency — kiểm tra current_user có role phù hợp trong workspace."""

    allowed_roles = set(roles)

    async def _check_role(
        workspace_id: int,
        db: DbDep,
        current_user: CurrentUserDep,
    ) -> WorkspaceMember:
        membership = await workspace_member_repository.get_membership(
            db,
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
        if membership is None:
            raise ForbiddenException(
                message="Not a workspace member",
                detail="You must be a member to access this workspace.",
            )
        if membership.role not in allowed_roles:
            raise ForbiddenException(
                message="Insufficient workspace role",
                detail=f"Required role(s): {[r.value for r in allowed_roles]}.",
            )
        return membership

    return _check_role


def require_project_access(
    *roles: WorkspaceMemberRole,
) -> Callable[..., Coroutine[Any, Any, Project]]:
    """[Ngày 5] Factory dependency — tra project → workspace → require_workspace_role."""

    allowed_roles = set(roles)

    async def _check_access(
        project_id: int,
        db: DbDep,
        current_user: CurrentUserDep,
    ) -> Project:
        project = await project_repository.get_by_id(db, project_id)
        if project is None:
            raise NotFoundException(
                message="Project not found",
                detail=f"Project id={project_id} does not exist.",
            )

        membership = await workspace_member_repository.get_membership(
            db,
            workspace_id=project.workspace_id,
            user_id=current_user.id,
        )
        if membership is None:
            raise ForbiddenException(
                message="Not a workspace member",
                detail="You must be a member to access this project.",
            )
        if membership.role not in allowed_roles:
            raise ForbiddenException(
                message="Insufficient workspace role",
                detail=f"Required role(s): {[r.value for r in allowed_roles]}.",
            )
        return project

    return _check_access
