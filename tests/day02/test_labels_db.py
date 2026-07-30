# [Ngày 2] Pytest suite — DB session, BaseRepository, LabelRepository trên DB thật

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label
from app.repositories.base import BaseRepository
from app.repositories.label_repository import LabelRepository
from app.schemas.label import LabelCreate, LabelUpdate


@pytest.mark.asyncio
async def test_db_session_connects(db_session: AsyncSession):
    """AsyncSession kết nối và thực thi truy vấn cơ bản."""
    from sqlalchemy import text

    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_base_repository_create_and_get_by_id(db_session: AsyncSession):
    """BaseRepository.create và get_by_id hoạt động đúng."""
    repo = BaseRepository(Label)
    created = await repo.create(
        db_session,
        obj_in={"project_id": 10, "name": "db-test", "color": "#123456"},
    )
    assert created.id is not None
    assert created.name == "db-test"

    fetched = await repo.get_by_id(db_session, created.id)
    assert fetched is not None
    assert fetched.name == "db-test"
    assert fetched.project_id == 10


@pytest.mark.asyncio
async def test_base_repository_list_pagination(db_session: AsyncSession):
    """BaseRepository.list hỗ trợ skip/limit."""
    repo = BaseRepository(Label)
    for i in range(5):
        await repo.create(
            db_session,
            obj_in={"project_id": 20, "name": f"pag-{i}", "color": "#aaaaaa"},
        )

    page1 = await repo.list(db_session, skip=0, limit=2)
    page2 = await repo.list(db_session, skip=2, limit=2)
    assert len(page1) == 2
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_base_repository_update(db_session: AsyncSession):
    """BaseRepository.update cập nhật entity."""
    repo = BaseRepository(Label)
    created = await repo.create(
        db_session,
        obj_in={"project_id": 30, "name": "before", "color": "#111111"},
    )
    updated = await repo.update(
        db_session,
        db_obj=created,
        obj_in=LabelUpdate(name="after", color="#222222"),
    )
    assert updated.name == "after"
    assert updated.color == "#222222"


@pytest.mark.asyncio
async def test_base_repository_delete_and_count(db_session: AsyncSession):
    """BaseRepository.delete và count hoạt động đúng."""
    repo = BaseRepository(Label)
    before_count = await repo.count(db_session)

    created = await repo.create(
        db_session,
        obj_in={"project_id": 40, "name": "to-delete", "color": "#000000"},
    )
    assert await repo.count(db_session) == before_count + 1

    deleted = await repo.delete(db_session, id=created.id)
    assert deleted is True
    assert await repo.get_by_id(db_session, created.id) is None


@pytest.mark.asyncio
async def test_label_repository_get_by_name_and_project(db_session: AsyncSession):
    """LabelRepository.get_by_name_and_project tìm theo tên không phân biệt hoa thường."""
    repo = LabelRepository()
    await repo.create_label(
        db_session, project_id=50, label_in=LabelCreate(name="BugFix", color="#ff0000")
    )

    found = await repo.get_by_name_and_project(db_session, name="bugfix", project_id=50)
    assert found is not None
    assert found.name == "BugFix"

    not_found = await repo.get_by_name_and_project(db_session, name="bugfix", project_id=10)
    assert not_found is None


@pytest.mark.asyncio
async def test_label_repository_list_by_project(db_session: AsyncSession):
    """LabelRepository.list_by_project chỉ trả về label thuộc project."""
    repo = LabelRepository()
    await repo.create_label(
        db_session, project_id=10, label_in=LabelCreate(name="p10-a", color="#111111")
    )
    await repo.create_label(
        db_session, project_id=20, label_in=LabelCreate(name="p20-a", color="#222222")
    )

    labels_p10 = await repo.list_by_project(db_session, project_id=10)
    assert all(label.project_id == 10 for label in labels_p10)
    assert any(label.name == "p10-a" for label in labels_p10)


@pytest.mark.asyncio
async def test_label_api_crud_via_client(client):
    """Integration: Label CRUD qua HTTP client trên DB test."""
    create_res = await client.post(
        "/api/v1/projects/10/labels",
        json={"name": "integration-db", "color": "#00ff00"},
    )
    assert create_res.status_code == 201
    label_id = create_res.json()["id"]

    list_res = await client.get("/api/v1/projects/10/labels")
    assert list_res.status_code == 200
    assert any(item["id"] == label_id for item in list_res.json())

    patch_res = await client.patch(
        f"/api/v1/projects/10/labels/{label_id}",
        json={"name": "integration-updated"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "integration-updated"

    del_res = await client.delete(f"/api/v1/projects/10/labels/{label_id}")
    assert del_res.status_code == 200
