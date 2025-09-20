from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class RawIntegrationMetrics(BaseModel):
    vendor: str
    campaign_id: str
    platform: Optional[str] = None
    account_id: Optional[str] = None
    payload: Dict[str, Any]
    start: datetime
    end: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

class NormalizedMetrics(BaseModel):
    campaign_id: str
    platform: Optional[str] = None
    account_id: Optional[str] = None
    vendor: Optional[str] = None
    start: datetime
    end: datetime
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    roas: float = 0.0
    cpm: float = 0.0
    data_quality_score: float = 0.0
    aggregated_at: datetime = Field(default_factory=datetime.utcnow)
