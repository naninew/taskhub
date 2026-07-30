# [Ngày 3] RefreshTokenRepository — tra cứu và revoke refresh token trong DB

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self) -> None:
        super().__init__(RefreshToken)

    async def get_by_token(
        self, db: AsyncSession, *, token: str
    ) -> Optional[RefreshToken]:
        """Lấy bản ghi refresh token theo chuỗi JWT."""
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalars().first()

    async def revoke(self, db: AsyncSession, *, db_obj: RefreshToken) -> RefreshToken:
        """Đánh dấu refresh token đã bị revoke (logout)."""
        db_obj.revoked = True
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def is_valid(self, db_obj: RefreshToken) -> bool:
        """Kiểm tra token chưa bị revoke và chưa hết hạn."""
        if db_obj.revoked:
            return False
        now = datetime.now(timezone.utc)
        expires_at = db_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > now


refresh_token_repository = RefreshTokenRepository()
