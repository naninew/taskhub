# [Ngày 1] Cấu hình ứng dụng dùng pydantic-settings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TaskHub API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    # [Ngày 2] Cấu hình DATABASE_URL (mặc định dùng SQLite async cho dev/test, hỗ trợ PostgreSQL qua biến môi trường)
    DATABASE_URL: str = "sqlite+aiosqlite:///./taskhub.db"
    # [Ngày 3] Cấu hình JWT — override SECRET_KEY qua biến môi trường trên production
    SECRET_KEY: str = "taskhub-dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
