import httpx
from typing import Dict, List, Tuple
from datetime import datetime
from app.integrations.base import AdPlatform, IntegrationError, RateLimitError, AuthenticationError
import logging

logger = logging.getLogger(__name__)


class TikTokAdsConnector(AdPlatform):
    """TikTok Ads API connector (scaffold with basic behavior)."""

    def __init__(self, credentials: Dict):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.advertiser_id = credentials.get("advertiser_id")
        self.base_url = "https://business-api.tiktok.com/open_api/v1.3"

    async def get_campaigns(self, account_id: str) -> List[Dict]:
        try:
            headers = await self._get_auth_headers()
            async with httpx.AsyncClient() as client:
                # TikTok campaign list endpoint (placeholder path)
                response = await client.get(
                    f"{self.base_url}/campaign/get/",
                    headers=headers,
                    params={"advertiser_id": self.advertiser_id, "page_size": 100}
                )
                if response.status_code == 429:
                    raise RateLimitError("TikTok API rate limit exceeded")
                if response.status_code == 401:
                    raise AuthenticationError("TikTok API authentication failed")
                if response.status_code != 200:
                    raise IntegrationError(f"TikTok API error: {response.text}")

                data = response.json().get("data", {})
                campaigns = []
                for c in data.get("list", []):
                    campaigns.append({
                        "id": c.get("campaign_id"),
                        "name": c.get("campaign_name"),
                        "status": c.get("operation_status"),
                        "budget": float(c.get("budget", 0) or 0),
                        "platform": "tiktok_ads"
                    })
                return campaigns
        except Exception as e:
            logger.error(f"Error fetching TikTok campaigns: {e}")
            raise IntegrationError(str(e))

    async def create_campaign(self, campaign_data: Dict) -> str:
        try:
            headers = await self._get_auth_headers()
            payload = {
                "advertiser_id": self.advertiser_id,
                "campaign_name": campaign_data.get("name"),
                "objective_type": campaign_data.get("objective", "TRAFFIC"),
                "budget": campaign_data.get("budget", 0),
                "operation_status": "PAUSED"
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/campaign/create/", headers=headers, json=payload
                )
                if response.status_code >= 300:
                    raise IntegrationError(f"TikTok create error: {response.text}")
                return response.json().get("data", {}).get("campaign_id", "")
        except Exception as e:
            logger.error(f"Error creating TikTok campaign: {e}")
            raise IntegrationError(str(e))

    async def update_campaign_budget(self, campaign_id: str, budget: float) -> bool:
        try:
            headers = await self._get_auth_headers()
            payload = {
                "advertiser_id": self.advertiser_id,
                "campaign_id": campaign_id,
                "budget": budget
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/campaign/update/", headers=headers, json=payload
                )
                return response.status_code < 300
        except Exception as e:
            logger.error(f"TikTok budget update error: {e}")
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        try:
            headers = await self._get_auth_headers()
            start_date = date_range[0].strftime("%Y-%m-%d")
            end_date = date_range[1].strftime("%Y-%m-%d")
            params = {
                "advertiser_id": self.advertiser_id,
                "campaign_id": campaign_id,
                "start_date": start_date,
                "end_date": end_date
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/report/integrated/get/", headers=headers, params=params
                )
                if response.status_code >= 300:
                    raise IntegrationError(f"TikTok metrics error: {response.text}")
                data = response.json().get("data", {}).get("list", [{}])[0]
                raw = {
                    "spend": float(data.get("spend", 0) or 0),
                    "impressions": int(data.get("impressions", 0) or 0),
                    "clicks": int(data.get("clicks", 0) or 0),
                    "conversions": int(data.get("conversions", 0) or 0),
                    "ctr": float(data.get("ctr", 0) or 0),
                    "cpc": float(data.get("cpc", 0) or 0),
                    "roas": float(data.get("roas", 0) or 0)
                }
                return self.normalize_metrics(raw)
        except Exception as e:
            logger.error(f"Error fetching TikTok metrics: {e}")
            raise IntegrationError(str(e))

    async def pause_campaign(self, campaign_id: str) -> bool:
        try:
            headers = await self._get_auth_headers()
            payload = {"advertiser_id": self.advertiser_id, "campaign_id": campaign_id, "operation_status": "PAUSED"}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/campaign/update/", headers=headers, json=payload
                )
                return response.status_code < 300
        except Exception:
            return False

    async def activate_campaign(self, campaign_id: str) -> bool:
        try:
            headers = await self._get_auth_headers()
            payload = {"advertiser_id": self.advertiser_id, "campaign_id": campaign_id, "operation_status": "ENABLE"}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/campaign/update/", headers=headers, json=payload
                )
                return response.status_code < 300
        except Exception:
            return False

    async def _get_auth_headers(self) -> Dict[str, str]:
        return {"Access-Token": self.access_token, "Content-Type": "application/json"}



