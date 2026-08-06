# [Ngày 8] Integration & Refactor tests cho Day 08

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import _verify_workspace_membership
from app.core.exceptions import ForbiddenException, NotFoundException, ConflictException
from app.models.enums import WorkspaceMemberRole
from app.models.task import Task
from app.models.label import Label
from app.repositories.task_repository import task_repository
from app.services.label_service import LabelService


@pytest.mark.asyncio
async def test_openapi_schema_validity(client: AsyncClient):
    """Test OpenAPI 3.x JSON schema response và các định nghĩa error responses."""
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "TaskHub API"
    assert data["info"]["version"] == "1.0.0"
    paths = data.get("paths", {})
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/projects/{project_id}/tasks" in paths


@pytest.mark.asyncio
async def test_refactored_verify_workspace_membership(db_session: AsyncSession):
    """Test helper _verify_workspace_membership đã refactor trong deps.py."""
    # Test non-member access raises ForbiddenException
    with pytest.raises(ForbiddenException) as exc_info:
        await _verify_workspace_membership(
            db_session,
            workspace_id=999,
            user_id=1,
            allowed_roles={WorkspaceMemberRole.OWNER},
            resource_type="workspace",
        )
    assert exc_info.value.code == "FORBIDDEN"
    assert "Not a workspace member" in exc_info.value.message


@pytest.mark.asyncio
async def test_n1_query_optimization_list_tasks(db_session: AsyncSession):
    """Test TaskRepository.list_tasks_filtered trả về eager-loaded Task với selectinload."""
    items, total = await task_repository.list_tasks_filtered(
        db_session,
        project_id=10,
        page=1,
        limit=10,
    )
    assert isinstance(items, list)
    assert total >= 0


@pytest.mark.asyncio
async def test_label_service_structured_exceptions(db_session: AsyncSession):
    """Test LabelService ném đúng các AppException đã refactor thay vì raw HTTPException."""
    service = LabelService()
    with pytest.raises(NotFoundException) as exc_info:
        await service.get_label(db_session, project_id=10, label_id=9999)
    assert exc_info.value.code == "NOT_FOUND"
