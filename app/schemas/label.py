# [Ngày 1] Pydantic v2 schema cho resource Label

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LabelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tên label")
    color: str = Field("#000000", max_length=20, description="Mã màu HEX")


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Tên label")
    color: Optional[str] = Field(None, max_length=20, description="Mã màu HEX")


class LabelRead(LabelBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
