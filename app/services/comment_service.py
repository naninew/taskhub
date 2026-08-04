# [Ngày 6] CommentService — Tạo và xoá comment trên task với kiểm tra phân quyền

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.comment import Comment
from app.models.enums import UserRole, WorkspaceMemberRole
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.schemas.comment import CommentCreate


class CommentService:
    """[Ngày 6] Service xử lý nghiệp vụ cho Comment."""

    def __init__(
        self,
        comment_repo: CommentRepository,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        member_repo: WorkspaceMemberRepository,
    ) -> None:
        self.comment_repo = comment_repo
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.member_repo = member_repo

    async def create_comment(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        author: User,
        data: CommentCreate,
    ) -> Comment:
        """Tạo comment trên task bởi author (phải là member workspace)."""
        task = await self.task_repo.get_by_id(db, task_id)
        if task is None:
            raise NotFoundException(
                message="Task not found",
                detail=f"Task id={task_id} does not exist.",
            )

        project = await self.project_repo.get_by_id(db, task.project_id)
        if project is None:
            raise NotFoundException(
                message="Project not found",
                detail=f"Project id={task.project_id} does not exist.",
            )

        membership = await self.member_repo.get_membership(
            db, workspace_id=project.workspace_id, user_id=author.id
        )
        if membership is None:
            raise ForbiddenException(
                message="Not a workspace member",
                detail="You must be a member of the workspace to comment on this task.",
            )

        return await self.comment_repo.create(
            db,
            obj_in={
                "task_id": task_id,
                "author_id": author.id,
                "content": data.content,
            },
        )

    async def delete_comment(
        self,
        db: AsyncSession,
        *,
        comment_id: int,
        actor: User,
    ) -> None:
        """Xoá comment — chỉ tác giả comment hoặc workspace OWNER/ADMIN mới được xoá."""
        comment = await self.comment_repo.get_by_id(db, comment_id)
        if comment is None:
            raise NotFoundException(
                message="Comment not found",
                detail=f"Comment id={comment_id} does not exist.",
            )

        # 1. Tác giả comment được phép xoá
        if comment.author_id == actor.id:
            await self.comment_repo.delete(db, id=comment_id)
            return

        # 2. Nếu không phải tác giả, kiểm tra hệ thống ADMIN hoặc workspace OWNER
        if actor.role == UserRole.ADMIN:
            await self.comment_repo.delete(db, id=comment_id)
            return

        task = await self.task_repo.get_by_id(db, comment.task_id)
        if task is None:
            raise NotFoundException(
                message="Task not found",
                detail=f"Task id={comment.task_id} does not exist.",
            )

        project = await self.project_repo.get_by_id(db, task.project_id)
        if project is None:
            raise NotFoundException(
                message="Project not found",
                detail=f"Project id={task.project_id} does not exist.",
            )

        membership = await self.member_repo.get_membership(
            db, workspace_id=project.workspace_id, user_id=actor.id
        )
        if membership is not None and membership.role == WorkspaceMemberRole.OWNER:
            await self.comment_repo.delete(db, id=comment_id)
            return

        raise ForbiddenException(
            message="Permission denied",
            detail="Only the comment author or workspace OWNER can delete this comment.",
        )
