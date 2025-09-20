import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.performance_service import PerformanceService
from app.models import PerformanceMetric
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_performance_service_initialization():
    """Test performance service initialization"""
    service = PerformanceService()
    assert service is not None

@pytest.mark.asyncio
async def test_create_performance_metric():
    """Test creating performance metrics"""
    service = PerformanceService()
    
    metric = PerformanceMetric(
        campaign_id="test-campaign",
        sku_id="test-sku",
        client_id="test-client",
        spend=100.0,
        impressions=1000,
        clicks=50,
        conversions=5,
        roas=2.5,
        ctr=5.0,
        cpc=2.0,
        platform="google_ads",
        mode="explore"
    )
    
    with patch('app.services.performance_service.create_performance_metric', return_value="metric-id-123"):
        result = await service.create_performance_metric_service(metric)
        
        assert result["success"] == True
        assert result["metric_id"] == "metric-id-123"
        assert "Performance metric created successfully" in result["message"]

@pytest.mark.asyncio
async def test_get_campaign_performance():
    """Test getting campaign performance metrics"""
    service = PerformanceService()
    
    # Mock performance data
    mock_metrics = [
        {
            "spend": 100.0,
            "impressions": 1000,
            "clicks": 50,
            "conversions": 5,
            "roas": 2.5,
            "ctr": 5.0,
            "cpc": 2.0
        },
        {
            "spend": 150.0,
            "impressions": 1500,
            "clicks": 75,
            "conversions": 7,
            "roas": 2.3,
            "ctr": 5.0,
            "cpc": 2.0
        }
    ]
    
    with patch('app.services.performance_service.get_performance_metrics_by_campaign', return_value=mock_metrics):
        result = await service.get_campaign_performance("test-campaign", 7)
        
        assert result["success"] == True
        data = result["data"]
        assert data["total_spend"] == 250.0  # 100 + 150
        assert data["total_impressions"] == 2500  # 1000 + 1500
        assert data["total_clicks"] == 125  # 50 + 75
        assert data["total_conversions"] == 12  # 5 + 7
        assert data["avg_roas"] == (12 / 250)  # conversions / spend
        assert data["data_points"] == 2

@pytest.mark.asyncio
async def test_get_sku_performance():
    """Test getting SKU performance metrics"""
    service = PerformanceService()
    
    # Mock aggregated performance data
    mock_aggregated = {
        "total_spend": 500.0,
        "total_impressions": 5000,
        "total_clicks": 250,
        "total_conversions": 25,
        "avg_roas": 2.0,
        "avg_ctr": 5.0,
        "avg_cpc": 2.0,
        "data_points": 10
    }
    
    with patch('app.services.performance_service.get_performance_metrics_by_sku', return_value=mock_aggregated):
        result = await service.get_sku_performance("test-sku", 7)
        
        assert result["success"] == True
        data = result["data"]
        assert data["total_spend"] == 500.0
        assert data["total_impressions"] == 5000
        assert data["total_clicks"] == 250
        assert data["total_conversions"] == 25
        assert data["avg_roas"] == 2.0

@pytest.mark.asyncio
async def test_calculate_burn_rate_metrics():
    """Test burn rate calculation"""
    service = PerformanceService()
    
    # Mock SKU data
    mock_sku = {
        "_id": "test-sku",
        "total_budget": 10000.0,
        "remaining_budget": 7000.0
    }
    
    # Mock spend data
    mock_hourly_spend = [{"hourly_spend": 50.0}]
    mock_daily_spend = [{"daily_spend": 1000.0}]
    
    with patch('app.services.performance_service.get_sku_by_id', return_value=mock_sku):
        with patch('app.services.performance_service.get_hourly_spend', return_value=mock_hourly_spend):
            with patch('app.services.performance_service.get_daily_spend', return_value=mock_daily_spend):
                result = await service.calculate_burn_rate_metrics("test-sku")
                
                assert result["success"] == True
                data = result["data"]
                
                # Check burn rates
                assert data["burn_rates"]["hourly_burn"] == 50.0
                assert data["burn_rates"]["daily_burn"] == 1000.0
                assert data["burn_rates"]["weekly_burn"] == 1000.0
                
                # Check budget status
                assert data["budget_status"]["total_budget"] == 10000.0
                assert data["budget_status"]["remaining_budget"] == 7000.0
                assert data["budget_status"]["total_spent"] == 3000.0
                assert data["budget_status"]["budget_utilization_percentage"] == 30.0
                
                # Check health status
                assert "budget_health" in data["health_status"]
                assert "status_description" in data["health_status"]

@pytest.mark.asyncio
async def test_pacing_status_determination():
    """Test pacing status determination logic"""
    service = PerformanceService()
    
    # Test optimal pacing
    assert service._determine_pacing_status(2.0) == "optimal"  # 2% variance
    
    # Test under pace
    assert service._determine_pacing_status(-10.0) == "under_pace"  # -10% variance
    
    # Test over pace
    assert service._determine_pacing_status(15.0) == "over_pace"  # 15% variance
    
    # Test critical overspend
    assert service._determine_pacing_status(25.0) == "critical_overspend"  # 25% variance

@pytest.mark.asyncio
async def test_health_description():
    """Test health status descriptions"""
    service = PerformanceService()
    
    assert "optimal" in service._get_health_description("optimal")
    assert "under" in service._get_health_description("under_pace")
    assert "over" in service._get_health_description("over_pace")
    assert "critical" in service._get_health_description("critical_overspend")
    assert "exhausted" in service._get_health_description("budget_exhausted")

@pytest.mark.asyncio
async def test_performance_endpoints():
    """Test performance metrics API endpoints"""
    async with AsyncClient(transport=ASGITransport(app=app, lifespan="on"), base_url="http://test") as ac:
        # Create test user and get auth token
        user_data = {
            "email": "performancetest@example.com",
            "password": "testpassword123",
            "first_name": "Performance",
            "last_name": "Test",
            "role": "analyst",
            "status": "active"
        }
        
        await ac.post("/api/v1/auth/register", json=user_data)
        
        login_response = await ac.post("/api/v1/auth/login", json={
            "email": "performancetest@example.com",
            "password": "testpassword123"
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test creating performance metric
        metric_data = {
            "campaign_id": "test-campaign",
            "sku_id": "test-sku",
            "client_id": "test-client",
            "spend": 100.0,
            "impressions": 1000,
            "clicks": 50,
            "conversions": 5,
            "roas": 2.5,
            "ctr": 5.0,
            "cpc": 2.0,
            "platform": "google_ads",
            "mode": "explore"
        }
        
        response = await ac.post("/api/v1/metrics/performance", json=metric_data, headers=headers)
        assert response.status_code == 200
        assert "metric_id" in response.json()
        
        # Test getting campaign performance
        response = await ac.get("/api/v1/metrics/campaigns/test-campaign?days=7", headers=headers)
        # This might return 404 if no data, which is expected
        assert response.status_code in [200, 404]
        
        # Test getting SKU performance
        response = await ac.get("/api/v1/metrics/skus/test-sku?days=7", headers=headers)
        assert response.status_code in [200, 404]
        
        # Test burn rate analysis
        response = await ac.get("/api/v1/metrics/burn-rate/test-sku", headers=headers)
        assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_performance_endpoints_unauthorized():
    """Test performance endpoints without authentication"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test without auth headers
        response = await ac.get("/api/v1/metrics/campaigns/test-campaign")
        assert response.status_code == 401
        
        response = await ac.post("/api/v1/metrics/performance", json={})
        assert response.status_code == 401

