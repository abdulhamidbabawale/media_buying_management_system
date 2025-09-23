from app.models import Campaign
from fastapi.encoders import jsonable_encoder
from app.db.campaign_queries import (
    create_campaign, get_campaign_by_id, get_campaigns_by_client,
    get_campaigns_by_sku, update_campaign, delete_campaign,
    pause_campaign, activate_campaign, update_campaign_budget,
    get_active_campaigns, get_campaigns_by_platform, get_all_campaigns
)

async def create_campaign_service(campaign: Campaign):
    """Create a new campaign"""
    campaign_dict = jsonable_encoder(campaign)
    try:
        result = await create_campaign(campaign_dict)
        if result:
            return {
                "success": True,
                "message": "Campaign Created Successfully",
                "campaign_id": str(result)
            }
        else:
            return {"success": False, "message": "Campaign creation failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_campaign_by_id_service(campaign_id: str):
    """Get campaign by ID"""
    try:
        campaign = await get_campaign_by_id(campaign_id)
        return campaign
    except Exception as e:
        return None

async def get_campaigns_by_client_service(client_id: str):
    """Get all campaigns for a specific client"""
    try:
        campaigns = await get_campaigns_by_client(client_id)
        return campaigns
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_all_campaigns_service():
    """Get all campaigns (admin)."""
    try:
        campaigns = await get_all_campaigns()
        return campaigns
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_campaigns_by_sku_service(sku_id: str):
    """Get all campaigns for a specific SKU"""
    try:
        campaigns = await get_campaigns_by_sku(sku_id)
        return campaigns
    except Exception as e:
        return {"success": False, "message": str(e)}

async def update_campaign_service(campaign_id: str, campaign: Campaign):
    """Update campaign"""
    campaign_dict = jsonable_encoder(campaign)
    try:
        result = await update_campaign(campaign_id, campaign_dict)
        if result:
            return {
                "success": True,
                "message": "Campaign Updated Successfully",
                "campaign_id": str(campaign_id)
            }
        else:
            return {"success": False, "message": "Campaign update failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def delete_campaign_service(campaign_id: str):
    """Delete campaign (soft delete)"""
    try:
        result = await delete_campaign(campaign_id)
        if result:
            return {
                "success": True,
                "message": "Campaign Deleted Successfully"
            }
        else:
            return {"success": False, "message": "Campaign deletion failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def pause_campaign_service(campaign_id: str):
    """Pause campaign"""
    try:
        result = await pause_campaign(campaign_id)
        if result:
            return {
                "success": True,
                "message": "Campaign Paused Successfully"
            }
        else:
            return {"success": False, "message": "Campaign pause failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def activate_campaign_service(campaign_id: str):
    """Activate campaign"""
    try:
        result = await activate_campaign(campaign_id)
        if result:
            return {
                "success": True,
                "message": "Campaign Activated Successfully"
            }
        else:
            return {"success": False, "message": "Campaign activation failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def update_campaign_budget_service(campaign_id: str, new_budget: float):
    """Update campaign budget"""
    try:
        result = await update_campaign_budget(campaign_id, new_budget)
        if result:
            return {
                "success": True,
                "message": "Campaign Budget Updated Successfully"
            }
        else:
            return {"success": False, "message": "Budget update failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_active_campaigns_service():
    """Get all active campaigns"""
    try:
        campaigns = await get_active_campaigns()
        return campaigns
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_campaigns_by_platform_service(platform: str):
    """Get campaigns by platform"""
    try:
        campaigns = await get_campaigns_by_platform(platform)
        return campaigns
    except Exception as e:
        return {"success": False, "message": str(e)}
