# [Ngày 7] Pytest — Caching Redis & Cache Invalidation

from unittest.mock import AsyncMock, patch
import pytest


class MockRedis:
    """Mock Redis async client dùng dictionary làm in-memory store cho test suite."""

    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def setex(self, key: str, time: int, value: str):
        self.store[key] = value

    async def scan_iter(self, match: str):
        # Đơn giản hoá wildcard pattern tasks:{project_id}:*
        prefix = match.replace("*", "")
        for key in list(self.store.keys()):
            if key.startswith(prefix):
                yield key

    async def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                count += 1
        return count

    async def ping(self):
        return True

    async def aclose(self):
        pass


async def _register_and_login(client, payload: dict) -> str:
    reg = await client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_cache_hit_and_invalidation_flow(client):
    """Test GET list_tasks lấy từ Cache khi gọi lần 2 và bị invalidate khi tạo/sửa/xoá/gán label."""
    mock_redis = MockRedis()

    with patch("app.db.redis.get_redis", return_value=mock_redis), \
         patch("app.services.task_service.get_redis", return_value=mock_redis):

        user_payload = {
            "email": "day07-cache-user@example.com",
            "full_name": "Cache User",
            "password": "Secret123!",
        }
        token = await _register_and_login(client, user_payload)

        # 1. Tạo Workspace & Project
        ws_res = await client.post(
            "/api/v1/workspaces",
            json={"name": "Cache WS"},
            headers=_auth_header(token),
        )
        ws_id = ws_res.json()["id"]

        proj_res = await client.post(
            f"/api/v1/workspaces/{ws_id}/projects",
            json={"name": "Cache Project"},
            headers=_auth_header(token),
        )
        proj_id = proj_res.json()["id"]

        # 2. Lần 1: Gọi GET list_tasks -> Cache MISS -> query DB -> lưu cache
        res1 = await client.get(
            f"/api/v1/projects/{proj_id}/tasks",
            headers=_auth_header(token),
        )
        assert res1.status_code == 200
        assert res1.json()["total"] == 0
        assert len(mock_redis.store) == 1

        cached_key = list(mock_redis.store.keys())[0]
        assert cached_key.startswith(f"tasks:{proj_id}:")

        # 3. Lần 2: Gọi GET list_tasks -> Cache HIT (kết quả trùng khớp từ MockRedis)
        res2 = await client.get(
            f"/api/v1/projects/{proj_id}/tasks",
            headers=_auth_header(token),
        )
        assert res2.status_code == 200
        assert res2.json()["total"] == 0

        # 4. Tạo task mới -> Invalidate Cache (xóa key khỏi MockRedis)
        create_res = await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"title": "New Task for Cache Test"},
            headers=_auth_header(token),
        )
        assert create_res.status_code == 201
        assert len(mock_redis.store) == 0  # Key đã bị invalidate!

        # 5. Lần 3: Gọi lại GET list_tasks -> Cache MISS -> query DB thấy task mới -> set lại cache
        res3 = await client.get(
            f"/api/v1/projects/{proj_id}/tasks",
            headers=_auth_header(token),
        )
        assert res3.status_code == 200
        assert res3.json()["total"] == 1
        assert res3.json()["items"][0]["title"] == "New Task for Cache Test"
        assert len(mock_redis.store) == 1
