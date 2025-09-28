# routes/integration_routes.py
from fastapi import APIRouter, Request,Depends,HTTPException, Query
import requests
import os
from app.db.connection import db 
from app.db.google_ads_queries import get_user_config
from app.services.google_ads_service import CampaignService,MetricsService,get_google_ads_client,create_google_ads_campaign
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
import urllib.parse
from app.schemas.google_ads_schema import CampaignRequest
from app.db.google_ads_queries import save_campaign_to_db
from app.middleware import (
    get_current_client_id,
    get_current_client_id_optional,
    get_current_client_id_or_admin,
    get_current_user_role,
    verify_client_access,
)

router = APIRouter(prefix="/google-ads", tags=["Google"])

collection = db.google_ads_connection

CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
REDIRECT_URI = os.getenv("GOOGLE_ADS_REDIRECT_URI")  
SCOPES = ["https://www.googleapis.com/auth/adwords"]

@router.get("/oauth2/start")
def start_google_ads_auth( current_client_id = Depends(get_current_client_id_optional)):
# def start_google_ads_auth( current_client_id = Depends(get_current_client_id_optional),user_id: str = Query(...)):
    """
    Redirect user to Google Ads OAuth2 consent screen.
    """
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",   # Needed for refresh token
        "prompt": "consent",        # Always ask to ensure refresh_token is returned
        "state": current_client_id           # So we know which user to save tokens for
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {"auth_url": url}


@router.get("/oauth2/callback")
def google_ads_callback(code: str = Query(...), state: str = Query(...)):
    """
    Handles Google Ads OAuth2 callback.
    Exchanges code for tokens and saves refresh_token in MongoDB.
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    tokens = response.json()
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token returned. Try again with prompt=consent")

    # Save into MongoDB for the user (state = user_id)
    collection.update_one(
        {"_id": state},
        {"$set": {
            "google_ads": {
                # "developer_token": DEVELOPER_TOKEN,
                # "client_id": CLIENT_ID,
                # "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "access_token": access_token
            }
        }},
        upsert=True
    )

    return {"message": "Google Ads connected successfully", "refresh_token": refresh_token}


@router.post("/campaigns/create")
async def create_campaign(req: CampaignRequest):
    result = await create_google_ads_campaign(req)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Save to DB
    save_campaign_to_db(result["campaign_obj"])

    return {
        "message": "Campaign created and saved successfully",
        "campaign_id": result["campaign_id"],
        "ad_group_id": result["ad_group_id"],
        "ad_id": result["ad_id"],
        "keywords": result["keywords"],
    }

@router.get("/campaigns/metrics")
async def get_campaign_metrics(
    user_id: str = Query(...),
    customer_id: str = Query(...),
    campaign_id: str = Query(...),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
):
    """
    Fetch metrics for a specific campaign
    """
    # Fetch user's Google Ads auth details from MongoDB
    user_config =await get_google_ads_client(user_id)

    if not user_config:
        return {"error": "User config not found"}

    service = MetricsService(user_config)
    return service.get_campaign_metrics(
        customer_id=customer_id,
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
    )


