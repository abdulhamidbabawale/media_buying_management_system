import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_rate_limiter():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First request should succeed
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API is running 🚀"}



@pytest.mark.asyncio
async def test_rate_limiter():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API is running 🚀"}


import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

@pytest.mark.asyncio
async def test_rate_limiter():
    # Manually initialize redis before running the test
    r = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First request should succeed
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API is running 🚀"}

        # Hit the rate limit (101 requests, since limit is 100 per minute)
        for _ in range(100):
            await ac.get("/")

        # The next request should be blocked
        response = await ac.get("/")
        assert response.status_code == 429
        assert "Too Many Requests" in response.text
