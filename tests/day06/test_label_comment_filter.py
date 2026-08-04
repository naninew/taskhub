# [Ngày 6] Pytest — Label, Comment, Filtering & Pagination

import pytest


async def _register_and_login(client, payload: dict) -> str:
    """Helper: đăng ký + login, trả về access_token."""
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
async def test_task_label_assign_and_remove(client):
    """Gán/bỏ label cho task qua POST/DELETE /tasks/{id}/labels/{label_id}."""
    user_payload = {
        "email": "day06-label-owner@example.com",
        "full_name": "Label Owner",
        "password": "Secret123!",
    }
    token = await _register_and_login(client, user_payload)

    # 1. Tạo Workspace & Project
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Label WS"},
        headers=_auth_header(token),
    )
    ws_id = ws_res.json()["id"]

    proj_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Label Project"},
        headers=_auth_header(token),
    )
    proj_id = proj_res.json()["id"]

    # 2. Tạo Task & Label
    task_res = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Label Task"},
        headers=_auth_header(token),
    )
    task_id = task_res.json()["id"]

    label_res = await client.post(
        f"/api/v1/projects/{proj_id}/labels",
        json={"name": "Bug", "color": "#FF0000"},
        headers=_auth_header(token),
    )
    label_id = label_res.json()["id"]

    # 3. Gán label cho task
    assign_res = await client.post(
        f"/api/v1/tasks/{task_id}/labels/{label_id}",
        headers=_auth_header(token),
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["id"] == label_id

    # 4. Bỏ label khỏi task
    remove_res = await client.delete(
        f"/api/v1/tasks/{task_id}/labels/{label_id}",
        headers=_auth_header(token),
    )
    assert remove_res.status_code == 200
    assert "removed" in remove_res.json()["message"].lower()


@pytest.mark.asyncio
async def test_comment_create_and_delete_permissions(client):
    """Thêm/xoá comment: author và workspace OWNER có quyền xoá, user khác bị 403."""
    owner_payload = {
        "email": "day06-owner@example.com",
        "full_name": "Comment Owner",
        "password": "Secret123!",
    }
    author_payload = {
        "email": "day06-author@example.com",
        "full_name": "Comment Author",
        "password": "Secret123!",
    }
    other_payload = {
        "email": "day06-other@example.com",
        "full_name": "Comment Other",
        "password": "Secret123!",
    }

    owner_token = await _register_and_login(client, owner_payload)
    author_token = await _register_and_login(client, author_payload)
    other_token = await _register_and_login(client, other_payload)

    # 1. Owner tạo Workspace, Project, Task
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Comment WS"},
        headers=_auth_header(owner_token),
    )
    ws_id = ws_res.json()["id"]

    # Mời author và other vào workspace (EDITOR & VIEWER)
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": author_payload["email"], "role": "EDITOR"},
        headers=_auth_header(owner_token),
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": other_payload["email"], "role": "VIEWER"},
        headers=_auth_header(owner_token),
    )

    proj_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Comment Project"},
        headers=_auth_header(owner_token),
    )
    proj_id = proj_res.json()["id"]

    task_res = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task with comments"},
        headers=_auth_header(owner_token),
    )
    task_id = task_res.json()["id"]

    # 2. Author thêm comment
    c1_res = await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "Author comment content"},
        headers=_auth_header(author_token),
    )
    assert c1_res.status_code == 201
    c1_id = c1_res.json()["id"]

    # 3. User 'other' (không phải author, không phải OWNER) thử xoá -> 403 Forbidden
    del_forbidden = await client.delete(
        f"/api/v1/comments/{c1_id}",
        headers=_auth_header(other_token),
    )
    assert del_forbidden.status_code == 403

    # 4. Author tự xoá comment của mình -> 200 OK
    del_author = await client.delete(
        f"/api/v1/comments/{c1_id}",
        headers=_auth_header(author_token),
    )
    assert del_author.status_code == 200

    # 5. Author tạo comment khác, Owner xoá comment này -> 200 OK
    c2_res = await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "Second comment by author"},
        headers=_auth_header(author_token),
    )
    assert c2_res.status_code == 201
    c2_id = c2_res.json()["id"]

    del_owner = await client.delete(
        f"/api/v1/comments/{c2_id}",
        headers=_auth_header(owner_token),
    )
    assert del_owner.status_code == 200


@pytest.mark.asyncio
async def test_task_filtering_and_pagination(client):
    """Nâng cấp GET /projects/{id}/tasks: filter status/priority và pagination total/page/limit."""
    user_payload = {
        "email": "day06-filter-user@example.com",
        "full_name": "Filter User",
        "password": "Secret123!",
    }
    token = await _register_and_login(client, user_payload)

    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Filter WS"},
        headers=_auth_header(token),
    )
    ws_id = ws_res.json()["id"]

    proj_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Filter Project"},
        headers=_auth_header(token),
    )
    proj_id = proj_res.json()["id"]

    # Tạo 5 tasks với status và priority khác nhau:
    # Task 1: TODO, HIGH
    # Task 2: TODO, HIGH
    # Task 3: TODO, LOW
    # Task 4: IN_PROGRESS, HIGH
    # Task 5: IN_PROGRESS, LOW
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task 1", "priority": "HIGH"},
        headers=_auth_header(token),
    )
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task 2", "priority": "HIGH"},
        headers=_auth_header(token),
    )
    t3 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task 3", "priority": "LOW"},
        headers=_auth_header(token),
    )
    t4 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task 4", "priority": "HIGH"},
        headers=_auth_header(token),
    )
    t4_id = t4.json()["id"]
    await client.patch(
        f"/api/v1/tasks/{t4_id}",
        json={"status": "IN_PROGRESS"},
        headers=_auth_header(token),
    )

    t5 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task 5", "priority": "LOW"},
        headers=_auth_header(token),
    )
    t5_id = t5.json()["id"]
    await client.patch(
        f"/api/v1/tasks/{t5_id}",
        json={"status": "IN_PROGRESS"},
        headers=_auth_header(token),
    )

    # 1. Filter status=TODO & priority=HIGH
    filter_res = await client.get(
        f"/api/v1/projects/{proj_id}/tasks?status=TODO&priority=HIGH&page=1&limit=10",
        headers=_auth_header(token),
    )
    assert filter_res.status_code == 200
    data = filter_res.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["status"] == "TODO"
        assert item["priority"] == "HIGH"

    # 2. Pagination test: page=1, limit=2
    page1_res = await client.get(
        f"/api/v1/projects/{proj_id}/tasks?page=1&limit=2",
        headers=_auth_header(token),
    )
    assert page1_res.status_code == 200
    p1_data = page1_res.json()
    assert p1_data["total"] == 5
    assert p1_data["page"] == 1
    assert p1_data["limit"] == 2
    assert len(p1_data["items"]) == 2

    # 3. Pagination test: page=2, limit=2
    page2_res = await client.get(
        f"/api/v1/projects/{proj_id}/tasks?page=2&limit=2",
        headers=_auth_header(token),
    )
    assert page2_res.status_code == 200
    p2_data = page2_res.json()
    assert p2_data["total"] == 5
    assert p2_data["page"] == 2
    assert p2_data["limit"] == 2
    assert len(p2_data["items"]) == 2
