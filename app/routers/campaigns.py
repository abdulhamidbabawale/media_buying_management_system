from fastapi import APIRouter, HTTPException, Depends, Request
from app.models import Campaign
from app.services import campaign_service
from app.schemas.campaign_schema import (
    CampaignCreateRequest, CampaignUpdateRequest, CampaignListResponse,
    CampaignCreateResponse, BudgetUpdateRequest
)
from app.middleware import (
    get_current_client_id,
    get_current_client_id_optional,
    get_current_user_role,
    verify_client_access,
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.post("/", response_model=CampaignCreateResponse)
async def create_campaign(
    campaign: CampaignCreateRequest,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Create a new campaign"""
    # Verify client access
    await verify_client_access(client_id, campaign.client_id, request)
    
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

@router.get("/", response_model=dict)
async def get_campaigns(
    request: Request,
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Get campaigns: admin sees all, clients see their own"""
    if role == "admin":
        campaigns = await campaign_service.get_all_campaigns_service()
    else:
        if not current_client_id:
            raise HTTPException(status_code=401, detail="Client context not found")
        campaigns = await campaign_service.get_campaigns_by_client_service(current_client_id)
    return {
        "message": "Campaigns retrieved successfully",
        "data": campaigns or []
    }

@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    request: Request,
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Get campaign by ID (admin bypasses client check)"""
    campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if role != "admin":
        if not current_client_id:
            raise HTTPException(status_code=401, detail="Client context not found")
        await verify_client_access(current_client_id, campaign["client_id"], request)
    return {"message": "Campaign retrieved successfully", "data": campaign}

@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    campaign_update: CampaignUpdateRequest,
    request: Request,
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Update campaign"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if role != "admin":
        if not current_client_id:
            raise HTTPException(status_code=401, detail="Client context not found")
        await verify_client_access(current_client_id, existing_campaign["client_id"], request)
    
    
    result = await campaign_service.update_campaign_service(campaign_id, campaign_update)
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
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Delete campaign (soft delete)"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if role != "admin":
        if not current_client_id:
            raise HTTPException(status_code=401, detail="Client context not found")
        await verify_client_access(current_client_id, existing_campaign["client_id"], request)
    
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
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Pause campaign"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(current_client_id, existing_campaign["client_id"], request)
    
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
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Activate campaign"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(current_client_id, existing_campaign["client_id"], request)
    
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
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Update campaign budget"""
    # Get existing campaign to verify client access
    existing_campaign = await campaign_service.get_campaign_by_id_service(campaign_id)
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await verify_client_access(current_client_id, existing_campaign["client_id"], request)
    
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
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional)
):
    """Get all campaigns for a specific SKU (admin sees all)"""
    campaigns = await campaign_service.get_campaigns_by_sku_service(sku_id)
    if not campaigns:
        raise HTTPException(status_code=404, detail="No campaigns found for this SKU")
    if role == "admin":
        return {"message": "Campaigns retrieved successfully", "data": campaigns}
    if not current_client_id:
        raise HTTPException(status_code=401, detail="Client context not found")
    filtered_campaigns = [c for c in campaigns if c["client_id"] == current_client_id]
    return {"message": "Campaigns retrieved successfully", "data": filtered_campaigns}
