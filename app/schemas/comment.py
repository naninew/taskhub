# [Ngày 6] Pydantic v2 schemas cho resource Comment

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Nội dung comment")


class CommentRead(BaseModel):
    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
