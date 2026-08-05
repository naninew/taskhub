# [Ngày 7] Pytest — Background Task gửi email notification khi assign task

from unittest.mock import patch
import pytest


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
async def test_assign_task_triggers_background_email(client):
    """Test assign task gọi background_tasks.add_task(send_assignment_email, ...)."""
    owner_payload = {
        "email": "day07-owner@example.com",
        "full_name": "Task Owner",
        "password": "Secret123!",
    }
    assignee_payload = {
        "email": "day07-assignee@example.com",
        "full_name": "Task Assignee",
        "password": "Secret123!",
    }

    owner_token = await _register_and_login(client, owner_payload)
    assignee_token = await _register_and_login(client, assignee_payload)

    # Lấy ID của assignee user qua /users/me
    me_res = await client.get("/api/v1/users/me", headers=_auth_header(assignee_token))
    assert me_res.status_code == 200
    assignee_id = me_res.json()["id"]

    # 1. Owner tạo Workspace, Project, Task
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Email WS"},
        headers=_auth_header(owner_token),
    )
    ws_id = ws_res.json()["id"]

    # Mời assignee vào workspace
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": assignee_payload["email"], "role": "EDITOR"},
        headers=_auth_header(owner_token),
    )

    proj_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Email Project"},
        headers=_auth_header(owner_token),
    )
    proj_id = proj_res.json()["id"]

    task_res = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Important Background Task"},
        headers=_auth_header(owner_token),
    )
    task_id = task_res.json()["id"]

    # 2. Patch send_assignment_email để verify được gọi khi assign task
    with patch("app.api.v1.endpoints.tasks.send_assignment_email") as mock_send_email:
        assign_res = await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"assignee_id": assignee_id},
            headers=_auth_header(owner_token),
        )
        assert assign_res.status_code == 200
        assert assign_res.json()["assignee_id"] == assignee_id

        # Verify background task send_assignment_email được gọi với đúng parameter
        mock_send_email.assert_called_once_with(
            user_email=assignee_payload["email"],
            task_title="Important Background Task",
        )
