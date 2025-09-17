from pydantic import BaseModel
from typing import Optional, List, Dict

class skuCreateResponse(BaseModel):
    message: str
    client_id: str

class SkuUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    total_budget: Optional[float] = 0.0
    remaining_budget: Optional[float] = 0.0
    status: Optional[str] = "pending"
    intelligence_settings: Optional[Dict] = {}

