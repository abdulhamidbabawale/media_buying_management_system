import pytest
from httpx import AsyncClient
from app.main import app
from app.models import Campaign
from app.services.campaign_service import create_campaign_service, get_campaign_by_id_service
from datetime import datetime

@pytest.mark.asyncio
async def test_campaign_creation():
    """Test campaign creation service"""
    campaign_data = Campaign(
        sku_id="test-sku-123",
        client_id="test-client-123",
        platform="google_ads",
        campaign_name="Test Campaign",
        budget_allocated=1000.0,
        target_groups=[{"age": "25-34", "location": "US"}],
        creatives=[{"type": "image", "url": "https://example.com/image.jpg"}],
        status="active"
    )
    
    result = await create_campaign_service(campaign_data)
    assert result["success"] == True
    assert "campaign_id" in result
    assert result["message"] == "Campaign Created Successfully"

@pytest.mark.asyncio
async def test_campaign_endpoints():
    """Test campaign API endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First, create a test user and get auth token
        user_data = {
            "email": "campaigntest@example.com",
            "password": "testpassword123",
            "first_name": "Campaign",
            "last_name": "Test",
            "role": "analyst",
            "status": "active"
        }
        
        await ac.post("/api/v1/auth/register", json=user_data)
        
        login_response = await ac.post("/api/v1/auth/login", json={
            "email": "campaigntest@example.com",
            "password": "testpassword123"
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test campaign creation
        campaign_data = {
            "sku_id": "test-sku-123",
            "client_id": "test-client-123",
            "platform": "google_ads",
            "campaign_name": "Test Campaign",
            "budget_allocated": 1000.0,
            "target_groups": [{"age": "25-34", "location": "US"}],
            "creatives": [{"type": "image", "url": "https://example.com/image.jpg"}]
        }
        
        response = await ac.post("/api/v1/campaigns/", json=campaign_data, headers=headers)
        assert response.status_code == 200
        assert "campaign_id" in response.json()
        
        campaign_id = response.json()["campaign_id"]
        
        # Test getting campaigns
        response = await ac.get("/api/v1/campaigns/", headers=headers)
        assert response.status_code == 200
        assert "data" in response.json()
        
        # Test getting specific campaign
        response = await ac.get(f"/api/v1/campaigns/{campaign_id}", headers=headers)
        assert response.status_code == 200
        assert "data" in response.json()
        
        # Test campaign update
        update_data = {
            "campaign_name": "Updated Campaign Name",
            "budget_allocated": 1500.0
        }
        
        response = await ac.put(f"/api/v1/campaigns/{campaign_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        # Test campaign pause
        response = await ac.post(f"/api/v1/campaigns/{campaign_id}/pause", headers=headers)
        assert response.status_code == 200
        
        # Test campaign activation
        response = await ac.post(f"/api/v1/campaigns/{campaign_id}/activate", headers=headers)
        assert response.status_code == 200
        
        # Test budget update
        budget_data = {"new_budget": 2000.0}
        response = await ac.put(f"/api/v1/campaigns/{campaign_id}/budget", json=budget_data, headers=headers)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_campaign_unauthorized_access():
    """Test campaign endpoints without authentication"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test without auth headers
        response = await ac.get("/api/v1/campaigns/")
        assert response.status_code == 401
        
        response = await ac.post("/api/v1/campaigns/", json={})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_campaign_validation():
    """Test campaign data validation"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create test user and get token
        user_data = {
            "email": "validationtest@example.com",
            "password": "testpassword123",
            "first_name": "Validation",
            "last_name": "Test",
            "role": "analyst",
            "status": "active"
        }
        
        await ac.post("/api/v1/auth/register", json=user_data)
        
        login_response = await ac.post("/api/v1/auth/login", json={
            "email": "validationtest@example.com",
            "password": "testpassword123"
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with invalid campaign data
        invalid_campaign = {
            "sku_id": "",  # Empty SKU ID
            "client_id": "test-client-123",
            "platform": "invalid_platform",
            "campaign_name": "",
            "budget_allocated": -100  # Negative budget
        }
        
        response = await ac.post("/api/v1/campaigns/", json=invalid_campaign, headers=headers)
        # Should return validation error
        assert response.status_code in [400, 422]
