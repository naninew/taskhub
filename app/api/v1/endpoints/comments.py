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
    description="Tạo một bình luận mới trên task (Yêu cầu là thành viên workspace).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Chưa là thành viên của workspace"},
        404: {"description": "Task không tồn tại"},
    },
)
async def create_comment(
    task_id: int,
    data: CommentCreate,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
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
    description="Xoá bình luận (Chỉ tác giả bình luận, hệ thống ADMIN hoặc Workspace OWNER mới có quyền xoá).",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không có quyền xóa bình luận này"},
        404: {"description": "Bình luận không tồn tại"},
    },
)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
    service: CommentService = Depends(get_comment_service),
) -> dict[str, str]:
    """Xoá comment (chỉ tác giả comment hoặc workspace OWNER/ADMIN mới được xoá)."""
    await service.delete_comment(db, comment_id=comment_id, actor=current_user)
    return {"message": "Comment deleted successfully."}
