from pydantic import BaseModel,Field
from typing import List, Dict, Optional
from datetime import datetime

class CampaignRequest(BaseModel):
    user_id: str
    customer_id: str
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
    user_id: str
    google_customer_id: str
    campaign_id: str
    campaign_name: str
    status: str
    budget: Budget
    channel: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ad_groups: List[AdGroup] = []
