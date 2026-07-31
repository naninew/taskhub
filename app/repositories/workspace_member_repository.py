# [Ngày 4] WorkspaceMemberRepository — composite PK (workspace_id, user_id)

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import WorkspaceMemberRole
from app.models.workspace_member import WorkspaceMember
from app.repositories.base import BaseRepository


class WorkspaceMemberRepository(BaseRepository[WorkspaceMember]):
    def __init__(self) -> None:
        super().__init__(WorkspaceMember)

    async def get_membership(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        user_id: int,
    ) -> Optional[WorkspaceMember]:
        """Tra cứu membership theo workspace_id + user_id."""
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def list_by_workspace(
        self, db: AsyncSession, *, workspace_id: int
    ) -> List[WorkspaceMember]:
        """Danh sách member của workspace (kèm thông tin user)."""
        result = await db.execute(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == workspace_id)
        )
        return list(result.scalars().all())

    async def count_owners(
        self, db: AsyncSession, *, workspace_id: int
    ) -> int:
        """Đếm số OWNER trong workspace — dùng chặn xoá OWNER cuối cùng."""
        result = await db.execute(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceMemberRole.OWNER,
            )
        )
        return result.scalar_one() or 0

    async def add_member(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        user_id: int,
        role: WorkspaceMemberRole,
    ) -> WorkspaceMember:
        """Thêm member mới vào workspace."""
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    async def remove_member(
        self,
        db: AsyncSession,
        *,
        workspace_id: int,
        user_id: int,
    ) -> bool:
        """Xoá member khỏi workspace theo composite key."""
        member = await self.get_membership(
            db, workspace_id=workspace_id, user_id=user_id
        )
        if member is None:
            return False
        await db.delete(member)
        await db.commit()
        return True


workspace_member_repository = WorkspaceMemberRepository()
