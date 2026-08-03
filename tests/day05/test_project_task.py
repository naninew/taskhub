# [Ngày 5] Pytest — Project & Task CRUD end-to-end

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
async def test_project_task_full_flow(client):
    """Luồng đầy đủ: tạo project → task → assign sai → assign đúng → status → archive."""
    owner_payload = {
        "email": "day05-owner@example.com",
        "full_name": "Day05 Owner",
        "password": "Secret123!",
    }
    editor_payload = {
        "email": "day05-editor@example.com",
        "full_name": "Day05 Editor",
        "password": "Secret123!",
    }
    outsider_payload = {
        "email": "day05-outsider@example.com",
        "full_name": "Day05 Outsider",
        "password": "Secret123!",
    }

    token_owner = await _register_and_login(client, owner_payload)
    token_editor = await _register_and_login(client, editor_payload)
    await _register_and_login(client, outsider_payload)

    owner_me = await client.get("/api/v1/users/me", headers=_auth_header(token_owner))
    editor_me = await client.get("/api/v1/users/me", headers=_auth_header(token_editor))
    owner_id = owner_me.json()["id"]
    editor_id = editor_me.json()["id"]

    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Day05 Workspace"},
        headers=_auth_header(token_owner),
    )
    assert ws_res.status_code == 201
    workspace_id = ws_res.json()["id"]

    invite_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": editor_payload["email"], "role": "EDITOR"},
        headers=_auth_header(token_owner),
    )
    assert invite_res.status_code == 201

    project_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Sprint Alpha", "description": "First sprint"},
        headers=_auth_header(token_owner),
    )
    assert project_res.status_code == 201
    project = project_res.json()
    assert project["name"] == "Sprint Alpha"
    assert project["status"] == "ACTIVE"
    assert project["workspace_id"] == workspace_id
    project_id = project["id"]

    task_res = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Implement login", "description": "JWT auth flow"},
        headers=_auth_header(token_editor),
    )
    assert task_res.status_code == 201
    task = task_res.json()
    assert task["title"] == "Implement login"
    assert task["status"] == "TODO"
    assert task["priority"] == "MEDIUM"
    assert task["project_id"] == project_id
    assert task["created_by"] == editor_id
    task_id = task["id"]

    outsider_me = await client.get(
        "/api/v1/users/me",
        headers=_auth_header(await _register_and_login(client, {
            "email": "day05-outsider2@example.com",
            "full_name": "Outsider2",
            "password": "Secret123!",
        })),
    )
    outsider_id = outsider_me.json()["id"]

    bad_assign = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"assignee_id": outsider_id},
        headers=_auth_header(token_editor),
    )
    assert bad_assign.status_code == 409
    assert bad_assign.json()["code"] == "CONFLICT"
    assert "member" in bad_assign.json()["message"].lower()

    good_assign = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"assignee_id": owner_id},
        headers=_auth_header(token_editor),
    )
    assert good_assign.status_code == 200
    assert good_assign.json()["assignee_id"] == owner_id

    todo_to_progress = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "IN_PROGRESS"},
        headers=_auth_header(token_editor),
    )
    assert todo_to_progress.status_code == 200
    assert todo_to_progress.json()["status"] == "IN_PROGRESS"

    to_review = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "IN_REVIEW"},
        headers=_auth_header(token_editor),
    )
    assert to_review.status_code == 200
    assert to_review.json()["status"] == "IN_REVIEW"

    to_done = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "DONE"},
        headers=_auth_header(token_editor),
    )
    assert to_done.status_code == 200
    assert to_done.json()["status"] == "DONE"

    invalid_transition = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "TODO"},
        headers=_auth_header(token_editor),
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["code"] == "CONFLICT"
    assert "transition" in invalid_transition.json()["message"].lower()

    archive_res = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/archive",
        headers=_auth_header(token_owner),
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "ARCHIVED"

    list_default = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=_auth_header(token_owner),
    )
    assert list_default.status_code == 200
    assert all(p["status"] == "ACTIVE" for p in list_default.json())
    assert project_id not in [p["id"] for p in list_default.json()]

    list_with_archived = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects?include_archived=true",
        headers=_auth_header(token_owner),
    )
    assert list_with_archived.status_code == 200
    archived_ids = [p["id"] for p in list_with_archived.json()]
    assert project_id in archived_ids

    get_archived = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=_auth_header(token_owner),
    )
    assert get_archived.status_code == 200
    assert get_archived.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_viewer_cannot_create_project(client):
    """VIEWER không được tạo project — trả 403."""
    owner_token = await _register_and_login(client, {
        "email": "day05-v-owner@example.com",
        "full_name": "Viewer Test Owner",
        "password": "Secret123!",
    })
    viewer_token = await _register_and_login(client, {
        "email": "day05-v-viewer@example.com",
        "full_name": "Viewer Test Viewer",
        "password": "Secret123!",
    })

    ws = await client.post(
        "/api/v1/workspaces",
        json={"name": "Viewer RBAC WS"},
        headers=_auth_header(owner_token),
    )
    workspace_id = ws.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": "day05-v-viewer@example.com", "role": "VIEWER"},
        headers=_auth_header(owner_token),
    )

    forbidden = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Blocked Project"},
        headers=_auth_header(viewer_token),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_update_task_priority_and_due_date(client):
    """Cập nhật priority và due_date qua PATCH /tasks/{id}."""
    token = await _register_and_login(client, {
        "email": "day05-priority@example.com",
        "full_name": "Priority User",
        "password": "Secret123!",
    })

    ws = await client.post(
        "/api/v1/workspaces",
        json={"name": "Priority WS"},
        headers=_auth_header(token),
    )
    workspace_id = ws.json()["id"]

    project = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Priority Project"},
        headers=_auth_header(token),
    )
    project_id = project.json()["id"]

    task = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Set priority"},
        headers=_auth_header(token),
    )
    task_id = task.json()["id"]

    updated = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"priority": "HIGH", "due_date": "2026-12-31"},
        headers=_auth_header(token),
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["priority"] == "HIGH"
    assert body["due_date"] == "2026-12-31"


@pytest.mark.asyncio
async def test_delete_task(client):
    """DELETE /tasks/{id} xoá task thành công."""
    token = await _register_and_login(client, {
        "email": "day05-delete@example.com",
        "full_name": "Delete User",
        "password": "Secret123!",
    })

    ws = await client.post(
        "/api/v1/workspaces",
        json={"name": "Delete WS"},
        headers=_auth_header(token),
    )
    workspace_id = ws.json()["id"]

    project = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Delete Project"},
        headers=_auth_header(token),
    )
    project_id = project.json()["id"]

    task = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "To be deleted"},
        headers=_auth_header(token),
    )
    task_id = task.json()["id"]

    delete_res = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(token),
    )
    assert delete_res.status_code == 200

    list_res = await client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=_auth_header(token),
    )
    assert list_res.status_code == 200
    assert all(t["id"] != task_id for t in list_res.json())
