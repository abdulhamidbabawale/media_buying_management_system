import httpx
from typing import Dict, Tuple,Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseIntegrator:
    def __init__(self, credentials: Dict):
        self.credentials = credentials

    async def update_campaign_budget(self, campaign_id: str, new_budget: float) -> bool:
        raise NotImplementedError

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        raise NotImplementedError



class AdRollConnector(BaseIntegrator):
    def __init__(self, credentials: Dict = None):
        super().__init__(credentials or {})
        creds = credentials or {}
        # Auth modes: 'pat' (Personal Access Token) or 'oauth'
        self.auth_mode = creds.get("auth_mode", "pat")
        self.pat_token = creds.get("pat_token", "")  # used when auth_mode == 'pat'
        self.client_id = creds.get("client_id", "")  # apikey param for PAT
        self.access_token = creds.get("access_token", "")  # used when auth_mode == 'oauth'
        self.base_url = creds.get("base_url", "https://services.adroll.com")
        # Budget level preference: 'strategy' (recommended) or 'campaign'
        self.budget_level = creds.get("budget_level", "strategy")

    def _auth_headers_and_url(self, path: str) -> Tuple[Dict, str]:
        """Build headers and URL (with apikey for PAT)."""
        url = f"{self.base_url}{path}"
        if self.auth_mode == "pat":
            headers = {"Authorization": f"Token {self.pat_token}"}
            if self.client_id:
                sep = "&" if ("?" in url) else "?"
                url = f"{url}{sep}apikey={self.client_id}"
            return headers, url
        # oauth
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return headers, url

    async def update_campaign_budget(self, campaign_or_strategy_id: str, new_budget: float) -> bool:
        """
        Update budget for AdRoll. Prefer strategy-level budgets. If strategy update fails,
        try campaign-level daily_budget edit. Caller should pass a strategy EID when using
        strategy-level updates, or a campaign EID when using campaign-level updates.
        """
        # Attempt strategy-level budget update first when preferred
        if self.budget_level == "strategy":
            try:
                headers, url = self._auth_headers_and_url("/activate/api/v3/strategy")
                # StrategyEdit via PUT requires EID in body (per docs variants)
                payload = {
                    "eid": campaign_or_strategy_id,
                    "budget": {"type": "daily", "goal": float(new_budget)}
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.put(url, headers=headers, json=payload)
                    if resp.status_code < 300:
                        return True
            except Exception:
                pass

        # Fallback to campaign-level daily_budget update
        try:
            headers, url = self._auth_headers_and_url("/activate/api/v3/campaign")
            payload = {
                "eid": campaign_or_strategy_id,
                "daily_budget": float(new_budget)
            }
            async with httpx.AsyncClient() as client:
                resp = await client.put(url, headers=headers, json=payload)
                return resp.status_code < 300
        except Exception:
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        # Metrics endpoint details vary; placeholder implementation until exact spec is confirmed.
        try:
            headers, url = self._auth_headers_and_url("/activate/api/v3/campaign")
            # Placeholder: in practice, use the documented reporting endpoint with proper params
            params = {
                "eid": campaign_id,
                "start": date_range[0].strftime("%Y-%m-%dT%H:%M:%S"),
                "end": date_range[1].strftime("%Y-%m-%dT%H:%M:%S"),
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code >= 300:
                    return {}
                return resp.json() or {}
        except Exception:
            return {}

    async def create_campaign(self, campaign_data: Dict) -> Optional[str]:
        """
        Create an AdRoll campaign under a strategy.
        Expects campaign_data to contain:
          - strategy_eid: str
          - campaign: dict (matching one of AdRoll's create schemas, e.g., WebRetargetingCampaignCreate)
        Returns the created campaign EID on success, otherwise None.
        """
        try:
            strategy_eid = campaign_data.get("strategy_eid")
            body = campaign_data.get("campaign", campaign_data)
            if not strategy_eid or not isinstance(body, dict):
                return None
            # POST /activate/api/v3/campaign?strategy_eid=...
            path = f"/activate/api/v3/campaign?strategy_eid={strategy_eid}"
            headers, url = self._auth_headers_and_url(path)
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code >= 300:
                    return None
                data = resp.json() or {}
                # Try to extract the created campaign EID from common response shapes
                # Prefer top-level 'eid'; otherwise check nested structures
                campaign_eid = data.get("eid")
                if not campaign_eid and isinstance(data, dict):
                    # Some responses may wrap the campaign
                    for key in ("campaign", "data", "result"):
                        inner = data.get(key)
                        if isinstance(inner, dict) and inner.get("eid"):
                            campaign_eid = inner.get("eid")
                            break
                return campaign_eid or ""
        except Exception:
            return None


class StackAdaptConnector(BaseIntegrator):
    def __init__(self, credentials: Dict = None):
        super().__init__(credentials or {})
        self.api_key = (credentials or {}).get("api_key", "")
        self.base_url = "https://api.stackadapt.com"

    async def update_campaign_budget(self, campaign_id: str, new_budget: float) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{self.base_url}/campaigns/{campaign_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"daily_budget": new_budget}
                )
                return resp.status_code < 300
        except Exception:
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/reports/campaigns/{campaign_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "start_date": date_range[0].strftime("%Y-%m-%d"),
                        "end_date": date_range[1].strftime("%Y-%m-%d")
                    }
                )
                if resp.status_code >= 300:
                    return {}
                return resp.json() or {}
        except Exception:
            return {}


class AdEspressoConnector(BaseIntegrator):
    def __init__(self, credentials: Dict = None):
        super().__init__(credentials or {})
        self.api_key = (credentials or {}).get("api_key", "")
        self.base_url = "https://api.adespresso.com/v1"

    async def update_campaign_budget(self, campaign_id: str, new_budget: float) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/campaigns/{campaign_id}/budget",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"budget": new_budget}
                )
                return resp.status_code < 300
        except Exception:
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/campaigns/{campaign_id}/metrics",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "from": date_range[0].isoformat(),
                        "to": date_range[1].isoformat()
                    }
                )
                if resp.status_code >= 300:
                    return {}
                return resp.json() or {}
        except Exception:
            return {}


class MadgicxConnector(BaseIntegrator):
    def __init__(self, credentials: Dict = None):
        super().__init__(credentials or {})
        self.api_key = (credentials or {}).get("api_key", "")
        self.base_url = "https://api.madgicx.com/v1"

    async def update_campaign_budget(self, campaign_id: str, new_budget: float) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/campaigns/{campaign_id}/budget",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"budget": new_budget}
                )
                return resp.status_code < 300
        except Exception:
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/campaigns/{campaign_id}/metrics",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "start": date_range[0].isoformat(),
                        "end": date_range[1].isoformat()
                    }
                )
                if resp.status_code >= 300:
                    return {}
                return resp.json() or {}
        except Exception:
            return {}



