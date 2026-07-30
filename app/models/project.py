# [Ngày 2] SQLAlchemy ORM model cho bảng projects

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.task import Task
    from app.models.label import Label


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="projects")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    labels: Mapped[List["Label"]] = relationship("Label", back_populates="project", cascade="all, delete-orphan")
