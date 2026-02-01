"""
Integration tests for authentication endpoints.

Tests:
- User registration
- User login with valid credentials
- Login with invalid credentials
- Get current user info
- Delete user account
"""

import pytest
import httpx


pytestmark = pytest.mark.integration


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_new_user(self, sync_api_client: httpx.Client):
        """Test successful user registration."""
        import uuid
        credentials = {
            "username": f"test_reg_{uuid.uuid4().hex[:8]}",
            "password": "StrongPassword123!",
        }
        
        response = sync_api_client.post("/api/auth/register", json=credentials)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == credentials["username"]
        assert "id" in data
        
        # Cleanup: Delete the user
        login_response = sync_api_client.post(
            "/api/auth/token",
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        sync_api_client.delete(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    def test_register_duplicate_username(self, sync_api_client: httpx.Client):
        """Test that registering with an existing username fails."""
        import uuid
        credentials = {
            "username": f"test_dup_{uuid.uuid4().hex[:8]}",
            "password": "StrongPassword123!",
        }
        
        # First registration
        response1 = sync_api_client.post("/api/auth/register", json=credentials)
        assert response1.status_code == 200
        
        # Second registration with same username
        response2 = sync_api_client.post("/api/auth/register", json=credentials)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
        
        # Cleanup
        login_response = sync_api_client.post(
            "/api/auth/token",
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        sync_api_client.delete(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )


class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_valid_credentials(self, sync_api_client: httpx.Client):
        """Test successful login with valid credentials."""
        import uuid
        credentials = {
            "username": f"test_login_{uuid.uuid4().hex[:8]}",
            "password": "StrongPassword123!",
        }
        
        # Register first
        sync_api_client.post("/api/auth/register", json=credentials)
        
        # Login
        response = sync_api_client.post(
            "/api/auth/token",
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Cleanup
        sync_api_client.delete(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
    
    def test_login_invalid_password(self, sync_api_client: httpx.Client):
        """Test login with invalid password fails."""
        import uuid
        credentials = {
            "username": f"test_inv_{uuid.uuid4().hex[:8]}",
            "password": "StrongPassword123!",
        }
        
        # Register first
        sync_api_client.post("/api/auth/register", json=credentials)
        
        # Login with wrong password
        response = sync_api_client.post(
            "/api/auth/token",
            data={
                "username": credentials["username"],
                "password": "WrongPassword123!",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
        
        # Cleanup
        login_response = sync_api_client.post(
            "/api/auth/token",
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        sync_api_client.delete(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    def test_login_nonexistent_user(self, sync_api_client: httpx.Client):
        """Test login with nonexistent username fails."""
        response = sync_api_client.post(
            "/api/auth/token",
            data={
                "username": "nonexistent_user_12345",
                "password": "SomePassword123!",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        assert response.status_code == 401


class TestAuthenticatedEndpoints:
    """Tests for endpoints requiring authentication."""
    
    def test_get_current_user(self, sync_auth_user: httpx.Client):
        """Test getting current user info."""
        response = sync_auth_user.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "created_at" in data
    
    def test_access_without_token(self, sync_api_client: httpx.Client):
        """Test that protected endpoints require authentication."""
        response = sync_api_client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_access_with_invalid_token(self, sync_api_client: httpx.Client):
        """Test that invalid tokens are rejected."""
        response = sync_api_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        
        assert response.status_code == 401
