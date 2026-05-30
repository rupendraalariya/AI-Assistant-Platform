"""API tests for health endpoint."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns healthy status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_check_contains_service_info(client: AsyncClient):
    """Test health check includes service metadata."""
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["service"] == "LLM Chatbot Assistant"
    assert "environment" in data
