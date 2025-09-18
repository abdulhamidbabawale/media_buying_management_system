import httpx
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.integrations.base import AdPlatform, IntegrationError, RateLimitError, AuthenticationError
import logging

logger = logging.getLogger(__name__)

class GoogleAdsConnector(AdPlatform):
    """Google Ads API connector"""
    
    def __init__(self, credentials: Dict):
        super().__init__(credentials)
        self.api_key = credentials.get("api_key")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.refresh_token = credentials.get("refresh_token")
        self.base_url = "https://googleads.googleapis.com/v14"
        
    async def get_campaigns(self, account_id: str) -> List[Dict]:
        """Get all campaigns for a Google Ads account"""
        try:
            headers = await self._get_auth_headers()
            
            # Google Ads API query to get campaigns
            query = """
                SELECT campaign.id, campaign.name, campaign.status, 
                       campaign.advertising_channel_type, campaign_budget.amount_micros
                FROM campaign
                WHERE campaign.status != 'REMOVED'
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/customers/{account_id}/googleAds:search",
                    headers=headers,
                    json={"query": query}
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Google Ads API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Google Ads API authentication failed")
                elif response.status_code != 200:
                    raise IntegrationError(f"Google Ads API error: {response.text}")
                
                data = response.json()
                campaigns = []
                
                for row in data.get("results", []):
                    campaign = row.get("campaign", {})
                    budget = row.get("campaignBudget", {})
                    
                    campaigns.append({
                        "id": campaign.get("id"),
                        "name": campaign.get("name"),
                        "status": campaign.get("status"),
                        "type": campaign.get("advertisingChannelType"),
                        "budget": float(budget.get("amountMicros", 0)) / 1_000_000,  # Convert from micros
                        "platform": "google_ads"
                    })
                
                return campaigns
                
        except Exception as e:
            logger.error(f"Error fetching Google Ads campaigns: {e}")
            raise IntegrationError(f"Failed to fetch campaigns: {str(e)}")
    
    async def create_campaign(self, campaign_data: Dict) -> str:
        """Create a new Google Ads campaign"""
        try:
            headers = await self._get_auth_headers()
            
            # Convert campaign data to Google Ads format
            google_campaign = {
                "name": campaign_data["name"],
                "advertisingChannelType": self._map_campaign_type(campaign_data.get("type", "SEARCH")),
                "status": "PAUSED",  # Start paused for safety
                "campaignBudget": {
                    "amountMicros": int(campaign_data["budget"] * 1_000_000)  # Convert to micros
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/customers/{campaign_data['account_id']}/campaigns",
                    headers=headers,
                    json=google_campaign
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Google Ads API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Google Ads API authentication failed")
                elif response.status_code != 200:
                    raise IntegrationError(f"Google Ads API error: {response.text}")
                
                result = response.json()
                return result.get("results", [{}])[0].get("resourceName", "").split("/")[-1]
                
        except Exception as e:
            logger.error(f"Error creating Google Ads campaign: {e}")
            raise IntegrationError(f"Failed to create campaign: {str(e)}")
    
    async def update_campaign_budget(self, campaign_id: str, budget: float) -> bool:
        """Update Google Ads campaign budget"""
        try:
            headers = await self._get_auth_headers()
            
            # Get current campaign to find budget resource name
            campaign = await self._get_campaign_details(campaign_id)
            budget_resource = campaign.get("campaignBudget")
            
            if not budget_resource:
                raise IntegrationError("Campaign budget not found")
            
            # Update budget
            budget_update = {
                "amountMicros": int(budget * 1_000_000)  # Convert to micros
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/{budget_resource}",
                    headers=headers,
                    json=budget_update
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Google Ads API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Google Ads API authentication failed")
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error updating Google Ads campaign budget: {e}")
            raise IntegrationError(f"Failed to update budget: {str(e)}")
    
    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        """Get Google Ads campaign performance metrics"""
        try:
            headers = await self._get_auth_headers()
            
            start_date = date_range[0].strftime("%Y-%m-%d")
            end_date = date_range[1].strftime("%Y-%m-%d")
            
            query = f"""
                SELECT segments.date, metrics.cost_micros, metrics.impressions,
                       metrics.clicks, metrics.conversions, metrics.ctr,
                       metrics.average_cpc
                FROM campaign
                WHERE campaign.id = {campaign_id}
                AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/customers/{self.client_id}/googleAds:search",
                    headers=headers,
                    json={"query": query}
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Google Ads API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Google Ads API authentication failed")
                elif response.status_code != 200:
                    raise IntegrationError(f"Google Ads API error: {response.text}")
                
                data = response.json()
                metrics = self._aggregate_metrics(data.get("results", []))
                
                return self.normalize_metrics(metrics)
                
        except Exception as e:
            logger.error(f"Error fetching Google Ads metrics: {e}")
            raise IntegrationError(f"Failed to fetch metrics: {str(e)}")
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause Google Ads campaign"""
        try:
            headers = await self._get_auth_headers()
            
            campaign_update = {
                "status": "PAUSED"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/customers/{self.client_id}/campaigns/{campaign_id}",
                    headers=headers,
                    json=campaign_update
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error pausing Google Ads campaign: {e}")
            return False
    
    async def activate_campaign(self, campaign_id: str) -> bool:
        """Activate Google Ads campaign"""
        try:
            headers = await self._get_auth_headers()
            
            campaign_update = {
                "status": "ENABLED"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/customers/{self.client_id}/campaigns/{campaign_id}",
                    headers=headers,
                    json=campaign_update
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error activating Google Ads campaign: {e}")
            return False
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Google Ads API"""
        # In a real implementation, you'd handle OAuth2 token refresh here
        return {
            "Authorization": f"Bearer {self.api_key}",
            "developer-token": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def _get_campaign_details(self, campaign_id: str) -> Dict:
        """Get detailed campaign information"""
        headers = await self._get_auth_headers()
        
        query = f"""
            SELECT campaign.id, campaign.name, campaign.campaign_budget
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/customers/{self.client_id}/googleAds:search",
                headers=headers,
                json={"query": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [{}])[0] if data.get("results") else {}
            
            return {}
    
    def _map_campaign_type(self, campaign_type: str) -> str:
        """Map internal campaign type to Google Ads type"""
        mapping = {
            "search": "SEARCH",
            "display": "DISPLAY",
            "video": "VIDEO",
            "shopping": "SHOPPING",
            "app": "APP"
        }
        return mapping.get(campaign_type.lower(), "SEARCH")
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict:
        """Aggregate daily metrics into totals"""
        total_spend = 0
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        
        for result in results:
            metrics = result.get("metrics", {})
            total_spend += float(metrics.get("costMicros", 0)) / 1_000_000
            total_impressions += int(metrics.get("impressions", 0))
            total_clicks += int(metrics.get("clicks", 0))
            total_conversions += float(metrics.get("conversions", 0))
        
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        roas = (total_conversions / total_spend) if total_spend > 0 else 0
        
        return {
            "spend": total_spend,
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "ctr": ctr,
            "cpc": cpc,
            "roas": roas
        }
