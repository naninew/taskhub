# [Ngày 2] SQLAlchemy ORM model cho bảng labels

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task_label import TaskLabel


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(50), default="#808080", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="labels")
    task_labels: Mapped[List["TaskLabel"]] = relationship("TaskLabel", back_populates="label", cascade="all, delete-orphan")
