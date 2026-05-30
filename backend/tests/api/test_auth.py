"""API tests for authentication endpoints - local, refresh, logout, Google."""

import pytest
from httpx import AsyncClient

from app.services.auth_service import AuthService


# ============================================================
# REGISTRATION
# ============================================================


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["auth_provider"] == "local"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registration with existing email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "different",
            "password": "securepass123",
        },
    )
    assert response.status_code in (422, 500)


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Test registration with short password fails validation."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "username": "user",
            "password": "short",
        },
    )
    assert response.status_code == 422


# ============================================================
# LOGIN
# ============================================================


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login returns tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code in (401, 500)


# ============================================================
# PROFILE / JWT VALIDATION
# ============================================================


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient, auth_headers):
    """Test getting user profile with valid token."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "auth_provider" in data


@pytest.mark.asyncio
async def test_get_profile_no_auth(client: AsyncClient):
    """Test getting profile without auth fails."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_invalid_token(client: AsyncClient):
    """Test that an invalid JWT is rejected."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


# ============================================================
# TOKEN REFRESH
# ============================================================


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user):
    """Test refreshing tokens with a valid refresh token."""
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient, test_user):
    """Test that using an access token as a refresh token is rejected."""
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    access_token = login.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code in (401, 500)


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Test refresh with an invalid token fails."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "garbage.token.value"},
    )
    assert response.status_code in (401, 500)


# ============================================================
# LOGOUT
# ============================================================


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, auth_headers):
    """Test logout with a valid token."""
    response = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_logout_requires_auth(client: AsyncClient):
    """Test logout without auth fails."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 401


# ============================================================
# GOOGLE OAUTH (service-level, no live Google calls)
# ============================================================


@pytest.mark.asyncio
async def test_google_creates_new_user(db_session):
    """Test Google auth creates a new account on first login."""
    service = AuthService(db_session)
    userinfo = {
        "sub": "google-id-123",
        "email": "googleuser@example.com",
        "name": "Google User",
        "picture": "https://example.com/pic.jpg",
    }
    result = await service.authenticate_google(userinfo)
    await db_session.commit()

    assert "access_token" in result
    user = result["user"]
    assert user.email == "googleuser@example.com"
    assert user.auth_provider == "google"
    assert user.google_id == "google-id-123"
    assert user.hashed_password is None


@pytest.mark.asyncio
async def test_google_links_existing_email(db_session, test_user):
    """Test Google auth links to an existing local account by email."""
    service = AuthService(db_session)
    userinfo = {
        "sub": "google-id-456",
        "email": "test@example.com",  # same as test_user
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
    }
    result = await service.authenticate_google(userinfo)
    await db_session.commit()

    user = result["user"]
    assert user.email == "test@example.com"
    assert user.google_id == "google-id-456"
    assert user.profile_picture == "https://example.com/avatar.jpg"


@pytest.mark.asyncio
async def test_google_returning_user(db_session):
    """Test Google auth logs in an existing Google user by google_id."""
    service = AuthService(db_session)
    userinfo = {
        "sub": "google-id-789",
        "email": "returning@example.com",
        "name": "Returning User",
        "picture": "https://example.com/p.jpg",
    }
    # First login creates
    first = await service.authenticate_google(userinfo)
    await db_session.commit()
    first_id = first["user"].id

    # Second login finds the same user
    second = await service.authenticate_google(userinfo)
    await db_session.commit()
    assert second["user"].id == first_id
