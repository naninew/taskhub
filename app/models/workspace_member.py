# [Ngày 2] SQLAlchemy ORM model cho bảng workspace_members

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WorkspaceMemberRole

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[WorkspaceMemberRole] = mapped_column(Enum(WorkspaceMemberRole), default=WorkspaceMemberRole.VIEWER, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="workspace_memberships")
