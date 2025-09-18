from uuid import uuid4
from datetime import datetime, timedelta
from app.db.connection import db
from app.models import PerformanceMetric
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

collection = db.performance_metrics

async def create_performance_metric(metric: dict):
    """Create a new performance metric record"""
    result = await collection.insert_one(metric)
    return str(result.inserted_id)

async def get_performance_metrics_by_campaign(campaign_id: str, days: int = 7):
    """Get performance metrics for a campaign over specified days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return await collection.find({
        "campaign_id": campaign_id,
        "timestamp": {"$gte": start_date, "$lte": end_date}
    }).sort("timestamp", -1).to_list(1000)

async def get_performance_metrics_by_sku(sku_id: str, days: int = 7):
    """Get aggregated performance metrics for a SKU over specified days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "sku_id": sku_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_spend": {"$sum": "$spend"},
                "total_impressions": {"$sum": "$impressions"},
                "total_clicks": {"$sum": "$clicks"},
                "total_conversions": {"$sum": "$conversions"},
                "avg_roas": {"$avg": "$roas"},
                "avg_ctr": {"$avg": "$ctr"},
                "avg_cpc": {"$avg": "$cpc"},
                "data_points": {"$sum": 1}
            }
        }
    ]
    
    results = await collection.aggregate(pipeline).to_list(1)
    return results[0] if results else None

async def get_performance_metrics_by_client(client_id: str, days: int = 7):
    """Get aggregated performance metrics for a client over specified days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "client_id": client_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_spend": {"$sum": "$spend"},
                "total_impressions": {"$sum": "$impressions"},
                "total_clicks": {"$sum": "$clicks"},
                "total_conversions": {"$sum": "$conversions"},
                "avg_roas": {"$avg": "$roas"},
                "avg_ctr": {"$avg": "$ctr"},
                "avg_cpc": {"$avg": "$cpc"},
                "data_points": {"$sum": 1}
            }
        }
    ]
    
    results = await collection.aggregate(pipeline).to_list(1)
    return results[0] if results else None

async def get_hourly_spend(sku_id: str, hours: int = 24):
    """Get spend data for burn rate calculation"""
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)
    
    pipeline = [
        {
            "$match": {
                "sku_id": sku_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$hour": "$timestamp"}
                },
                "hourly_spend": {"$sum": "$spend"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    return await collection.aggregate(pipeline).to_list(1000)

async def get_daily_spend(sku_id: str, days: int = 30):
    """Get daily spend data for pacing analysis"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "sku_id": sku_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"}
                },
                "daily_spend": {"$sum": "$spend"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    return await collection.aggregate(pipeline).to_list(1000)

async def get_platform_performance_breakdown(sku_id: str, days: int = 7):
    """Get performance breakdown by platform"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "sku_id": sku_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$platform",
                "total_spend": {"$sum": "$spend"},
                "total_impressions": {"$sum": "$impressions"},
                "total_clicks": {"$sum": "$clicks"},
                "total_conversions": {"$sum": "$conversions"},
                "avg_roas": {"$avg": "$roas"},
                "avg_ctr": {"$avg": "$ctr"},
                "avg_cpc": {"$avg": "$cpc"}
            }
        }
    ]
    
    return await collection.aggregate(pipeline).to_list(1000)

async def get_mode_performance_breakdown(sku_id: str, days: int = 7):
    """Get performance breakdown by intelligence mode (explore/exploit)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "sku_id": sku_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$mode",
                "total_spend": {"$sum": "$spend"},
                "total_impressions": {"$sum": "$impressions"},
                "total_clicks": {"$sum": "$clicks"},
                "total_conversions": {"$sum": "$conversions"},
                "avg_roas": {"$avg": "$roas"},
                "avg_ctr": {"$avg": "$ctr"},
                "avg_cpc": {"$avg": "$cpc"}
            }
        }
    ]
    
    return await collection.aggregate(pipeline).to_list(1000)
