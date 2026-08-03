# [Ngày 5] Pydantic schemas cho Project API

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Tên project")
    description: Optional[str] = Field(None, description="Mô tả project")


class ProjectRead(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tên mới")
    description: Optional[str] = Field(None, description="Mô tả mới")
