# [Ngày 2] SQLAlchemy ORM model cho bảng workspaces

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace_member import WorkspaceMember
    from app.models.project import Project


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_workspaces")
    members: Mapped[List["WorkspaceMember"]] = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
