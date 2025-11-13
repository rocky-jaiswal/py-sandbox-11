"""Basic API tests to verify setup."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_validation_error(client: TestClient) -> None:
    """Test validation error response (422)."""
    response = client.post(
        "/api/v1/users",
        json={
            "email": "invalid-email",  # Invalid email format
            "username": "test",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["status_code"] == 422
    assert data["error"]["type"] == "client_error"


def test_not_found_error(client: TestClient) -> None:
    """Test not found error response (404)."""
    response = client.get("/api/v1/users/99999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["status_code"] == 404
    assert data["error"]["type"] == "client_error"
