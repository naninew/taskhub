# [Ngày 4] Pydantic schemas cho Workspace API

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import WorkspaceMemberRole


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Tên workspace")


class WorkspaceRead(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberInvite(BaseModel):
    email: EmailStr = Field(..., description="Email user cần mời")
    role: WorkspaceMemberRole = Field(
        default=WorkspaceMemberRole.EDITOR,
        description="Role gán cho member (EDITOR hoặc VIEWER)",
    )


class MemberRead(BaseModel):
    workspace_id: int
    user_id: int
    role: WorkspaceMemberRole
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)
