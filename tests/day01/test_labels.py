# [Ngày 1] Pytest integration test suite cho CRUD resource Label

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_label_success():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/projects/10/labels",
            json={"name": "feature", "color": "#00ff00"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "feature"
        assert data["color"] == "#00ff00"
        assert data["project_id"] == 10
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_create_label_duplicate_name_fails():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Tạo label đầu tiên
        res1 = await client.post(
            "/api/v1/projects/10/labels",
            json={"name": "documentation", "color": "#0000ff"},
        )
        assert res1.status_code == 201

        # Tạo label trùng tên trong cùng project 10
        res2 = await client.post(
            "/api/v1/projects/10/labels",
            json={"name": "documentation", "color": "#111111"},
        )
        assert res2.status_code == 400
        assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_list_labels():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Tạo label cho project 20
        await client.post(
            "/api/v1/projects/20/labels",
            json={"name": "urgent", "color": "#ff0000"},
        )
        response = await client.get("/api/v1/projects/20/labels")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(l["name"] == "urgent" for l in data)


@pytest.mark.asyncio
async def test_get_label_detail():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/api/v1/projects/30/labels",
            json={"name": "refactor", "color": "#ffff00"},
        )
        label_id = created.json()["id"]

        response = await client.get(f"/api/v1/projects/30/labels/{label_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == label_id
        assert data["name"] == "refactor"


@pytest.mark.asyncio
async def test_get_label_not_found():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/projects/30/labels/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_label():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/api/v1/projects/40/labels",
            json={"name": "old_name", "color": "#aaaaaa"},
        )
        label_id = created.json()["id"]

        response = await client.patch(
            f"/api/v1/projects/40/labels/{label_id}",
            json={"name": "new_name", "color": "#bbbbbb"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new_name"
        assert data["color"] == "#bbbbbb"


@pytest.mark.asyncio
async def test_delete_label():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/api/v1/projects/50/labels",
            json={"name": "to_delete", "color": "#000000"},
        )
        label_id = created.json()["id"]

        del_res = await client.delete(f"/api/v1/projects/50/labels/{label_id}")
        assert del_res.status_code == 200

        get_res = await client.get(f"/api/v1/projects/50/labels/{label_id}")
        assert get_res.status_code == 404
