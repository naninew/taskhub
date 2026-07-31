# [Ngày 4] Pytest — Workspace RBAC end-to-end

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
async def test_create_workspace_creator_is_owner(client):
    """User tạo workspace → owner_id trùng user và có membership OWNER."""
    token = await _register_and_login(client, {
        "email": "creator-owner@example.com",
        "full_name": "Creator Owner",
        "password": "Secret123!",
    })

    me_res = await client.get("/api/v1/users/me", headers=_auth_header(token))
    user_id = me_res.json()["id"]

    create_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Team Alpha"},
        headers=_auth_header(token),
    )
    assert create_res.status_code == 201
    workspace = create_res.json()
    assert workspace["name"] == "Team Alpha"
    assert workspace["owner_id"] == user_id

    get_res = await client.get(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=_auth_header(token),
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == workspace["id"]


@pytest.mark.asyncio
async def test_workspace_rbac_invite_and_remove(client):
    """A (OWNER) tạo workspace → invite B (EDITOR) → B không xoá member → A xoá B."""
    user_a = {
        "email": "rbac-owner-a@example.com",
        "full_name": "RBAC Owner A",
        "password": "Secret123!",
    }
    user_b = {
        "email": "rbac-editor-b@example.com",
        "full_name": "RBAC Editor B",
        "password": "Secret123!",
    }
    token_a = await _register_and_login(client, user_a)
    token_b = await _register_and_login(client, user_b)

    create_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "RBAC Workspace"},
        headers=_auth_header(token_a),
    )
    assert create_res.status_code == 201
    workspace_id = create_res.json()["id"]
    owner_id = create_res.json()["owner_id"]

    invite_res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": user_b["email"], "role": "EDITOR"},
        headers=_auth_header(token_a),
    )
    assert invite_res.status_code == 201
    invited = invite_res.json()
    assert invited["role"] == "EDITOR"
    assert invited["email"] == user_b["email"]

    forbidden_res = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_id}",
        headers=_auth_header(token_b),
    )
    assert forbidden_res.status_code == 403
    err = forbidden_res.json()
    assert err["code"] == "FORBIDDEN"
    assert "message" in err
    assert "detail" in err

    remove_res = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{invited['user_id']}",
        headers=_auth_header(token_a),
    )
    assert remove_res.status_code == 200
    assert remove_res.json()["message"] == "Member removed successfully."


@pytest.mark.asyncio
async def test_cannot_remove_last_owner(client):
    """OWNER duy nhất không thể tự xoá — trả 409 Conflict."""
    token = await _register_and_login(client, {
        "email": "solo-owner@example.com",
        "full_name": "Solo Owner",
        "password": "Secret123!",
    })

    create_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Solo Workspace"},
        headers=_auth_header(token),
    )
    workspace_id = create_res.json()["id"]
    owner_id = create_res.json()["owner_id"]

    conflict_res = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_id}",
        headers=_auth_header(token),
    )
    assert conflict_res.status_code == 409
    err = conflict_res.json()
    assert err["code"] == "CONFLICT"
    assert "last owner" in err["message"].lower() or "last owner" in err["detail"].lower()


@pytest.mark.asyncio
async def test_editor_cannot_invite_member(client):
    """EDITOR không được mời member — trả 403."""
    token_a = await _register_and_login(client, {
        "email": "owner-invite@example.com",
        "full_name": "Owner Invite",
        "password": "Secret123!",
    })
    token_b = await _register_and_login(client, {
        "email": "editor-invite@example.com",
        "full_name": "Editor Invite",
        "password": "Secret123!",
    })
    await _register_and_login(client, {
        "email": "viewer-candidate@example.com",
        "full_name": "Viewer Candidate",
        "password": "Secret123!",
    })

    create_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Invite RBAC"},
        headers=_auth_header(token_a),
    )
    workspace_id = create_res.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": "editor-invite@example.com", "role": "EDITOR"},
        headers=_auth_header(token_a),
    )

    forbidden = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"email": "viewer-candidate@example.com", "role": "VIEWER"},
        headers=_auth_header(token_b),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "FORBIDDEN"
