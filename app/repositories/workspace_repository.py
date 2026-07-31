# [Ngày 4] WorkspaceRepository kế thừa BaseRepository[Workspace]

from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self) -> None:
        super().__init__(Workspace)


workspace_repository = WorkspaceRepository()
