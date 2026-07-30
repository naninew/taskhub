# [Ngày 1] Cấu hình ứng dụng dùng pydantic-settings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TaskHub API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    # [Ngày 2] Cấu hình DATABASE_URL (mặc định dùng SQLite async cho dev/test, hỗ trợ PostgreSQL qua biến môi trường)
    DATABASE_URL: str = "sqlite+aiosqlite:///./taskhub.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
