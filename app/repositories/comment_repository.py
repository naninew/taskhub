# [Ngày 6] Repository SQLAlchemy cho resource Comment (BaseRepository[Comment])

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    """[Ngày 6] CommentRepository thao tác bảng comments kế thừa BaseRepository."""

    def __init__(self) -> None:
        super().__init__(Comment)

    async def list_by_task(
        self, db: AsyncSession, task_id: int
    ) -> List[Comment]:
        """Lấy danh sách comment của một task theo thứ tự thời gian tạo tăng dần."""
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


comment_repository = CommentRepository()
