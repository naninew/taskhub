# [Ngày 3] AuthService — register, login, refresh, logout với JWT + refresh token trong DB

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
    ) -> None:
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def register(self, db: AsyncSession, *, data: RegisterRequest) -> User:
        """Đăng ký user mới — kiểm tra email trùng, hash mật khẩu."""
        existing = await self.user_repo.get_by_email(db, email=data.email.lower())
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{data.email}' is already registered.",
            )

        user = await self.user_repo.create(
            db,
            obj_in={
                "email": data.email.lower(),
                "full_name": data.full_name,
                "hashed_password": hash_password(data.password),
                "role": UserRole.MEMBER,
                "is_active": True,
            },
        )
        return user

    async def _issue_token_pair(
        self, db: AsyncSession, *, user: User
    ) -> TokenPair:
        """Tạo cặp access/refresh token và lưu refresh token vào DB."""
        subject = str(user.id)
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_token_repo.create(
            db,
            obj_in={
                "token": refresh_token,
                "user_id": user.id,
                "revoked": False,
                "expires_at": expires_at,
            },
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def login(self, db: AsyncSession, *, data: LoginRequest) -> TokenPair:
        """Đăng nhập — verify mật khẩu, phát hành cặp token."""
        user = await self.user_repo.get_by_email(db, email=data.email.lower())
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )
        return await self._issue_token_pair(db, user=user)

    async def refresh(self, db: AsyncSession, *, refresh_token: str) -> TokenPair:
        """Đổi refresh token lấy cặp token mới — kiểm tra DB chưa revoke."""
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )

        db_token = await self.refresh_token_repo.get_by_token(db, token=refresh_token)
        if not db_token or not await self.refresh_token_repo.is_valid(db_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or expired.",
            )

        user = await self.user_repo.get_by_id(db, db_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive.",
            )

        # [Ngày 3] Revoke token cũ rồi phát hành cặp token mới (token rotation)
        await self.refresh_token_repo.revoke(db, db_obj=db_token)
        return await self._issue_token_pair(db, user=user)

    async def logout(self, db: AsyncSession, *, refresh_token: str) -> None:
        """Logout — đánh dấu refresh token revoked=True trong DB."""
        db_token = await self.refresh_token_repo.get_by_token(db, token=refresh_token)
        if db_token and not db_token.revoked:
            await self.refresh_token_repo.revoke(db, db_obj=db_token)
