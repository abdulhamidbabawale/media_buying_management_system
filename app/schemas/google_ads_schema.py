from pydantic import BaseModel,Field
from typing import List, Dict, Optional,Literal
from datetime import datetime
from uuid import UUID, uuid4

#for creating campaign
class CampaignRequest(BaseModel):
    budget_micros: int
    campaign_type: str
    name: str
    ad_group_name: str
    keywords: List[str]
    headlines: List[str]
    descriptions: List[str]
    final_url: str


class Keyword(BaseModel):
    criterion_id: str
    keyword_text: str
    match_type: str
    status: str

class Ad(BaseModel):
    ad_id: str
    ad_type: str
    status: str
    headlines: List[str]
    descriptions: List[str]
    final_urls: List[str]

class AdGroup(BaseModel):
    ad_group_id: str
    ad_group_name: str
    status: str
    cpc_bid_micros: Optional[int]
    ads: List[Ad] = []
    keywords: List[Keyword] = []

class Budget(BaseModel):
    amount_micros: int
    currency_code: str

class Campaign(BaseModel):
    id: str = Field(alias="_id")
    client_id: str
    google_customer_id: str
    campaign_id: str
    campaign_name: str
    status: str
    budget: Budget
    channel: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ad_groups: List[AdGroup] = []

class GoogleCampaignListResponse(BaseModel):
    message:str
    data: List[Campaign] = []

class GoogleGetCampaignResponse(BaseModel):
    message:str
    data: Campaign  

class CampaignStatusUpdate(BaseModel):
    campaign_id: str
    new_status: Literal["ENABLED", "PAUSED", "REMOVED"] = Field(..., description="New status of the campaign") 