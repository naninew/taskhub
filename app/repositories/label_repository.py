# [Ngày 1] Repository in-memory cho resource Label

from datetime import datetime, timezone
from typing import Optional
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate


class LabelRepository:
    def __init__(self) -> None:
        self._storage: dict[int, LabelRead] = {}
        self._next_id: int = 1

    async def create(self, project_id: int, label_in: LabelCreate) -> LabelRead:
        label_id = self._next_id
        self._next_id += 1
        now = datetime.now(timezone.utc)
        label_read = LabelRead(
            id=label_id,
            project_id=project_id,
            name=label_in.name,
            color=label_in.color,
            created_at=now,
        )
        self._storage[label_id] = label_read
        return label_read

    async def get_by_id(self, label_id: int) -> Optional[LabelRead]:
        return self._storage.get(label_id)

    async def get_by_name_and_project(
        self, name: str, project_id: int
    ) -> Optional[LabelRead]:
        for label in self._storage.values():
            if label.project_id == project_id and label.name.lower() == name.lower():
                return label
        return None

    async def list_by_project(self, project_id: int) -> list[LabelRead]:
        return [
            label for label in self._storage.values() if label.project_id == project_id
        ]

    async def update(
        self, label_id: int, label_in: LabelUpdate
    ) -> Optional[LabelRead]:
        existing = self._storage.get(label_id)
        if not existing:
            return None

        updated_data = existing.model_dump()
        if label_in.name is not None:
            updated_data["name"] = label_in.name
        if label_in.color is not None:
            updated_data["color"] = label_in.color

        updated_label = LabelRead(**updated_data)
        self._storage[label_id] = updated_label
        return updated_label

    async def delete(self, label_id: int) -> bool:
        if label_id in self._storage:
            del self._storage[label_id]
            return True
        return False


# Singleton instance dùng tạm cho Ngày 1 in-memory storage
label_repository = LabelRepository()
