"""
Performance metrics and burn rate calculation service
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.db.performance_queries import (
    create_performance_metric, get_performance_metrics_by_campaign,
    get_performance_metrics_by_sku, get_performance_metrics_by_client,
    get_hourly_spend, get_daily_spend, get_platform_performance_breakdown,
    get_mode_performance_breakdown
)
from app.db.sku_queries import get_sku_by_id
from app.models import PerformanceMetric
from fastapi.encoders import jsonable_encoder
import logging

logger = logging.getLogger(__name__)

class PerformanceService:
    """Service for performance metrics and burn rate calculations"""
    
    async def create_performance_metric_service(self, metric: PerformanceMetric):
        """Create a new performance metric"""
        metric_dict = jsonable_encoder(metric)
        try:
            result = await create_performance_metric(metric_dict)
            return {
                "success": True,
                "message": "Performance metric created successfully",
                "metric_id": result
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_campaign_performance(self, campaign_id: str, days: int = 7) -> Dict:
        """Get performance metrics for a specific campaign"""
        try:
            metrics = await get_performance_metrics_by_campaign(campaign_id, days)
            if not metrics:
                return {
                    "success": False,
                    "message": "No performance data found for this campaign"
                }
            
            # Calculate aggregated metrics
            total_spend = sum(m["spend"] for m in metrics)
            total_impressions = sum(m["impressions"] for m in metrics)
            total_clicks = sum(m["clicks"] for m in metrics)
            total_conversions = sum(m["conversions"] for m in metrics)
            
            avg_roas = (total_conversions / total_spend) if total_spend > 0 else 0.0
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
            avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
            
            return {
                "success": True,
                "data": {
                    "campaign_id": campaign_id,
                    "period_days": days,
                    "total_spend": total_spend,
                    "total_impressions": total_impressions,
                    "total_clicks": total_clicks,
                    "total_conversions": total_conversions,
                    "avg_roas": avg_roas,
                    "avg_ctr": avg_ctr,
                    "avg_cpc": avg_cpc,
                    "data_points": len(metrics),
                    "hourly_breakdown": metrics
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_sku_performance(self, sku_id: str, days: int = 7) -> Dict:
        """Get aggregated performance metrics for a SKU"""
        try:
            metrics = await get_performance_metrics_by_sku(sku_id, days)
            if not metrics:
                return {
                    "success": False,
                    "message": "No performance data found for this SKU"
                }
            
            return {
                "success": True,
                "data": {
                    "sku_id": sku_id,
                    "period_days": days,
                    "total_spend": metrics["total_spend"],
                    "total_impressions": metrics["total_impressions"],
                    "total_clicks": metrics["total_clicks"],
                    "total_conversions": metrics["total_conversions"],
                    "avg_roas": metrics["avg_roas"],
                    "avg_ctr": metrics["avg_ctr"],
                    "avg_cpc": metrics["avg_cpc"],
                    "data_points": metrics["data_points"]
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_client_performance(self, client_id: str, days: int = 7) -> Dict:
        """Get aggregated performance metrics for a client"""
        try:
            metrics = await get_performance_metrics_by_client(client_id, days)
            if not metrics:
                return {
                    "success": False,
                    "message": "No performance data found for this client"
                }
            
            return {
                "success": True,
                "data": {
                    "client_id": client_id,
                    "period_days": days,
                    "total_spend": metrics["total_spend"],
                    "total_impressions": metrics["total_impressions"],
                    "total_clicks": metrics["total_clicks"],
                    "total_conversions": metrics["total_conversions"],
                    "avg_roas": metrics["avg_roas"],
                    "avg_ctr": metrics["avg_ctr"],
                    "avg_cpc": metrics["avg_cpc"],
                    "data_points": metrics["data_points"]
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def calculate_burn_rate_metrics(self, sku_id: str) -> Dict:
        """Calculate comprehensive burn rate and pacing metrics"""
        try:
            # Get SKU information
            sku = await get_sku_by_id(sku_id)
            if not sku:
                return {"success": False, "message": "SKU not found"}
            
            total_budget = sku.get("total_budget", 0)
            remaining_budget = sku.get("remaining_budget", 0)
            
            # Get spend data
            hourly_spend = await get_hourly_spend(sku_id, 24)
            daily_spend = await get_daily_spend(sku_id, 30)
            
            # Calculate burn rates
            hourly_burn = sum(h["hourly_spend"] for h in hourly_spend[-1:]) if hourly_spend else 0
            daily_burn = sum(d["daily_spend"] for d in daily_spend[-1:]) if daily_spend else 0
            weekly_burn = sum(d["daily_spend"] for d in daily_spend[-7:]) if daily_spend else 0
            
            # Calculate pacing metrics
            current_date = datetime.now()
            days_in_month = 30  # Simplified
            days_remaining = days_in_month - current_date.day
            
            target_daily_pace = total_budget / days_in_month
            actual_vs_target_pace = (daily_burn / target_daily_pace) if target_daily_pace > 0 else 0
            pace_variance = (actual_vs_target_pace - 1.0) * 100
            
            # Calculate forecasting
            days_until_budget_depletion = (remaining_budget / daily_burn) if daily_burn > 0 else float('inf')
            projected_month_end_spend = daily_burn * days_remaining
            recommended_daily_adjustment = (remaining_budget / days_remaining) - daily_burn if days_remaining > 0 else 0
            
            # Determine budget health
            budget_health = self._determine_pacing_status(pace_variance)
            
            # Calculate budget utilization
            total_spent = total_budget - remaining_budget
            budget_utilization = (total_spent / total_budget * 100) if total_budget > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "sku_id": sku_id,
                    "burn_rates": {
                        "hourly_burn": hourly_burn,
                        "daily_burn": daily_burn,
                        "weekly_burn": weekly_burn
                    },
                    "pacing_analysis": {
                        "target_daily_pace": target_daily_pace,
                        "actual_vs_target_pace": actual_vs_target_pace,
                        "pace_variance_percentage": pace_variance
                    },
                    "budget_status": {
                        "total_budget": total_budget,
                        "remaining_budget": remaining_budget,
                        "total_spent": total_spent,
                        "budget_utilization_percentage": budget_utilization
                    },
                    "forecasting": {
                        "days_until_budget_depletion": days_until_budget_depletion,
                        "projected_month_end_spend": projected_month_end_spend,
                        "recommended_daily_adjustment": recommended_daily_adjustment
                    },
                    "health_status": {
                        "budget_health": budget_health,
                        "status_description": self._get_health_description(budget_health)
                    }
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_platform_breakdown(self, sku_id: str, days: int = 7) -> Dict:
        """Get performance breakdown by platform"""
        try:
            breakdown = await get_platform_performance_breakdown(sku_id, days)
            if not breakdown:
                return {
                    "success": False,
                    "message": "No platform performance data found"
                }
            
            return {
                "success": True,
                "data": {
                    "sku_id": sku_id,
                    "period_days": days,
                    "platform_breakdown": breakdown
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_mode_breakdown(self, sku_id: str, days: int = 7) -> Dict:
        """Get performance breakdown by intelligence mode"""
        try:
            breakdown = await get_mode_performance_breakdown(sku_id, days)
            if not breakdown:
                return {
                    "success": False,
                    "message": "No mode performance data found"
                }
            
            return {
                "success": True,
                "data": {
                    "sku_id": sku_id,
                    "period_days": days,
                    "mode_breakdown": breakdown
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _determine_pacing_status(self, pace_variance: float) -> str:
        """Determine pacing status based on variance"""
        if -5 <= pace_variance <= 5:
            return "optimal"  # 95-105% of target pace
        elif pace_variance < -5:
            return "under_pace"  # <95% of target pace
        elif 5 < pace_variance <= 20:
            return "over_pace"  # 105-120% of target pace
        elif pace_variance > 20:
            return "critical_overspend"  # >120% of target pace
        else:
            return "budget_exhausted"  # 100% budget spent
    
    def _get_health_description(self, health_status: str) -> str:
        """Get human-readable health status description"""
        descriptions = {
            "optimal": "Spending at optimal pace - on track to meet budget goals",
            "under_pace": "under target pace - consider increasing budget allocation",
            "over_pace": "over target pace - monitor closely for budget depletion",
            "critical_overspend": "Critical overspend detected - immediate action required",
            "budget_exhausted": "Budget has been fully utilized"
        }
        return descriptions.get(health_status, "Unknown status")
