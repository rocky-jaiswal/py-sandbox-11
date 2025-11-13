"""Integration tests for User API with real PostgreSQL database."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import User


class TestUserIntegration:
    """Integration tests for User CRUD operations with real database."""

    def test_create_user_success(self, client: TestClient) -> None:
        """Test creating a user successfully."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "john@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "john@example.com"
        assert data["username"] == "john_doe"
        assert data["full_name"] == "John Doe"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_user_duplicate_email(self, client: TestClient) -> None:
        """Test creating user with duplicate email returns 409."""
        # Create first user
        client.post(
            "/api/v1/users",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "full_name": "User One",
            },
        )

        # Try to create user with same email
        response = client.post(
            "/api/v1/users",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "full_name": "User Two",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["status_code"] == 409
        assert data["error"]["type"] == "client_error"
        assert "duplicate@example.com" in data["error"]["message"]

    def test_create_user_duplicate_username(self, client: TestClient) -> None:
        """Test creating user with duplicate username returns 409."""
        # Create first user
        client.post(
            "/api/v1/users",
            json={
                "email": "user1@example.com",
                "username": "duplicate_user",
                "full_name": "User One",
            },
        )

        # Try to create user with same username
        response = client.post(
            "/api/v1/users",
            json={
                "email": "user2@example.com",
                "username": "duplicate_user",
                "full_name": "User Two",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert "duplicate_user" in data["error"]["message"]

    def test_create_user_invalid_email(self, client: TestClient) -> None:
        """Test creating user with invalid email returns 422."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["status_code"] == 422
        assert data["error"]["type"] == "client_error"
        assert "validation_errors" in data["error"]["details"]

    def test_create_user_invalid_username(self, client: TestClient) -> None:
        """Test creating user with invalid username returns 422."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "test@example.com",
                "username": "user with spaces!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["type"] == "client_error"

    def test_get_user_success(self, client: TestClient) -> None:
        """Test retrieving a user by ID."""
        # Create user
        create_response = client.post(
            "/api/v1/users",
            json={
                "email": "get@example.com",
                "username": "getuser",
                "full_name": "Get User",
            },
        )
        user_id = create_response.json()["id"]

        # Get user
        response = client.get(f"/api/v1/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "get@example.com"

    def test_get_user_not_found(self, client: TestClient) -> None:
        """Test getting non-existent user returns 404."""
        response = client.get("/api/v1/users/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["status_code"] == 404
        assert data["error"]["type"] == "client_error"

    def test_list_users_pagination(self, client: TestClient) -> None:
        """Test listing users with pagination."""
        # Create multiple users
        for i in range(5):
            client.post(
                "/api/v1/users",
                json={
                    "email": f"user{i}@example.com",
                    "username": f"user_{i}",
                    "full_name": f"User {i}",
                },
            )

        # Get first page
        response = client.get("/api/v1/users?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2

        # Get second page
        response = client.get("/api/v1/users?page=2&page_size=2")
        data = response.json()
        assert len(data["users"]) == 2
        assert data["page"] == 2

    def test_update_user_success(self, client: TestClient) -> None:
        """Test updating a user."""
        # Create user
        create_response = client.post(
            "/api/v1/users",
            json={
                "email": "update@example.com",
                "username": "updateuser",
                "full_name": "Original Name",
            },
        )
        user_id = create_response.json()["id"]

        # Update user
        response = client.patch(
            f"/api/v1/users/{user_id}",
            json={"full_name": "Updated Name", "is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["full_name"] == "Updated Name"
        assert data["is_active"] is False
        assert data["email"] == "update@example.com"  # Unchanged

    def test_update_user_duplicate_email(self, client: TestClient) -> None:
        """Test updating user to existing email returns 409."""
        # Create two users
        client.post(
            "/api/v1/users",
            json={
                "email": "user1@example.com",
                "username": "user1",
                "full_name": "User 1",
            },
        )
        create_response = client.post(
            "/api/v1/users",
            json={
                "email": "user2@example.com",
                "username": "user2",
                "full_name": "User 2",
            },
        )
        user2_id = create_response.json()["id"]

        # Try to update user2's email to user1's email
        response = client.patch(
            f"/api/v1/users/{user2_id}",
            json={"email": "user1@example.com"},
        )

        assert response.status_code == 409
        data = response.json()
        assert "already in use" in data["error"]["message"]

    def test_update_user_not_found(self, client: TestClient) -> None:
        """Test updating non-existent user returns 404."""
        response = client.patch(
            "/api/v1/users/99999",
            json={"full_name": "New Name"},
        )

        assert response.status_code == 404

    def test_delete_user_success(self, client: TestClient) -> None:
        """Test deleting a user."""
        # Create user
        create_response = client.post(
            "/api/v1/users",
            json={
                "email": "delete@example.com",
                "username": "deleteuser",
                "full_name": "Delete User",
            },
        )
        user_id = create_response.json()["id"]

        # Delete user
        response = client.delete(f"/api/v1/users/{user_id}")

        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient) -> None:
        """Test deleting non-existent user returns 404."""
        response = client.delete("/api/v1/users/99999")

        assert response.status_code == 404


class TestUserIntegrationAsync:
    """Async integration tests for User API."""

    @pytest.mark.asyncio
    async def test_create_and_verify_in_database(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that created user exists in database."""
        # Create user via API
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "dbtest@example.com",
                "username": "dbtest",
                "full_name": "DB Test User",
            },
        )

        assert response.status_code == 201
        user_id = response.json()["id"]

        # Verify in database
        result = await db_session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.email == "dbtest@example.com"
        assert user.username == "dbtest"
        assert user.full_name == "DB Test User"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, async_client: AsyncClient) -> None:
        """Test concurrent user creation with async client."""
        import asyncio

        async def create_user(index: int) -> int:
            response = await async_client.post(
                "/api/v1/users",
                json={
                    "email": f"concurrent{index}@example.com",
                    "username": f"concurrent_{index}",
                    "full_name": f"Concurrent User {index}",
                },
            )
            return response.status_code

        # Create 10 users concurrently
        results = await asyncio.gather(*[create_user(i) for i in range(10)])

        # All should succeed
        assert all(status == 201 for status in results)

        # Verify all created
        response = await async_client.get("/api/v1/users?page=1&page_size=20")
        data = response.json()
        assert data["total"] >= 10
