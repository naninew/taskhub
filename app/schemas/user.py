# [Ngày 3] Pydantic v2 schemas cho User API

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Họ và tên mới")
    email: Optional[str] = Field(None, min_length=3, max_length=255, description="Email mới")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Mật khẩu hiện tại")
    new_password: str = Field(..., min_length=8, max_length=128, description="Mật khẩu mới")
