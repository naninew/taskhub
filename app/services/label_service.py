# [Ngày 1] Service xử lý business logic cho resource Label

from typing import Optional
from fastapi import HTTPException, status

from app.repositories.label_repository import LabelRepository
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate


class LabelService:
    def __init__(self, repo: LabelRepository) -> None:
        self.repo = repo

    async def create_label(self, project_id: int, label_in: LabelCreate) -> LabelRead:
        existing = await self.repo.get_by_name_and_project(
            name=label_in.name, project_id=project_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label with name '{label_in.name}' already exists in project {project_id}.",
            )
        return await self.repo.create(project_id=project_id, label_in=label_in)

    async def get_label(self, project_id: int, label_id: int) -> LabelRead:
        label = await self.repo.get_by_id(label_id)
        if not label or label.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in project {project_id}.",
            )
        return label

    async def list_labels(self, project_id: int) -> list[LabelRead]:
        return await self.repo.list_by_project(project_id=project_id)

    async def update_label(
        self, project_id: int, label_id: int, label_in: LabelUpdate
    ) -> LabelRead:
        existing = await self.get_label(project_id=project_id, label_id=label_id)

        if label_in.name is not None and label_in.name.lower() != existing.name.lower():
            duplicate = await self.repo.get_by_name_and_project(
                name=label_in.name, project_id=project_id
            )
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Label with name '{label_in.name}' already exists in project {project_id}.",
                )

        updated = await self.repo.update(label_id=label_id, label_in=label_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in project {project_id}.",
            )
        return updated

    async def delete_label(self, project_id: int, label_id: int) -> bool:
        # Check if exists in project first
        await self.get_label(project_id=project_id, label_id=label_id)
        return await self.repo.delete(label_id=label_id)
