# [Ngày 1] Stub security module cho ứng dụng (sẽ triển khai JWT/Hash ở Ngày 3)
# [Ngày 3] Password hashing (passlib bcrypt) và JWT encode/decode (python-jose)

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# [Ngày 3] CryptContext dùng bcrypt để hash/verify mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash mật khẩu plain-text bằng bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So sánh mật khẩu plain-text với hash đã lưu trong DB."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT access token với payload sub + type=access + exp."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT refresh token với payload sub + type=refresh + exp."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": str(uuid4())}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode JWT và trả về payload; raise JWTError nếu token không hợp lệ."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
