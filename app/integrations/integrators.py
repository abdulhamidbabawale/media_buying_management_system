import httpx
from typing import Dict, Tuple
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


class RevealBotConnector(BaseIntegrator):
    def __init__(self, credentials: Dict = None):
        super().__init__(credentials or {})
        self.api_key = (credentials or {}).get("api_key", "")
        self.base_url = "https://api.revealbot.com/v1"

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


class AdRollConnector(BaseIntegrator):
    def __init__(self, credentials: Dict = None):
        super().__init__(credentials or {})
        self.access_token = (credentials or {}).get("access_token", "")
        self.base_url = "https://services.adroll.com/api/v1"

    async def update_campaign_budget(self, campaign_id: str, new_budget: float) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/campaign/{campaign_id}/budget",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json={"budget": new_budget}
                )
                return resp.status_code < 300
        except Exception:
            return False

    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/campaign/{campaign_id}/metrics",
                    headers={"Authorization": f"Bearer {self.access_token}"},
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



