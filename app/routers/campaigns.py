from fastapi import APIRouter, HTTPException, Depends, Request
from app.models import Campaign
from app.services import campaign_service
from app.schemas.campaign_schema import (
    CampaignCreateRequest, CampaignUpdateRequest, CampaignListResponse,
    CampaignCreateResponse, BudgetUpdateRequest
)
from app.middleware import get_current_client_id, verify_client_access

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.post("/", response_model=CampaignCreateResponse)
async def create_campaign(
    campaign: CampaignCreateRequest,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Create a new campaign"""
    # Verify client access
    await verify_client_access(client_id, campaign.client_id)
    
    # Create campaign model
    campaign_model = Campaign(
        sku_id=campaign.sku_id,
        client_id=campaign.client_id,
        platform=campaign.platform,
        campaign_name=campaign.campaign_name,
        budget_allocated=campaign.budget_allocated,
        target_groups=campaign.target_groups,
        creatives=campaign.creatives,
        status="active"
    )
    
    result = await campaign_service.create_campaign_service(campaign_model)
    if result.get("success"):
        return {
            "message": result["message"],
            "campaign_id": result["campaign_id"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error creating campaign: {result['message']}")

@router.get("/", response_model=CampaignListResponse)
async def get_campaigns(
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Get all campaigns for the current client"""
    campaigns = await campaign_service.get_campaigns_by_client_service(client_id)
    if campaigns:
        return {
            "message": "Campaigns retrieved successfully",
            "data": campaigns
        }
    else:
        raise HTTPException(status_code=404, detail="No campaigns found")

@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Get campaign by ID"""
    campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify client access
    await verify_client_access(client_id, campaign["client_id"])
    
    return {
        "message": "Campaign retrieved successfully",
        "data": campaign
    }

@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    campaign_update: CampaignUpdateRequest,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Update campaign"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(client_id, existing_campaign["client_id"])
    
    # Create updated campaign model
    campaign_model = Campaign(
        sku_id=existing_campaign["sku_id"],
        client_id=existing_campaign["client_id"],
        platform=existing_campaign["platform"],
        campaign_name=campaign_update.campaign_name or existing_campaign["campaign_name"],
        budget_allocated=campaign_update.budget_allocated or existing_campaign["budget_allocated"],
        target_groups=campaign_update.target_groups or existing_campaign["target_groups"],
        creatives=campaign_update.creatives or existing_campaign["creatives"],
        status=existing_campaign["status"],
        performance_metrics=campaign_update.performance_metrics or existing_campaign.get("performance_metrics", {})
    )
    
    result = await campaign_service.update_campaign_service(campaign_id, campaign_model)
    if result.get("success"):
        return {
            "message": result["message"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error updating campaign: {result['message']}")

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Delete campaign (soft delete)"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(client_id, existing_campaign["client_id"])
    
    result = await campaign_service.delete_campaign_service(campaign_id)
    if result.get("success"):
        return {
            "message": result["message"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error deleting campaign: {result['message']}")

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Pause campaign"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(client_id, existing_campaign["client_id"])
    
    result = await campaign_service.pause_campaign_service(campaign_id)
    if result.get("success"):
        return {
            "message": result["message"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error pausing campaign: {result['message']}")

@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Activate campaign"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(client_id, existing_campaign["client_id"])
    
    result = await campaign_service.activate_campaign_service(campaign_id)
    if result.get("success"):
        return {
            "message": result["message"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error activating campaign: {result['message']}")

@router.put("/{campaign_id}/budget")
async def update_campaign_budget(
    campaign_id: str,
    budget_update: BudgetUpdateRequest,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Update campaign budget"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(client_id, existing_campaign["client_id"])
    
    result = await campaign_service.update_campaign_budget_service(campaign_id, budget_update.new_budget)
    if result.get("success"):
        return {
            "message": result["message"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Error updating budget: {result['message']}")

@router.get("/sku/{sku_id}")
async def get_campaigns_by_sku(
    sku_id: str,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Get all campaigns for a specific SKU"""
    campaigns = await campaign_service.get_campaigns_by_sku_service(sku_id)
    if campaigns:
        # Filter campaigns by client access
        filtered_campaigns = [c for c in campaigns if c["client_id"] == client_id]
        return {
            "message": "Campaigns retrieved successfully",
            "data": filtered_campaigns
        }
    else:
        raise HTTPException(status_code=404, detail="No campaigns found for this SKU")
