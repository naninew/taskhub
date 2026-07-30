# [Ngày 1] API Endpoints CRUD cho resource Label
# [Ngày 2] Cập nhật: truyền db session vào service (AsyncSession thật)

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_label_service
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate
from app.services.label_service import LabelService

router = APIRouter()


@router.post(
    "/projects/{project_id}/labels",
    response_model=LabelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo label mới cho project",
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
