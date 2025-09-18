from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class CampaignCreateRequest(BaseModel):
    sku_id: str
    client_id: str
    platform: str  # google, meta, tiktok, linkedin
    campaign_name: str
    budget_allocated: float
    target_groups: List[Dict] = []
    creatives: List[Dict] = []

class CampaignUpdateRequest(BaseModel):
    campaign_name: Optional[str] = None
    budget_allocated: Optional[float] = None
    target_groups: Optional[List[Dict]] = None
    creatives: Optional[List[Dict]] = None
    performance_metrics: Optional[Dict] = None

class CampaignResponse(BaseModel):
    id: str
    sku_id: str
    client_id: str
    platform: str
    campaign_name: str
    status: str
    budget_allocated: float
    target_groups: List[Dict]
    creatives: List[Dict]
    created_date: datetime
    performance_metrics: Optional[Dict] = None

class CampaignListResponse(BaseModel):
    message: str
    data: List[CampaignResponse]

class CampaignCreateResponse(BaseModel):
    message: str
    campaign_id: str

class BudgetUpdateRequest(BaseModel):
    new_budget: float
