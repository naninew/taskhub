# [Ngày 1] Cấu hình ứng dụng dùng pydantic-settings
# [Ngày 7] nâng cấp: Settings(BaseSettings) fail-fast (DATABASE_URL, REDIS_URL, JWT_SECRET bắt buộc), hỗ trợ ENV và SMTP_*

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TaskHub API"
    API_V1_STR: str = "/api/v1"
    ENV: str = Field(default="development", description="Môi trường chạy: development / production / test")

    # Các biến bắt buộc — fail-fast nếu thiếu trong môi trường/.env
    DATABASE_URL: str = Field(..., description="Async Database URL (SQLite/PostgreSQL)")
    REDIS_URL: str = Field(..., description="Redis Connection URL")
    JWT_SECRET: str = Field(..., description="JWT Secret Key")

    # JWT Configs
    JWT_ACCESS_EXPIRE_MIN: int = Field(default=30, description="Hạn của Access Token tính bằng phút")
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=7, description="Hạn của Refresh Token tính bằng ngày")
    ALGORITHM: str = "HS256"

    # SMTP Configs (Optional)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: Optional[int] = Field(default=None)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # [Ngày 7] Properties tương thích ngược với Ngày 1-6
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.JWT_ACCESS_EXPIRE_MIN

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return self.JWT_REFRESH_EXPIRE_DAYS

    @property
    def ENVIRONMENT(self) -> str:
        return self.ENV


settings = Settings()

