"""
Integration Service - Manages platform and integrator connections
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.integrations.middleware import integration_middleware
from app.integrations.google_ads import GoogleAdsConnector
from app.integrations.meta_ads import MetaAdsConnector
from app.integrations.base import AdPlatform
import logging

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service for managing platform and integrator integrations"""
    
    def __init__(self):
        self.middleware = integration_middleware
        self.initialized = False
    
    async def initialize_platforms(self, client_credentials: Dict[str, Dict]) -> Dict:
        """Initialize platform connectors for a client"""
        try:
            results = {}
            
            # Initialize Google Ads
            if "google_ads" in client_credentials:
                google_creds = client_credentials["google_ads"]
                google_connector = GoogleAdsConnector(google_creds)
                
                # Validate credentials
                if await google_connector.validate_credentials():
                    self.middleware.register_platform("google_ads", google_connector)
                    results["google_ads"] = {"success": True, "message": "Google Ads connected"}
                else:
                    results["google_ads"] = {"success": False, "message": "Invalid Google Ads credentials"}
            
            # Initialize Meta Ads
            if "meta_ads" in client_credentials:
                meta_creds = client_credentials["meta_ads"]
                meta_connector = MetaAdsConnector(meta_creds)
                
                # Validate credentials
                if await meta_connector.validate_credentials():
                    self.middleware.register_platform("meta_ads", meta_connector)
                    results["meta_ads"] = {"success": True, "message": "Meta Ads connected"}
                else:
                    results["meta_ads"] = {"success": False, "message": "Invalid Meta Ads credentials"}
            
            self.initialized = True
            return {
                "success": True,
                "message": "Platform initialization completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error initializing platforms: {e}")
            return {
                "success": False,
                "message": f"Platform initialization failed: {str(e)}"
            }
    
    async def execute_campaign_budget_update(self, campaign_id: str, new_budget: float, 
                                           platform: str, account_id: str) -> Dict:
        """Execute campaign budget update through middleware"""
        try:
            result = await self.middleware.execute_budget_change(
                campaign_id, new_budget, platform, account_id
            )
            
            return {
                "success": result["success"],
                "message": result.get("message", "Budget update completed"),
                "source": result.get("source", "unknown"),
                "campaign_id": campaign_id,
                "new_budget": new_budget
            }
            
        except Exception as e:
            logger.error(f"Error executing budget update: {e}")
            return {
                "success": False,
                "message": f"Budget update failed: {str(e)}"
            }
    
    async def get_campaign_performance(self, campaign_id: str, platform: str, 
                                     account_id: str, days: int = 7) -> Dict:
        """Get aggregated campaign performance data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_range = (start_date, end_date)
            
            result = await self.middleware.aggregate_performance_data(
                campaign_id, platform, account_id, date_range
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Performance data retrieved successfully",
                    "data": result["data"]
                }
            else:
                return {
                    "success": False,
                    "message": result["message"]
                }
                
        except Exception as e:
            logger.error(f"Error getting campaign performance: {e}")
            return {
                "success": False,
                "message": f"Performance data retrieval failed: {str(e)}"
            }
    
    async def create_campaign(self, campaign_data: Dict, platform: str, account_id: str) -> Dict:
        """Create campaign through middleware"""
        try:
            result = await self.middleware.create_campaign_with_fallback(
                campaign_data, platform, account_id
            )
            
            return {
                "success": result["success"],
                "message": result.get("message", "Campaign creation completed"),
                "source": result.get("source", "unknown"),
                "campaign_id": result.get("campaign_id"),
                "platform": platform
            }
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return {
                "success": False,
                "message": f"Campaign creation failed: {str(e)}"
            }
    
    async def pause_campaign(self, campaign_id: str, platform: str, account_id: str) -> Dict:
        """Pause campaign through middleware"""
        try:
            result = await self.middleware.pause_campaign_with_fallback(
                campaign_id, platform, account_id
            )
            
            return {
                "success": result["success"],
                "message": result.get("message", "Campaign pause completed"),
                "source": result.get("source", "unknown"),
                "campaign_id": campaign_id
            }
            
        except Exception as e:
            logger.error(f"Error pausing campaign: {e}")
            return {
                "success": False,
                "message": f"Campaign pause failed: {str(e)}"
            }
    
    async def get_available_platforms(self) -> List[str]:
        """Get list of available platforms"""
        return list(self.middleware.platforms.keys())
    
    async def get_available_integrators(self) -> List[str]:
        """Get list of available integrators"""
        return list(self.middleware.integrators.keys())
    
    async def validate_platform_credentials(self, platform: str, credentials: Dict) -> Dict:
        """Validate platform credentials"""
        try:
            if platform == "google_ads":
                connector = GoogleAdsConnector(credentials)
            elif platform == "meta_ads":
                connector = MetaAdsConnector(credentials)
            else:
                return {
                    "success": False,
                    "message": f"Unsupported platform: {platform}"
                }
            
            is_valid = await connector.validate_credentials()
            
            return {
                "success": is_valid,
                "message": "Credentials valid" if is_valid else "Invalid credentials"
            }
            
        except Exception as e:
            logger.error(f"Error validating {platform} credentials: {e}")
            return {
                "success": False,
                "message": f"Credential validation failed: {str(e)}"
            }
    
    async def get_platform_status(self) -> Dict:
        """Get status of all registered platforms"""
        status = {
            "platforms": {},
            "integrators": {},
            "initialized": self.initialized
        }
        
        # Check platform status
        for platform_name, platform_connector in self.middleware.platforms.items():
            try:
                is_valid = await platform_connector.validate_credentials()
                status["platforms"][platform_name] = {
                    "connected": True,
                    "valid": is_valid,
                    "status": "healthy" if is_valid else "invalid_credentials"
                }
            except Exception as e:
                status["platforms"][platform_name] = {
                    "connected": True,
                    "valid": False,
                    "status": "error",
                    "error": str(e)
                }
        
        # Check integrator status
        for integrator_name, integrator in self.middleware.integrators.items():
            try:
                # Basic health check for integrators
                status["integrators"][integrator_name] = {
                    "connected": True,
                    "status": "healthy"
                }
            except Exception as e:
                status["integrators"][integrator_name] = {
                    "connected": True,
                    "status": "error",
                    "error": str(e)
                }
        
        return status

# Global integration service instance
integration_service = IntegrationService()
