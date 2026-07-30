# [Ngày 3] UserRepository kế thừa BaseRepository[User], thêm get_by_email

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Tra cứu user theo email (không phân biệt hoa thường)."""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalars().first()


user_repository = UserRepository()
