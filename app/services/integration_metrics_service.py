"""
Integration Metrics Service - Normalization and persistence for vendor/platform metrics
"""
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from app.schemas.integration_metrics import RawIntegrationMetrics, NormalizedMetrics
from app.db.connection import db

class IntegrationMetricsService:
    def __init__(self):
        self.raw_collection = db.integration_metrics_raw
        self.norm_collection = db.integration_metrics

    async def save_raw(self, vendor: str, campaign_id: str, platform: Optional[str], account_id: Optional[str], payload: Dict[str, Any], date_range: Tuple[datetime, datetime]):
        raw = RawIntegrationMetrics(
            vendor=vendor,
            campaign_id=campaign_id,
            platform=platform,
            account_id=account_id,
            payload=payload,
            start=date_range[0],
            end=date_range[1],
        )
        await self.raw_collection.insert_one(raw.model_dump())

    def normalize_payload(self, vendor: str, payload: Dict[str, Any], campaign_id: str, platform: Optional[str], account_id: Optional[str], date_range: Tuple[datetime, datetime]) -> NormalizedMetrics:
        # Vendor-specific mapping. Keep it defensive.
        spend = float(payload.get("spend") or payload.get("total_spend") or payload.get("cost") or 0.0)
        impressions = int(payload.get("impressions") or payload.get("total_impressions") or 0)
        clicks = int(payload.get("clicks") or payload.get("total_clicks") or 0)
        conversions = int(payload.get("conversions") or payload.get("total_conversions") or 0)

        ctr = (clicks / impressions * 100.0) if impressions > 0 else float(payload.get("ctr") or 0.0)
        cpc = (spend / clicks) if clicks > 0 else float(payload.get("cpc") or 0.0)
        roas = (conversions / spend) if spend > 0 else float(payload.get("roas") or 0.0)
        cpm = (spend / impressions * 1000.0) if impressions > 0 else float(payload.get("cpm") or 0.0)

        return NormalizedMetrics(
            vendor=vendor,
            campaign_id=campaign_id,
            platform=platform,
            account_id=account_id,
            start=date_range[0],
            end=date_range[1],
            spend=spend,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            ctr=ctr,
            cpc=cpc,
            roas=roas,
            cpm=cpm,
            data_quality_score=payload.get("data_quality_score", 0.0),
        )

    async def save_normalized(self, normalized: NormalizedMetrics):
        await self.norm_collection.insert_one(normalized.model_dump())

# global instance
integration_metrics_service = IntegrationMetricsService()
