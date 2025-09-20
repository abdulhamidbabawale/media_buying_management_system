import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.jwt import create_access_token, create_refresh_token, verify_token_type, decode_access_token
from app.services.auth_service import register_user, login_user, refresh_access_token
from app.models import User
from app.schemas.auth_schema import LoginRequest, RefreshTokenRequest
from datetime import datetime

@pytest.mark.asyncio
async def test_jwt_token_creation():
    """Test JWT token creation and validation"""
    # Test access token creation
    access_token = create_access_token({"sub": "test@example.com", "user_id": "123"})
    assert access_token is not None
    
    # Test refresh token creation
    refresh_token = create_refresh_token({"sub": "test@example.com", "user_id": "123"})
    assert refresh_token is not None
    
    # Test token decoding
    payload = decode_access_token(access_token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["user_id"] == "123"
    assert payload["type"] == "access"
    
    # Test refresh token validation
    refresh_payload = decode_access_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload["type"] == "refresh"

@pytest.mark.asyncio
async def test_token_type_verification():
    """Test token type verification"""
    access_token = create_access_token({"sub": "test@example.com"})
    refresh_token = create_refresh_token({"sub": "test@example.com"})
    
    assert verify_token_type(access_token, "access") == True
    assert verify_token_type(refresh_token, "refresh") == True
    assert verify_token_type(access_token, "refresh") == False
    assert verify_token_type(refresh_token, "access") == False

@pytest.mark.asyncio
async def test_auth_endpoints():
    """Test authentication endpoints"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test user registration
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": "admin",
            "status": "active"
        }
        
        response = await ac.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        assert "user_id" in response.json()
        
        # Test user login
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = await ac.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Test token refresh
        refresh_data = {
            "refresh_token": data["refresh_token"]
        }
        
        response = await ac.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        refresh_response = response.json()
        assert "access_token" in refresh_response

@pytest.mark.asyncio
async def test_invalid_credentials():
    """Test authentication with invalid credentials"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test invalid login
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await ac.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        #assert "Invalid credentials" in response.json()["detail"]

@pytest.mark.asyncio
async def test_duplicate_registration():
    """Test registration with duplicate email"""
    async with AsyncClient(transport=ASGITransport(app=app, lifespan="on"), base_url="http://test") as ac:
        user_data = {
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": "admin",
            "status": "active"
        }
        
        # First registration should succeed
        response = await ac.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        assert "user_id" in response.json()
        
        # Second registration should fail
        response = await ac.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]

