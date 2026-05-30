"""API tests for session endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, auth_headers):
    """Test creating a new session."""
    response = await client.post(
        "/api/v1/sessions",
        json={"title": "Test Session", "model": "gpt-4o-mini"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Session"
    assert data["model"] == "gpt-4o-mini"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sessions_empty(client: AsyncClient, auth_headers):
    """Test listing sessions when none exist."""
    response = await client.get("/api/v1/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["sessions"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, auth_headers, test_user, db_session):
    """Test listing sessions after creating one."""
    # Create a session directly
    session = Session(user_id=test_user.id, title="My Session")
    db_session.add(session)
    await db_session.commit()

    response = await client.get("/api/v1/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient, auth_headers, test_user, db_session):
    """Test deleting a session."""
    session = Session(user_id=test_user.id, title="To Delete")
    db_session.add(session)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/sessions/{session.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_session(client: AsyncClient, auth_headers):
    """Test deleting a session that doesn't exist."""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/v1/sessions/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_session_requires_auth(client: AsyncClient):
    """Test that session endpoints require authentication."""
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 401
