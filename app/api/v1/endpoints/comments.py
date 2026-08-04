# [Ngày 6] API Endpoints cho resource Comment: POST /tasks/{id}/comments, DELETE /comments/{id}

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUserDep, get_comment_service, get_db
from app.schemas.comment import CommentCreate, CommentRead
from app.services.comment_service import CommentService

router = APIRouter()


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm comment cho task",
)
async def create_comment(
    task_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUserDep = None,
    service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    """Tạo mới comment trên task (yêu cầu thành viên workspace)."""
    comment = await service.create_comment(
        db, task_id=task_id, author=current_user, data=data
    )
    return CommentRead.model_validate(comment)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_200_OK,
    summary="Xoá comment",
)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUserDep = None,
    service: CommentService = Depends(get_comment_service),
) -> dict[str, str]:
    """Xoá comment (chỉ tác giả comment hoặc workspace OWNER/ADMIN mới được xoá)."""
    await service.delete_comment(db, comment_id=comment_id, actor=current_user)
    return {"message": "Comment deleted successfully."}
