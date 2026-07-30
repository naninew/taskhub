# [Ngày 2] Service xử lý business logic cho resource Label với AsyncSession DB thật

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label
from app.repositories.label_repository import LabelRepository
from app.schemas.label import LabelCreate, LabelUpdate


class LabelService:
    def __init__(self, repo: LabelRepository) -> None:
        self.repo = repo

    async def create_label(
        self, db: AsyncSession, project_id: int, label_in: LabelCreate
    ) -> Label:
        existing = await self.repo.get_by_name_and_project(
            db=db, name=label_in.name, project_id=project_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label with name '{label_in.name}' already exists in project {project_id}.",
            )
        return await self.repo.create_label(db=db, project_id=project_id, label_in=label_in)

    async def get_label(
        self, db: AsyncSession, project_id: int, label_id: int
    ) -> Label:
        label = await self.repo.get_by_id(db=db, id=label_id)
        if not label or label.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in project {project_id}.",
            )
        return label

    async def list_labels(self, db: AsyncSession, project_id: int) -> List[Label]:
        return await self.repo.list_by_project(db=db, project_id=project_id)

    async def update_label(
        self, db: AsyncSession, project_id: int, label_id: int, label_in: LabelUpdate
    ) -> Label:
        existing = await self.get_label(db=db, project_id=project_id, label_id=label_id)

        if label_in.name is not None and label_in.name.lower() != existing.name.lower():
            duplicate = await self.repo.get_by_name_and_project(
                db=db, name=label_in.name, project_id=project_id
            )
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Label with name '{label_in.name}' already exists in project {project_id}.",
                )

        updated = await self.repo.update_label(
            db=db, label_id=label_id, label_in=label_in
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in project {project_id}.",
            )
        return updated

    async def delete_label(
        self, db: AsyncSession, project_id: int, label_id: int
    ) -> bool:
        await self.get_label(db=db, project_id=project_id, label_id=label_id)
        return await self.repo.delete_label(db=db, label_id=label_id)
