import pytest
from datetime import datetime, timedelta
from app.intelligence.sku_intelligence import SKUIntelligence
from app.intelligence.config import MVP_CONFIG
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_sku_intelligence_initialization():
    """Test SKU intelligence initialization"""
    intelligence = SKUIntelligence()
    assert intelligence.config == MVP_CONFIG
    
    custom_config = {"min_campaign_budget": 200}
    intelligence = SKUIntelligence(custom_config)
    assert intelligence.config["min_campaign_budget"] == 200

@pytest.mark.asyncio
async def test_mode_determination():
    """Test EXPLORE vs EXPLOIT mode determination"""
    intelligence = SKUIntelligence()
    
    # Test new campaign (should be explore)
    performance_new = {
        "days_running": 3,
        "confidence_score": 0.3,
        "total_impressions": 500,
        "avg_roas": 1.5
    }
    mode = await intelligence.determine_mode("test-sku", performance_new)
    assert mode == "explore"
    
    # Test mature campaign with high confidence and good ROAS (should be exploit)
    performance_mature = {
        "days_running": 10,
        "confidence_score": 0.9,
        "total_impressions": 5000,
        "avg_roas": 3.5
    }
    mode = await intelligence.determine_mode("test-sku", performance_mature)
    assert mode == "exploit"
    
    # Test low impressions (should be explore)
    performance_low_impressions = {
        "days_running": 10,
        "confidence_score": 0.9,
        "total_impressions": 500,  # Below threshold
        "avg_roas": 3.5
    }
    mode = await intelligence.determine_mode("test-sku", performance_low_impressions)
    assert mode == "explore"

@pytest.mark.asyncio
async def test_explore_mode_decisions():
    """Test explore mode decision making"""
    intelligence = SKUIntelligence()
    
    # Mock campaigns data
    campaigns = [
        {"_id": "campaign1", "budget_allocated": 1000, "status": "active"},
        {"_id": "campaign2", "budget_allocated": 800, "status": "active"},
        {"_id": "campaign3", "budget_allocated": 1200, "status": "active"}
    ]
    
    # Mock performance data with campaign performance
    performance = {
        "campaigns": {
            "campaign1": {"roas": 1.2},  # Lowest performing
            "campaign2": {"roas": 2.1},  # Medium performing
            "campaign3": {"roas": 3.5}   # Highest performing
        }
    }
    
    with patch('app.intelligence.sku_intelligence.get_campaigns_by_sku', return_value=campaigns):
        decisions = await intelligence.explore_mode_decisions("test-sku", performance)
        
        # Should have decisions for underperforming campaigns
        assert len(decisions) > 0
        
        # Check that decisions are for budget allocation
        for decision in decisions:
            assert decision["type"] == "budget_allocation"
            assert "campaign_id" in decision
            assert "old_budget" in decision
            assert "new_budget" in decision
            assert "reason" in decision

@pytest.mark.asyncio
async def test_exploit_mode_decisions():
    """Test exploit mode decision making"""
    intelligence = SKUIntelligence()
    
    # Mock campaigns data
    campaigns = [
        {"_id": "campaign1", "budget_allocated": 1000, "status": "active"},
        {"_id": "campaign2", "budget_allocated": 800, "status": "active"}
    ]
    
    # Mock performance data
    performance = {
        "campaigns": {
            "campaign1": {"roas": 4.0},  # High performing
            "campaign2": {"roas": 1.0}   # Low performing
        }
    }
    
    with patch('app.intelligence.sku_intelligence.get_campaigns_by_sku', return_value=campaigns):
        decisions = await intelligence.exploit_mode_decisions("test-sku", performance)
        
        # Should have decisions for budget adjustments
        assert len(decisions) > 0
        
        # Check decision types
        for decision in decisions:
            assert decision["type"] == "budget_allocation"
            assert "reason" in decision
            # High ROAS campaigns should get budget increases
            # Low ROAS campaigns should get budget decreases

@pytest.mark.asyncio
async def test_sku_performance_aggregation():
    """Test SKU performance data aggregation"""
    intelligence = SKUIntelligence()
    
    # Mock performance collection data
    mock_performance_data = [
        {
            "_id": "campaign1",
            "total_spend": 1000,
            "total_impressions": 10000,
            "total_clicks": 500,
            "total_conversions": 50,
            "avg_roas": 2.5,
            "data_points": 7
        },
        {
            "_id": "campaign2", 
            "total_spend": 800,
            "total_impressions": 8000,
            "total_clicks": 400,
            "total_conversions": 40,
            "avg_roas": 2.0,
            "data_points": 7
        }
    ]
    
    with patch('app.intelligence.sku_intelligence.get_campaigns_by_sku', return_value=[{"_id": "campaign1"}, {"_id": "campaign2"}]):
        with patch.object(intelligence.performance_collection, 'aggregate', return_value=AsyncMock(to_list=AsyncMock(return_value=mock_performance_data))):
            performance = await intelligence.get_sku_performance("test-sku")
            
            assert performance["total_spend"] == 1800  # 1000 + 800
            assert performance["total_impressions"] == 18000  # 10000 + 8000
            assert performance["total_conversions"] == 90  # 50 + 40
            assert performance["avg_roas"] == (90 / 1800)  # conversions / spend
            assert performance["confidence_score"] > 0  # Based on data points

@pytest.mark.asyncio
async def test_decision_execution():
    """Test decision execution"""
    intelligence = SKUIntelligence()
    
    decisions = [
        {
            "type": "budget_allocation",
            "campaign_id": "test-campaign",
            "new_budget": 1500.0
        }
    ]
    
    with patch('app.intelligence.sku_intelligence.update_campaign_budget', return_value=True):
        results = await intelligence.execute_decisions(decisions)
        
        assert len(results) == 1
        assert results[0]["success"] == True
        assert results[0]["message"] == "Budget updated successfully"

@pytest.mark.asyncio
async def test_decision_logging():
    """Test decision logging"""
    intelligence = SKUIntelligence()
    
    decisions = [{"type": "budget_allocation", "campaign_id": "test-campaign"}]
    execution_results = [{"success": True, "message": "Updated"}]
    
    with patch.object(intelligence.decisions_collection, 'insert_one', return_value=AsyncMock()):
        await intelligence.log_decisions("test-sku", "test-client", decisions, "explore", execution_results)
        
        # If no exception is raised, logging was successful
        assert True

@pytest.mark.asyncio
async def test_make_hourly_decisions_integration():
    """Test the main hourly decisions process"""
    intelligence = SKUIntelligence()
    
    # Mock all dependencies
    with patch('app.intelligence.sku_intelligence.get_sku_by_id', return_value={"_id": "test-sku", "client_id": "test-client"}):
        with patch.object(intelligence, 'get_sku_performance', return_value={
            "days_running": 5,
            "confidence_score": 0.6,
            "total_impressions": 2000,
            "avg_roas": 2.0,
            "campaigns": {}
        }):
            with patch.object(intelligence, 'execute_decisions', return_value=[{"success": True}]):
                with patch.object(intelligence, 'log_decisions', return_value=None):
                    result = await intelligence.make_hourly_decisions("test-sku")
                    
                    assert result["success"] == True
                    assert "mode" in result
                    assert "decisions" in result
                    assert "execution_results" in result
