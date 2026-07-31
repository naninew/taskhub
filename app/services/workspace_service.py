# [Ngày 4] WorkspaceService — create, invite member, remove member

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.enums import WorkspaceMemberRole
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import MemberInvite, WorkspaceCreate


class WorkspaceService:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        user_repo: UserRepository,
    ) -> None:
        self.workspace_repo = workspace_repo
        self.member_repo = member_repo
        self.user_repo = user_repo

    async def create_workspace(
        self, db: AsyncSession, *, user: User, data: WorkspaceCreate
    ) -> Workspace:
        """Tạo workspace — người tạo tự động là OWNER trong workspace_members."""
        workspace = await self.workspace_repo.create(
            db,
            obj_in={"name": data.name, "owner_id": user.id},
        )
        await self.member_repo.add_member(
            db,
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceMemberRole.OWNER,
        )
        return workspace

    async def get_workspace(
        self, db: AsyncSession, *, workspace_id: int, user: User
    ) -> Workspace:
        """Lấy workspace — yêu cầu user là member."""
        workspace = await self.workspace_repo.get_by_id(db, workspace_id)
        if workspace is None:
            raise NotFoundException(
                message="Workspace not found",
                detail=f"Workspace id={workspace_id} does not exist.",
            )

        membership = await self.member_repo.get_membership(
            db, workspace_id=workspace_id, user_id=user.id
        )
        if membership is None:
            raise ForbiddenException(
                message="Not a workspace member",
                detail="You must be a member to access this workspace.",
            )
        return workspace

    async def invite_member(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        inviter: User,
        data: MemberInvite,
    ) -> tuple[WorkspaceMember, User]:
        """Mời member — chỉ OWNER được invite."""
        membership = await self._require_owner(
            db, workspace_id=workspace_id, user=inviter
        )

        if data.role == WorkspaceMemberRole.OWNER:
            raise ForbiddenException(
                message="Cannot assign OWNER role via invite",
                detail="Use workspace ownership transfer in a future release.",
            )

        invited_user = await self.user_repo.get_by_email(db, email=data.email)
        if invited_user is None:
            raise NotFoundException(
                message="User not found",
                detail=f"No user registered with email '{data.email}'.",
            )

        existing = await self.member_repo.get_membership(
            db, workspace_id=workspace_id, user_id=invited_user.id
        )
        if existing is not None:
            raise ConflictException(
                message="User already a member",
                detail=f"User '{data.email}' is already in this workspace.",
            )

        member = await self.member_repo.add_member(
            db,
            workspace_id=membership.workspace_id,
            user_id=invited_user.id,
            role=data.role,
        )
        return member, invited_user

    async def remove_member(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        target_user_id: int,
        actor: User,
    ) -> None:
        """Remove member — chỉ OWNER; chặn xoá OWNER cuối cùng."""
        await self._require_owner(db, workspace_id=workspace_id, user=actor)

        target = await self.member_repo.get_membership(
            db, workspace_id=workspace_id, user_id=target_user_id
        )
        if target is None:
            raise NotFoundException(
                message="Member not found",
                detail=f"User id={target_user_id} is not a member of this workspace.",
            )

        if target.role == WorkspaceMemberRole.OWNER:
            owner_count = await self.member_repo.count_owners(
                db, workspace_id=workspace_id
            )
            if owner_count <= 1:
                raise ConflictException(
                    message="Cannot remove the last owner",
                    detail="Workspace must have at least one OWNER.",
                )

        removed = await self.member_repo.remove_member(
            db, workspace_id=workspace_id, user_id=target_user_id
        )
        if not removed:
            raise NotFoundException(
                message="Member not found",
                detail=f"User id={target_user_id} is not a member of this workspace.",
            )

    async def _require_owner(
        self, db: AsyncSession, *, workspace_id: int, user: User
    ) -> WorkspaceMember:
        """Kiểm tra user có role OWNER trong workspace."""
        membership = await self.member_repo.get_membership(
            db, workspace_id=workspace_id, user_id=user.id
        )
        if membership is None:
            raise ForbiddenException(
                message="Not a workspace member",
                detail="You must be a member to perform this action.",
            )
        if membership.role != WorkspaceMemberRole.OWNER:
            raise ForbiddenException(
                message="Owner role required",
                detail="Only workspace OWNER can perform this action.",
            )
        return membership
