from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdPlatform(ABC):
    """Abstract base class for ad platform integrators"""
    
    def __init__(self, credentials: Dict):
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.replace("Connector", "").lower()
        
    @abstractmethod
    async def get_campaigns(self, account_id: str) -> List[Dict]:
        """Get all campaigns for an account"""
        pass
        
    @abstractmethod
    async def create_campaign(self, campaign_data: Dict) -> str:
        """Create a new campaign"""
        pass
        
    @abstractmethod
    async def update_campaign_budget(self, campaign_id: str, budget: float) -> bool:
        """Update campaign budget"""
        pass
        
    @abstractmethod
    async def get_performance_metrics(self, campaign_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        """Get performance metrics for a campaign"""
        pass
        
    @abstractmethod
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign"""
        pass
        
    @abstractmethod
    async def activate_campaign(self, campaign_id: str) -> bool:
        """Activate a campaign"""
        pass
    
    def normalize_metrics(self, raw_metrics: Dict) -> Dict:
        """Normalize platform-specific metrics to standard format"""
        return {
            "spend": raw_metrics.get("spend", 0.0),
            "impressions": raw_metrics.get("impressions", 0),
            "clicks": raw_metrics.get("clicks", 0),
            "conversions": raw_metrics.get("conversions", 0),
            "roas": raw_metrics.get("roas", 0.0),
            "ctr": raw_metrics.get("ctr", 0.0),
            "cpc": raw_metrics.get("cpc", 0.0),
            "platform": self.platform_name,
            "timestamp": datetime.now()
        }
    
    async def validate_credentials(self) -> bool:
        """Validate platform credentials"""
        try:
            # Basic validation - each platform should implement specific validation
            return bool(self.credentials.get("api_key") or self.credentials.get("access_token"))
        except Exception as e:
            logger.error(f"Credential validation failed for {self.platform_name}: {e}")
            return False

class IntegrationError(Exception):
    """Custom exception for integration errors"""
    pass

class RateLimitError(IntegrationError):
    """Exception for rate limit errors"""
    pass

class AuthenticationError(IntegrationError):
    """Exception for authentication errors"""
    pass
