from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import Campaign
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

collection = db.campaigns

async def create_campaign(campaign: dict):
    """Create a new campaign"""
    result = await collection.insert_one(campaign)
    return str(result.inserted_id)

async def get_campaign_by_id(campaign_id: str):
    """Get campaign by ID"""
    return await collection.find_one({"_id": campaign_id})

async def get_campaigns_by_client(client_id: str):
    """Get all campaigns for a specific client"""
    return await collection.find({"client_id": client_id}).to_list(1000)

async def get_campaigns_by_sku(sku_id: str):
    """Get all campaigns for a specific SKU"""
    return await collection.find({"sku_id": sku_id}).to_list(1000)

async def update_campaign(campaign_id: str, campaign_data: dict):
    """Update campaign data"""
    result = await collection.update_one(
        {"_id": campaign_id}, 
        {"$set": campaign_data}
    )
    return result.modified_count > 0

async def delete_campaign(campaign_id: str):
    """Delete a campaign (soft delete by setting status to 'deleted')"""
    result = await collection.update_one(
        {"_id": campaign_id}, 
        {"$set": {"status": "deleted", "updated_at": datetime.now()}}
    )
    return result.modified_count > 0

async def pause_campaign(campaign_id: str):
    """Pause a campaign"""
    result = await collection.update_one(
        {"_id": campaign_id}, 
        {"$set": {"status": "paused", "updated_at": datetime.now()}}
    )
    return result.modified_count > 0

async def activate_campaign(campaign_id: str):
    """Activate a campaign"""
    result = await collection.update_one(
        {"_id": campaign_id}, 
        {"$set": {"status": "active", "updated_at": datetime.now()}}
    )
    return result.modified_count > 0

async def update_campaign_budget(campaign_id: str, new_budget: float):
    """Update campaign budget"""
    result = await collection.update_one(
        {"_id": campaign_id}, 
        {"$set": {"budget_allocated": new_budget, "updated_at": datetime.now()}}
    )
    return result.modified_count > 0

async def get_active_campaigns():
    """Get all active campaigns"""
    return await collection.find({"status": "active"}).to_list(1000)

async def get_campaigns_by_platform(platform: str):
    """Get campaigns by platform"""
    return await collection.find({"platform": platform}).to_list(1000)
