# [Ngày 2] SQLAlchemy ORM model cho bảng tasks

from datetime import datetime, date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, ForeignKey, Enum, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TaskStatus, TaskPriority

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.task_label import TaskLabel
    from app.models.comment import Comment


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    task_labels: Mapped[List["TaskLabel"]] = relationship("TaskLabel", back_populates="task", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
