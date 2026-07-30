# [Ngày 3] Pytest integration test — luồng auth end-to-end

import pytest


REGISTER_PAYLOAD = {
    "email": "day03-user@example.com",
    "full_name": "Day 03 User",
    "password": "Secret123!",
}

LOGIN_PAYLOAD = {
    "email": "day03-user@example.com",
    "password": "Secret123!",
}


@pytest.mark.asyncio
async def test_register_success(client):
    """Đăng ký user mới trả về 201 và thông tin user (không có password)."""
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["full_name"] == REGISTER_PAYLOAD["full_name"]
    assert data["is_active"] is True
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client):
    """Đăng ký email trùng phải trả 400."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_returns_token_pair(client):
    """Login trả về access_token + refresh_token."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_fails(client):
    """Login sai mật khẩu phải trả 401."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": LOGIN_PAYLOAD["email"], "password": "WrongPass!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_access_token(client):
    """GET /users/me với Bearer access token trả về profile."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_res = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    access_token = login_res.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["full_name"] == REGISTER_PAYLOAD["full_name"]


@pytest.mark.asyncio
async def test_get_me_without_token_fails(client):
    """GET /users/me không có token phải trả 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    """Refresh token hợp lệ trả về cặp token mới."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_res = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    old_refresh = login_res.json()["refresh_token"]

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["refresh_token"] != old_refresh


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    """Logout → gọi refresh lại với token cũ phải trả 401."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_res = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    refresh_token = login_res.json()["refresh_token"]

    logout_res = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client):
    """PATCH /users/me cập nhật full_name."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_res = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    patch_res = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "Updated Name"

    get_res = await client.get("/api/v1/users/me", headers=headers)
    assert get_res.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_change_password(client):
    """POST /users/me/change-password đổi mật khẩu và login lại được."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_res = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    change_res = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "Secret123!", "new_password": "NewSecret456!"},
        headers=headers,
    )
    assert change_res.status_code == 200

    old_login = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": LOGIN_PAYLOAD["email"], "password": "NewSecret456!"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current_fails(client):
    """Đổi mật khẩu với mật khẩu cũ sai phải trả 400."""
    payload = {
        "email": "wrong-pwd@example.com",
        "full_name": "Wrong Pwd User",
        "password": "Secret123!",
    }
    await client.post("/api/v1/auth/register", json=payload)
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    access_token = login_res.json()["access_token"]

    response = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "WrongOld!", "new_password": "NewSecret456!"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_auth_full_flow_e2e(client):
    """Luồng đầy đủ: register → login → /users/me → refresh → logout → refresh fail."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "e2e@example.com",
        "full_name": "E2E User",
        "password": "E2EPass123!",
    })
    assert reg.status_code == 201

    login = await client.post("/api/v1/auth/login", json={
        "email": "e2e@example.com",
        "password": "E2EPass123!",
    })
    assert login.status_code == 200
    tokens = login.json()

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "e2e@example.com"

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout.status_code == 200

    fail_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert fail_refresh.status_code == 401
