import httpx
from typing import Dict, List, Tuple
from datetime import datetime
from app.integrations.base import AdPlatform, IntegrationError
import logging

logger = logging.getLogger(__name__)


class LinkedInAdsConnector(AdPlatform):
    """LinkedIn Ads API connector (scaffold)."""

    def __init__(self, credentials: Dict):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.account_id = credentials.get("account_id")
        self.base_url = "https://api.linkedin.com/v2"

    async def get_campaigns(self, account_id: str) -> List[Dict]:
        try:
            headers = await self._get_auth_headers()
            async with httpx.AsyncClient() as client:
                # Placeholder endpoint for campaigns (LinkedIn uses adAccounts/campaigns)
                response = await client.get(
                    f"{self.base_url}/adCampaignsV2",
                    headers=headers,
                    params={"q": "search", "search.account.values[0]": f"urn:li:sponsoredAccount:{self.account_id}"}
                )
                if response.status_code >= 300:
                    raise IntegrationError(f"LinkedIn API error: {response.text}")
                data = response.json()
                elements = data.get("elements", [])
                campaigns = []
                for c in elements:
                    campaigns.append({
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "status": c.get("status"),
                        "budget": float(c.get("dailyBudget", {}).get("amount", 0) or 0),
                        "platform": "linkedin_ads"
                    })
                return campaigns
        except Exception as e:
            logger.error(f"LinkedIn get_campaigns error: {e}")
            raise IntegrationError(str(e))

    async def create_campaign(self, campaign_data: Dict) -> str:
        try:
            headers = await self._get_auth_headers()
            payload = {
                "account": f"urn:li:sponsoredAccount:{self.account_id}",
                "name": campaign_data.get("name"),
                "status": "PAUSED",
                "dailyBudget": {"amount": int(campaign_data.get("budget", 0) * 100)}
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/adCampaignsV2",
                    headers=headers,
                    json=payload
                )
                if response.status_code >= 300:
                    raise IntegrationError(f"LinkedIn create error: {response.text}")
                return response.json().get("id", "")
        except Exception as e:
            logger.error(f"LinkedIn create_campaign error: {e}")
            raise IntegrationError(str(e))

    async def update_campaign_budget(self, campaign_id: str, budget: float) -> bool:
        try:
            headers = await self._get_auth_headers()
            payload = {"dailyBudget": {"amount": int(budget * 100)}}
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/adCampaignsV2/{campaign_id}", headers=headers, json=payload
                )
                return response.status_code < 300
        except Exception as e:
            logger.error(f"LinkedIn budget update error: {e}")
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        try:
            headers = await self._get_auth_headers()
            # Placeholder metrics aggregation
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/adAnalyticsV2",
                    headers=headers,
                    params={
                        "q": "analytics",
                        "pivot": "CAMPAIGN",
                        "timeRange.start.year": date_range[0].year,
                        "timeRange.end.year": date_range[1].year,
                        # ... additional params normally required
                    }
                )
                if response.status_code >= 300:
                    raise IntegrationError(f"LinkedIn metrics error: {response.text}")
                # Minimal normalization
                data = response.json().get("elements", [{}])[0]
                raw = {
                    "spend": float(data.get("costInUsd", 0) or 0),
                    "impressions": int(data.get("impressions", 0) or 0),
                    "clicks": int(data.get("clicks", 0) or 0),
                    "conversions": int(data.get("conversions", 0) or 0),
                    "ctr": float(data.get("clickThroughRate", 0) or 0),
                    "cpc": float(data.get("costPerClick", 0) or 0),
                    "roas": float(data.get("returnOnAdSpend", 0) or 0),
                }
                return self.normalize_metrics(raw)
        except Exception as e:
            logger.error(f"LinkedIn metrics error: {e}")
            raise IntegrationError(str(e))

    async def pause_campaign(self, campaign_id: str) -> bool:
        try:
            headers = await self._get_auth_headers()
            payload = {"status": "PAUSED"}
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/adCampaignsV2/{campaign_id}", headers=headers, json=payload
                )
                return response.status_code < 300
        except Exception:
            return False

    async def activate_campaign(self, campaign_id: str) -> bool:
        try:
            headers = await self._get_auth_headers()
            payload = {"status": "ACTIVE"}
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/adCampaignsV2/{campaign_id}", headers=headers, json=payload
                )
                return response.status_code < 300
        except Exception:
            return False

    async def _get_auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}



