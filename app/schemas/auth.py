# [Ngày 3] Pydantic v2 schemas cho Auth API

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email đăng ký")
    full_name: str = Field(..., min_length=1, max_length=255, description="Họ và tên")
    password: str = Field(..., min_length=8, max_length=128, description="Mật khẩu")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email đăng nhập")
    password: str = Field(..., min_length=1, description="Mật khẩu")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token cần đổi mới")
