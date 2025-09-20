from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.integration_service import integration_service
from app.middleware import get_current_client_id, verify_client_access
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter(prefix="/integrations", tags=["Integrations"])

class PlatformCredentials(BaseModel):
    platform: str
    credentials: Dict

class CampaignBudgetUpdate(BaseModel):
    campaign_id: str
    new_budget: float
    platform: str
    account_id: str

class CampaignCreationRequest(BaseModel):
    campaign_data: Dict
    platform: str
    account_id: str

class IntegratorCredentials(BaseModel):
    # keys: revealbot, adroll, stackadapt, adespresso, madgicx
    credentials: Dict[str, Dict]

@router.post("/platforms/initialize")
async def initialize_platforms(
    credentials: Dict[str, Dict],
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Initialize platform connectors for a client"""
    result = await integration_service.initialize_platforms(credentials)
    
    if result["success"]:
        return {
            "message": "Platform initialization completed",
            "results": result["results"]
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.get("/platforms/status")
async def get_platform_status(
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Get status of all registered platforms and integrators"""
    status = await integration_service.get_platform_status()
    return {
        "message": "Platform status retrieved successfully",
        "data": status
    }

@router.get("/platforms/available")
async def get_available_platforms(
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Get list of available platforms"""
    platforms = await integration_service.get_available_platforms()
    return {
        "message": "Available platforms retrieved successfully",
        "data": platforms
    }

@router.get("/integrators/available")
async def get_available_integrators(
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Get list of available integrators"""
    integrators = await integration_service.get_available_integrators()
    return {
        "message": "Available integrators retrieved successfully",
        "data": integrators
    }

@router.post("/integrators/initialize")
async def initialize_integrators(
    payload: IntegratorCredentials,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Initialize media buying integrators"""
    result = await integration_service.initialize_integrators(payload.credentials)
    if result["success"]:
        return {"message": "Integrators initialized", "results": result["results"]}
    raise HTTPException(status_code=400, detail=result.get("message", "Initialization failed"))

@router.post("/platforms/validate")
async def validate_platform_credentials(
    platform_creds: PlatformCredentials,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Validate platform credentials"""
    result = await integration_service.validate_platform_credentials(
        platform_creds.platform, 
        platform_creds.credentials
    )
    
    if result["success"]:
        return {
            "message": "Credentials validated successfully",
            "valid": True
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.put("/campaigns/budget")
async def update_campaign_budget(
    budget_update: CampaignBudgetUpdate,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Update campaign budget through integration middleware"""
    result = await integration_service.execute_campaign_budget_update(
        budget_update.campaign_id,
        budget_update.new_budget,
        budget_update.platform,
        budget_update.account_id
    )
    
    if result["success"]:
        return {
            "message": "Campaign budget updated successfully",
            "data": {
                "campaign_id": result["campaign_id"],
                "new_budget": result["new_budget"],
                "source": result["source"]
            }
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.post("/campaigns/create")
async def create_campaign(
    campaign_request: CampaignCreationRequest,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Create campaign through integration middleware"""
    result = await integration_service.create_campaign(
        campaign_request.campaign_data,
        campaign_request.platform,
        campaign_request.account_id
    )
    
    if result["success"]:
        return {
            "message": "Campaign created successfully",
            "data": {
                "campaign_id": result["campaign_id"],
                "platform": result["platform"],
                "source": result["source"]
            }
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    platform: str,
    account_id: str,
    request: Request,
    client_id: str = Depends(get_current_client_id)
):
    """Pause campaign through integration middleware"""
    result = await integration_service.pause_campaign(
        campaign_id,
        platform,
        account_id
    )
    
    if result["success"]:
        return {
            "message": "Campaign paused successfully",
            "data": {
                "campaign_id": result["campaign_id"],
                "source": result["source"]
            }
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.get("/campaigns/{campaign_id}/performance")
async def get_campaign_performance(
    campaign_id: str,
    platform: str,
    account_id: str,
    days: int = 7,
    request: Request = None,
    client_id: str = Depends(get_current_client_id)
):
    """Get aggregated campaign performance data"""
    result = await integration_service.get_campaign_performance(
        campaign_id,
        platform,
        account_id,
        days
    )
    
    if result["success"]:
        return {
            "message": "Campaign performance retrieved successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=404, detail=result["message"])
