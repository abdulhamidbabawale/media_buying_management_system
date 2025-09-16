from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId
from uuid import UUID, uuid4

# ------------------ Users ------------------
class User(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    email: str
    password: str
    first_name: str
    last_name: str
    role: str  # admin, manager, analyst, etc.
    permissions: Optional[List[str]] = []
    status: str  # active, suspended, pending
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ------------------ Clients ------------------
class Client(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    name: str
    industry: str
    created_date: datetime = Field(default_factory=datetime.now)
    settings: Optional[Dict] = {}
    api_keys_refs: Optional[Dict] = {}

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ------------------ SKUs ------------------
class SKU(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    client_id: str
    name: str
    category: str
    total_budget: float
    remaining_budget: float
    status: str  # active, paused, completed
    created_date: datetime = Field(default_factory=datetime.now)
    intelligence_settings: Optional[Dict] = {}

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ------------------ Campaigns ------------------
class Campaign(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    sku_id: str
    client_id: str
    platform: str  # google, meta, tiktok
    campaign_name: str
    status: str  # active, paused, completed
    budget_allocated: float
    target_groups: List[Dict] = []
    creatives: List[Dict] = []
    created_date: datetime = Field(default_factory=datetime.now)
    performance_metrics: Optional[Dict] = {}

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ------------------ Performance Metrics ------------------
class PerformanceMetric(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    campaign_id: str
    sku_id: str
    client_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    spend: float
    impressions: int
    clicks: int
    conversions: int
    roas: float
    ctr: float
    cpc: float
    platform: str
    mode: str  # explore, exploit

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ------------------ Intelligence Decisions ------------------
class IntelligenceDecision(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    sku_id: str
    client_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    decision_type: str
    old_allocation: Dict
    new_allocation: Dict
    reason: str
    confidence_score: float
    mode: str  # explore, exploit
    data_points_used: int

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ------------------ System Benchmarks ------------------
class SystemBenchmark(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    industry_category: str
    platform: str
    metric_type: str
    avg_performance: float
    std_deviation: float
    sample_size: int
    date_range: Dict

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
