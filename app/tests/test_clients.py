import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_client():
    async with AsyncClient(transport=ASGITransport(app=app, lifespan="on"), base_url="http://test") as ac:
        # Register an admin user and login to get token
        admin_user = {
            "email": "admin_client_test@example.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "status": "active"
        }
        await ac.post("/api/v1/auth/register", json=admin_user)
        login_resp = await ac.post("/api/v1/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"]
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await ac.post(
            "/api/v1/clients/",
            json={
                "name": "johnny3",
                "industry": "driving",
                "settings": {},
                "api_keys_refs": {}
            },
            headers=headers,
        )
        assert response.status_code == 200
