import httpx
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.integrations.base import AdPlatform, IntegrationError, RateLimitError, AuthenticationError
import logging

logger = logging.getLogger(__name__)

class MetaAdsConnector(AdPlatform):
    """Meta Marketing API connector"""
    
    def __init__(self, credentials: Dict):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.app_id = credentials.get("app_id")
        self.app_secret = credentials.get("app_secret")
        self.base_url = "https://graph.facebook.com/v18.0"
        
    async def get_campaigns(self, account_id: str) -> List[Dict]:
        """Get all campaigns for a Meta ad account"""
        try:
            headers = await self._get_auth_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/act_{account_id}/campaigns",
                    headers=headers,
                    params={
                        "fields": "id,name,status,objective,effective_status,daily_budget,lifetime_budget",
                        "limit": 100
                    }
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Meta API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Meta API authentication failed")
                elif response.status_code != 200:
                    raise IntegrationError(f"Meta API error: {response.text}")
                
                data = response.json()
                campaigns = []
                
                for campaign in data.get("data", []):
                    # Determine budget (daily or lifetime)
                    budget = campaign.get("daily_budget") or campaign.get("lifetime_budget", 0)
                    if budget:
                        budget = float(budget) / 100  # Convert from cents
                    
                    campaigns.append({
                        "id": campaign.get("id"),
                        "name": campaign.get("name"),
                        "status": campaign.get("status"),
                        "objective": campaign.get("objective"),
                        "budget": budget,
                        "platform": "meta_ads"
                    })
                
                return campaigns
                
        except Exception as e:
            logger.error(f"Error fetching Meta campaigns: {e}")
            raise IntegrationError(f"Failed to fetch campaigns: {str(e)}")
    
    async def create_campaign(self, campaign_data: Dict) -> str:
        """Create a new Meta campaign"""
        try:
            headers = await self._get_auth_headers()
            
            # Convert campaign data to Meta format
            meta_campaign = {
                "name": campaign_data["name"],
                "objective": self._map_campaign_objective(campaign_data.get("objective", "TRAFFIC")),
                "status": "PAUSED",  # Start paused for safety
                "special_ad_categories": []
            }
            
            # Add budget based on type
            if campaign_data.get("budget_type") == "daily":
                meta_campaign["daily_budget"] = int(campaign_data["budget"] * 100)  # Convert to cents
            else:
                meta_campaign["lifetime_budget"] = int(campaign_data["budget"] * 100)  # Convert to cents
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/act_{campaign_data['account_id']}/campaigns",
                    headers=headers,
                    json=meta_campaign
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Meta API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Meta API authentication failed")
                elif response.status_code != 200:
                    raise IntegrationError(f"Meta API error: {response.text}")
                
                result = response.json()
                return result.get("id")
                
        except Exception as e:
            logger.error(f"Error creating Meta campaign: {e}")
            raise IntegrationError(f"Failed to create campaign: {str(e)}")
    
    async def update_campaign_budget(self, campaign_id: str, budget: float) -> bool:
        """Update Meta campaign budget"""
        try:
            headers = await self._get_auth_headers()
            
            # Get current campaign to determine budget type
            campaign = await self._get_campaign_details(campaign_id)
            budget_type = "daily" if campaign.get("daily_budget") else "lifetime"
            
            # Update budget
            budget_update = {}
            if budget_type == "daily":
                budget_update["daily_budget"] = int(budget * 100)  # Convert to cents
            else:
                budget_update["lifetime_budget"] = int(budget * 100)  # Convert to cents
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{campaign_id}",
                    headers=headers,
                    json=budget_update
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Meta API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Meta API authentication failed")
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error updating Meta campaign budget: {e}")
            raise IntegrationError(f"Failed to update budget: {str(e)}")
    
    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        """Get Meta campaign performance metrics"""
        try:
            headers = await self._get_auth_headers()
            
            start_date = date_range[0].strftime("%Y-%m-%d")
            end_date = date_range[1].strftime("%Y-%m-%d")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{campaign_id}/insights",
                    headers=headers,
                    params={
                        "fields": "spend,impressions,clicks,conversions,ctr,cpc,actions",
                        "time_range": f"{{'since':'{start_date}','until':'{end_date}'}}",
                        "level": "campaign"
                    }
                )
                
                if response.status_code == 429:
                    raise RateLimitError("Meta API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Meta API authentication failed")
                elif response.status_code != 200:
                    raise IntegrationError(f"Meta API error: {response.text}")
                
                data = response.json()
                metrics = self._process_insights(data.get("data", []))
                
                return self.normalize_metrics(metrics)
                
        except Exception as e:
            logger.error(f"Error fetching Meta metrics: {e}")
            raise IntegrationError(f"Failed to fetch metrics: {str(e)}")
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause Meta campaign"""
        try:
            headers = await self._get_auth_headers()
            
            campaign_update = {
                "status": "PAUSED"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{campaign_id}",
                    headers=headers,
                    json=campaign_update
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error pausing Meta campaign: {e}")
            return False
    
    async def activate_campaign(self, campaign_id: str) -> bool:
        """Activate Meta campaign"""
        try:
            headers = await self._get_auth_headers()
            
            campaign_update = {
                "status": "ACTIVE"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{campaign_id}",
                    headers=headers,
                    json=campaign_update
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error activating Meta campaign: {e}")
            return False
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Meta API"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def _get_campaign_details(self, campaign_id: str) -> Dict:
        """Get detailed campaign information"""
        headers = await self._get_auth_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{campaign_id}",
                headers=headers,
                params={
                    "fields": "id,name,status,daily_budget,lifetime_budget,objective"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            
            return {}
    
    def _map_campaign_objective(self, objective: str) -> str:
        """Map internal objective to Meta objective"""
        mapping = {
            "traffic": "TRAFFIC",
            "conversions": "CONVERSIONS",
            "awareness": "BRAND_AWARENESS",
            "reach": "REACH",
            "engagement": "POST_ENGAGEMENT",
            "app_installs": "APP_INSTALLS",
            "video_views": "VIDEO_VIEWS",
            "lead_generation": "LEAD_GENERATION"
        }
        return mapping.get(objective.lower(), "TRAFFIC")
    
    def _process_insights(self, insights_data: List[Dict]) -> Dict:
        """Process Meta insights data"""
        if not insights_data:
            return {
                "spend": 0.0,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "ctr": 0.0,
                "cpc": 0.0,
                "roas": 0.0
            }
        
        insight = insights_data[0]  # Meta returns array with single insight
        
        # Extract conversions from actions
        conversions = 0
        actions = insight.get("actions", [])
        for action in actions:
            if action.get("action_type") in ["purchase", "complete_registration", "add_to_cart"]:
                conversions += int(action.get("value", 0))
        
        spend = float(insight.get("spend", 0))
        impressions = int(insight.get("impressions", 0))
        clicks = int(insight.get("clicks", 0))
        ctr = float(insight.get("ctr", 0))
        cpc = float(insight.get("cpc", 0))
        roas = (conversions / spend) if spend > 0 else 0
        
        return {
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": ctr,
            "cpc": cpc,
            "roas": roas
        }
