# [Ngày 3] UserService — profile GET/PATCH và đổi mật khẩu

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def update_profile(
        self, db: AsyncSession, *, user: User, data: UserUpdate
    ) -> User:
        """Cập nhật thông tin profile — kiểm tra email trùng nếu đổi email."""
        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data:
            new_email = update_data["email"].lower()
            existing = await self.user_repo.get_by_email(db, email=new_email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{new_email}' is already in use.",
                )
            update_data["email"] = new_email

        if not update_data:
            return user

        return await self.user_repo.update(db, db_obj=user, obj_in=update_data)

    async def change_password(
        self,
        db: AsyncSession,
        *,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """Đổi mật khẩu — yêu cầu xác thực mật khẩu cũ trước."""
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        await self.user_repo.update(
            db,
            db_obj=user,
            obj_in={"hashed_password": hash_password(data.new_password)},
        )
