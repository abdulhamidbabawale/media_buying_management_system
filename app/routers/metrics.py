from fastapi import APIRouter, HTTPException, Depends, Request, Query
from app.services.performance_service import PerformanceService
from app.middleware import get_current_client_id, verify_client_access
from app.models import PerformanceMetric
from typing import Optional

router = APIRouter(prefix="/metrics", tags=["Performance Metrics"])

# Initialize service
performance_service = PerformanceService()

@router.post("/performance")
async def create_performance_metric(
    metric: PerformanceMetric,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Create a new performance metric record"""
    # Verify client access
    await verify_client_access(client_id, metric.client_id)
    
    result = await performance_service.create_performance_metric_service(metric)
    if result.get("success"):
        return {
            "message": result["message"],
            "metric_id": result["metric_id"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error creating metric: {result['message']}")

@router.get("/campaigns/{campaign_id}")
async def get_campaign_performance(
    campaign_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get performance metrics for a specific campaign"""
    result = await performance_service.get_campaign_performance(campaign_id, days)
    if result.get("success"):
        return {
            "message": "Campaign performance retrieved successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])

@router.get("/skus/{sku_id}")
async def get_sku_performance(
    sku_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get aggregated performance metrics for a SKU"""
    result = await performance_service.get_sku_performance(sku_id, days)
    if result.get("success"):
        return {
            "message": "SKU performance retrieved successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])

@router.get("/clients/{client_id}")
async def get_client_performance(
    client_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    request: Request = None,
    current_client_id: str = Depends(get_current_client_id)
):
    """Get aggregated performance metrics for a client"""
    # Verify client access
    await verify_client_access(current_client_id, client_id)
    
    result = await performance_service.get_client_performance(client_id, days)
    if result.get("success"):
        return {
            "message": "Client performance retrieved successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])

@router.get("/burn-rate/{sku_id}")
async def get_burn_rate_analysis(
    sku_id: str,
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get comprehensive burn rate and pacing analysis for a SKU"""
    result = await performance_service.calculate_burn_rate_metrics(sku_id)
    if result.get("success"):
        return {
            "message": "Burn rate analysis completed successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])

@router.get("/platform-breakdown/{sku_id}")
async def get_platform_breakdown(
    sku_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get performance breakdown by platform for a SKU"""
    result = await performance_service.get_platform_breakdown(sku_id, days)
    if result.get("success"):
        return {
            "message": "Platform breakdown retrieved successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])

@router.get("/mode-breakdown/{sku_id}")
async def get_mode_breakdown(
    sku_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get performance breakdown by intelligence mode (explore/exploit) for a SKU"""
    result = await performance_service.get_mode_breakdown(sku_id, days)
    if result.get("success"):
        return {
            "message": "Mode breakdown retrieved successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])

@router.get("/forecasts/{sku_id}")
async def get_budget_forecast(
    sku_id: str,
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get budget forecasting and recommendations for a SKU"""
    # This endpoint reuses burn rate analysis which includes forecasting
    result = await performance_service.calculate_burn_rate_metrics(sku_id)
    if result.get("success"):
        # Extract forecasting data
        forecast_data = result["data"]["forecasting"]
        health_data = result["data"]["health_status"]
        
        return {
            "message": "Budget forecast generated successfully",
            "data": {
                "sku_id": sku_id,
                "forecast": forecast_data,
                "recommendations": {
                    "daily_adjustment": forecast_data["recommended_daily_adjustment"],
                    "health_status": health_data["budget_health"],
                    "action_required": health_data["budget_health"] in ["critical_overspend", "budget_exhausted"]
                }
            }
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])
