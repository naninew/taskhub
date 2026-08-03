# [Ngày 5] Pydantic schemas cho Task API

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề task")
    description: Optional[str] = Field(None, description="Mô tả task")
    priority: Optional[TaskPriority] = Field(
        default=TaskPriority.MEDIUM, description="Độ ưu tiên (mặc định MEDIUM)"
    )
    due_date: Optional[date] = Field(None, description="Hạn hoàn thành")


class TaskRead(BaseModel):
    id: int
    project_id: int
    assignee_id: Optional[int]
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    created_by: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = Field(None, description="Gán task cho member workspace")
    status: Optional[TaskStatus] = Field(None, description="Đổi trạng thái task")
    priority: Optional[TaskPriority] = Field(None, description="Đổi độ ưu tiên")
    due_date: Optional[date] = Field(None, description="Đổi hạn hoàn thành")


class TaskAssign(BaseModel):
    assignee_id: int = Field(..., description="User ID của member workspace")


class TaskStatusUpdate(BaseModel):
    status: TaskStatus = Field(..., description="Trạng thái mới")
