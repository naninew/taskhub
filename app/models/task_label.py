# [Ngày 2] SQLAlchemy ORM model cho bảng trung gian task_labels

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.label import Label


class TaskLabel(Base):
    __tablename__ = "task_labels"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    label_id: Mapped[int] = mapped_column(ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="task_labels")
    label: Mapped["Label"] = relationship("Label", back_populates="task_labels")
