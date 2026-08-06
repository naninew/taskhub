# [Ngày 1] API Endpoints CRUD cho resource Label
# [Ngày 2] Cập nhật: truyền db session vào service (AsyncSession thật)
# [Ngày 6] NÂNG CẤP từ Ngày 5: thêm POST/DELETE /tasks/{task_id}/labels/{label_id} để gán/bỏ label khỏi task

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUserDep, get_db, get_label_service
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate
from app.services.label_service import LabelService

router = APIRouter()


@router.post(
    "/projects/{project_id}/labels",
    response_model=LabelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo label mới cho project",
    description="Tạo một Label mới thuộc dự án.",
    responses={
        400: {"description": "Label cùng tên đã tồn tại trong project"},
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
    },
)
async def create_label(
    project_id: int,
    label_in: LabelCreate,
    service: LabelService = Depends(get_label_service),
    db: AsyncSession = Depends(get_db),
) -> LabelRead:
    """Tạo mới một Label thuộc project_id cụ thể."""
    return await service.create_label(db=db, project_id=project_id, label_in=label_in)


@router.get(
    "/projects/{project_id}/labels",
    response_model=list[LabelRead],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách label của project",
    description="Lấy tất cả các nhãn (Label) đã tạo trong dự án.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
    },
)
async def list_labels(
    project_id: int,
    service: LabelService = Depends(get_label_service),
    db: AsyncSession = Depends(get_db),
) -> list[LabelRead]:
    """Lấy danh sách tất cả các Label của project_id."""
    return await service.list_labels(db=db, project_id=project_id)


@router.get(
    "/projects/{project_id}/labels/{label_id}",
    response_model=LabelRead,
    status_code=status.HTTP_200_OK,
    summary="Lấy chi tiết label",
    description="Lấy chi tiết thông tin một Label.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        404: {"description": "Label không tồn tại trong project"},
    },
)
async def get_label(
    project_id: int,
    label_id: int,
    service: LabelService = Depends(get_label_service),
    db: AsyncSession = Depends(get_db),
) -> LabelRead:
    """Lấy thông tin chi tiết của một Label theo label_id."""
    return await service.get_label(db=db, project_id=project_id, label_id=label_id)


@router.patch(
    "/projects/{project_id}/labels/{label_id}",
    response_model=LabelRead,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật label",
    description="Cập nhật tên hoặc màu sắc của Label.",
    responses={
        400: {"description": "Tên label mới bị trùng lặp trong project"},
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        404: {"description": "Label không tồn tại"},
    },
)
async def update_label(
    project_id: int,
    label_id: int,
    label_in: LabelUpdate,
    service: LabelService = Depends(get_label_service),
    db: AsyncSession = Depends(get_db),
) -> LabelRead:
    """Cập nhật thông tin Label (tên hoặc màu sắc)."""
    return await service.update_label(
        db=db, project_id=project_id, label_id=label_id, label_in=label_in
    )


@router.delete(
    "/projects/{project_id}/labels/{label_id}",
    status_code=status.HTTP_200_OK,
    summary="Xoá label",
    description="Xoá một Label khỏi dự án.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        404: {"description": "Label không tồn tại"},
    },
)
async def delete_label(
    project_id: int,
    label_id: int,
    service: LabelService = Depends(get_label_service),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Xoá một Label khỏi project."""
    await service.delete_label(db=db, project_id=project_id, label_id=label_id)
    return {"message": f"Label {label_id} deleted successfully."}


# [Ngày 6] NÂNG CẤP: gán/bỏ label khỏi task
@router.post(
    "/tasks/{task_id}/labels/{label_id}",
    response_model=LabelRead,
    status_code=status.HTTP_200_OK,
    summary="Gán label cho task",
    description="Gán nhãn vào task (Yêu cầu vai trò OWNER hoặc EDITOR trong workspace). Tự động xóa Redis Cache danh sách task.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền (Cần Workspace OWNER hoặc EDITOR)"},
        404: {"description": "Task hoặc Label không tồn tại"},
        409: {"description": "Label không thuộc cùng project với Task"},
    },
)
async def assign_label_to_task(
    task_id: int,
    label_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
    service: LabelService = Depends(get_label_service),
) -> LabelRead:
    """Gán label_id vào task_id (yêu cầu quyền OWNER/EDITOR trong workspace)."""
    return await service.assign_label_to_task(
        db=db, task_id=task_id, label_id=label_id, actor=current_user
    )


@router.delete(
    "/tasks/{task_id}/labels/{label_id}",
    status_code=status.HTTP_200_OK,
    summary="Bỏ label khỏi task",
    description="Gỡ bỏ nhãn khỏi task. Tự động xóa Redis Cache danh sách task.",
    responses={
        401: {"description": "Chưa đăng nhập hoặc token hết hạn"},
        403: {"description": "Không đủ quyền (Cần Workspace OWNER hoặc EDITOR)"},
        404: {"description": "Task hoặc Label không tồn tại"},
    },
)
async def remove_label_from_task(
    task_id: int,
    label_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
    service: LabelService = Depends(get_label_service),
) -> dict[str, str]:
    """Bỏ label_id khỏi task_id (yêu cầu quyền OWNER/EDITOR trong workspace)."""
    await service.remove_label_from_task(
        db=db, task_id=task_id, label_id=label_id, actor=current_user
    )
    return {"message": f"Label {label_id} removed from task {task_id} successfully."}
