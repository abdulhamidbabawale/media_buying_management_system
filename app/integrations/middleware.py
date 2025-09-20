"""
Integration Middleware - Orchestrates API calls across platforms and integrators
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.integrations.google_ads import GoogleAdsConnector
from app.integrations.meta_ads import MetaAdsConnector
from app.integrations.base import AdPlatform, IntegrationError, RateLimitError, AuthenticationError
from app.services.integration_metrics_service import integration_metrics_service
import logging

logger = logging.getLogger(__name__)

class IntegrationMiddleware:
    """Middleware for orchestrating API calls across platforms and integrators"""
    
    def __init__(self):
        self.platforms = {}
        self.integrators = {}
        self.fallback_enabled = True
        self.rate_limit_delays = {
            "google_ads": 1.0,  # seconds
            "meta_ads": 0.5,
            "tiktok_ads": 1.5,
            "linkedin_ads": 2.0
        }
    
    def register_platform(self, platform_name: str, platform_instance: AdPlatform):
        """Register a platform connector"""
        self.platforms[platform_name] = platform_instance
        logger.info(f"Registered platform: {platform_name}")
    
    def register_integrator(self, integrator_name: str, integrator_instance):
        """Register a media buying integrator"""
        self.integrators[integrator_name] = integrator_instance
        logger.info(f"Registered integrator: {integrator_name}")
    
    async def execute_budget_change(self, campaign_id: str, new_budget: float, 
                                  platform: str, account_id: str) -> Dict:
        """
        Execute budget change with fallback strategy
        Try integrator first, fallback to direct platform API
        """
        try:
            # Try integrator first if available
            integrator_result = await self._try_integrator_budget_change(
                campaign_id, new_budget, platform, account_id
            )
            
            if integrator_result["success"]:
                logger.info(f"Budget change successful via integrator for {campaign_id}")
                return integrator_result
            
            # Fallback to direct platform API
            if self.fallback_enabled:
                logger.warning(f"Integrator failed, falling back to direct platform API for {campaign_id}")
                platform_result = await self._try_platform_budget_change(
                    campaign_id, new_budget, platform, account_id
                )
                
                if platform_result["success"]:
                    logger.info(f"Budget change successful via direct platform API for {campaign_id}")
                    return platform_result
            
            return {
                "success": False,
                "message": "Both integrator and direct platform API failed",
                "errors": [integrator_result.get("message", ""), platform_result.get("message", "")]
            }
            
        except Exception as e:
            logger.error(f"Error executing budget change for {campaign_id}: {e}")
            return {
                "success": False,
                "message": f"Budget change execution failed: {str(e)}"
            }
    
    async def aggregate_performance_data(self, campaign_id: str, platform: str, 
                                       account_id: str, date_range: Tuple[datetime, datetime]) -> Dict:
        """
        Aggregate performance data from multiple sources
        """
        try:
            aggregated_data = {
                "campaign_id": campaign_id,
                "platform": platform,
                "sources": [],
                "total_spend": 0.0,
                "total_impressions": 0,
                "total_clicks": 0,
                "total_conversions": 0,
                "data_quality_score": 0.0,
                "timestamp": datetime.now()
            }
            
            # Collect data from integrators
            integrator_data = await self._collect_integrator_data(
                campaign_id, platform, account_id, date_range
            )
            
            # Collect data from direct platform API
            platform_data = await self._collect_platform_data(
                campaign_id, platform, account_id, date_range
            )
            
            # Merge and validate data
            all_data_sources = []
            if integrator_data:
                all_data_sources.append(("integrator", integrator_data))
            if platform_data:
                all_data_sources.append(("platform", platform_data))
            
            if not all_data_sources:
                return {
                    "success": False,
                    "message": "No performance data available from any source"
                }
            
            # Persist raw and aggregate normalized metrics per source
            for source_name, data in all_data_sources:
                aggregated_data["sources"].append(source_name)
                vendor = source_name  # 'integrator' or 'platform'
                # Save raw snapshot
                await integration_metrics_service.save_raw(
                    vendor=vendor,
                    campaign_id=campaign_id,
                    platform=platform,
                    account_id=account_id,
                    payload=data,
                    date_range=date_range,
                )
                # Normalize and persist
                normalized = integration_metrics_service.normalize_payload(
                    vendor=vendor,
                    payload=data,
                    campaign_id=campaign_id,
                    platform=platform,
                    account_id=account_id,
                    date_range=date_range,
                )
                await integration_metrics_service.save_normalized(normalized)
                # Use normalized values for aggregation
                aggregated_data["total_spend"] += normalized.spend
                aggregated_data["total_impressions"] += normalized.impressions
                aggregated_data["total_clicks"] += normalized.clicks
                aggregated_data["total_conversions"] += normalized.conversions
            
            # Calculate data quality score
            aggregated_data["data_quality_score"] = self._calculate_data_quality_score(all_data_sources)
            
            # Calculate derived metrics
            aggregated_data["avg_roas"] = (
                aggregated_data["total_conversions"] / aggregated_data["total_spend"]
                if aggregated_data["total_spend"] > 0 else 0.0
            )
            aggregated_data["avg_ctr"] = (
                aggregated_data["total_clicks"] / aggregated_data["total_impressions"] * 100
                if aggregated_data["total_impressions"] > 0 else 0.0
            )
            aggregated_data["avg_cpc"] = (
                aggregated_data["total_spend"] / aggregated_data["total_clicks"]
                if aggregated_data["total_clicks"] > 0 else 0.0
            )
            
            return {
                "success": True,
                "data": aggregated_data
            }
            
        except Exception as e:
            logger.error(f"Error aggregating performance data for {campaign_id}: {e}")
            return {
                "success": False,
                "message": f"Performance data aggregation failed: {str(e)}"
            }
    
    async def create_campaign_with_fallback(self, campaign_data: Dict, platform: str, 
                                          account_id: str) -> Dict:
        """
        Create campaign with fallback strategy
        """
        try:
            # Try integrator first
            integrator_result = await self._try_integrator_campaign_creation(
                campaign_data, platform, account_id
            )
            
            if integrator_result["success"]:
                return integrator_result
            
            # Fallback to direct platform API
            if self.fallback_enabled:
                platform_result = await self._try_platform_campaign_creation(
                    campaign_data, platform, account_id
                )
                
                if platform_result["success"]:
                    return platform_result
            
            return {
                "success": False,
                "message": "Campaign creation failed on all platforms"
            }
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return {
                "success": False,
                "message": f"Campaign creation failed: {str(e)}"
            }
    
    async def pause_campaign_with_fallback(self, campaign_id: str, platform: str, 
                                         account_id: str) -> Dict:
        """Pause campaign with fallback strategy"""
        try:
            # Try integrator first
            integrator_result = await self._try_integrator_campaign_pause(
                campaign_id, platform, account_id
            )
            
            if integrator_result["success"]:
                return integrator_result
            
            # Fallback to direct platform API
            if self.fallback_enabled:
                platform_result = await self._try_platform_campaign_pause(
                    campaign_id, platform, account_id
                )
                
                if platform_result["success"]:
                    return platform_result
            
            return {
                "success": False,
                "message": "Campaign pause failed on all platforms"
            }
            
        except Exception as e:
            logger.error(f"Error pausing campaign {campaign_id}: {e}")
            return {
                "success": False,
                "message": f"Campaign pause failed: {str(e)}"
            }
    
    async def _try_integrator_budget_change(self, campaign_id: str, new_budget: float, 
                                          platform: str, account_id: str) -> Dict:
        """Try budget change via integrator"""
        for integrator_name, integrator in self.integrators.items():
            try:
                if hasattr(integrator, 'update_campaign_budget'):
                    success = await integrator.update_campaign_budget(campaign_id, new_budget)
                    if success:
                        return {
                            "success": True,
                            "source": integrator_name,
                            "message": f"Budget updated via {integrator_name}"
                        }
            except Exception as e:
                logger.warning(f"Integrator {integrator_name} failed: {e}")
                continue
        
        return {"success": False, "message": "All integrators failed"}
    
    async def _try_platform_budget_change(self, campaign_id: str, new_budget: float, 
                                        platform: str, account_id: str) -> Dict:
        """Try budget change via direct platform API"""
        if platform not in self.platforms:
            return {"success": False, "message": f"Platform {platform} not available"}
        
        try:
            platform_connector = self.platforms[platform]
            # basic retry/backoff
            attempts = 0
            while attempts < 3:
                success = await platform_connector.update_campaign_budget(campaign_id, new_budget)
                if success:
                    break
                await asyncio.sleep((attempts + 1) * 0.5)
                attempts += 1
            
            if success:
                return {
                    "success": True,
                    "source": f"direct_{platform}",
                    "message": f"Budget updated via direct {platform} API"
                }
            else:
                return {"success": False, "message": f"Direct {platform} API failed"}
                
        except RateLimitError:
            # Implement rate limiting delay
            delay = self.rate_limit_delays.get(platform, 1.0)
            await asyncio.sleep(delay)
            return {"success": False, "message": f"Rate limited on {platform}"}
        except Exception as e:
            return {"success": False, "message": f"Direct {platform} API error: {str(e)}"}
    
    async def _collect_integrator_data(self, campaign_id: str, platform: str, 
                                     account_id: str, date_range: Tuple[datetime, datetime]) -> Optional[Dict]:
        """Collect performance data from integrators"""
        for integrator_name, integrator in self.integrators.items():
            try:
                if hasattr(integrator, 'get_performance_metrics'):
                    data = await integrator.get_performance_metrics(campaign_id, date_range)
                    if data:
                        return data
            except Exception as e:
                logger.warning(f"Integrator {integrator_name} data collection failed: {e}")
                continue
        
        return None
    
    async def _collect_platform_data(self, campaign_id: str, platform: str, 
                                   account_id: str, date_range: Tuple[datetime, datetime]) -> Optional[Dict]:
        """Collect performance data from direct platform API"""
        if platform not in self.platforms:
            return None
        
        try:
            platform_connector = self.platforms[platform]
            attempts = 0
            data = None
            while attempts < 3 and not data:
                data = await platform_connector.get_performance_metrics(campaign_id, date_range)
                if data:
                    break
                await asyncio.sleep((attempts + 1) * 0.5)
                attempts += 1
            return data
        except Exception as e:
            logger.warning(f"Platform {platform} data collection failed: {e}")
            return None
    
    async def _try_integrator_campaign_creation(self, campaign_data: Dict, platform: str, 
                                              account_id: str) -> Dict:
        """Try campaign creation via integrator"""
        for integrator_name, integrator in self.integrators.items():
            try:
                if hasattr(integrator, 'create_campaign'):
                    campaign_id = await integrator.create_campaign(campaign_data)
                    if campaign_id:
                        return {
                            "success": True,
                            "source": integrator_name,
                            "campaign_id": campaign_id,
                            "message": f"Campaign created via {integrator_name}"
                        }
            except Exception as e:
                logger.warning(f"Integrator {integrator_name} campaign creation failed: {e}")
                continue
        
        return {"success": False, "message": "All integrators failed"}
    
    async def _try_platform_campaign_creation(self, campaign_data: Dict, platform: str, 
                                            account_id: str) -> Dict:
        """Try campaign creation via direct platform API"""
        if platform not in self.platforms:
            return {"success": False, "message": f"Platform {platform} not available"}
        
        try:
            platform_connector = self.platforms[platform]
            campaign_id = await platform_connector.create_campaign(campaign_data)
            
            if campaign_id:
                return {
                    "success": True,
                    "source": f"direct_{platform}",
                    "campaign_id": campaign_id,
                    "message": f"Campaign created via direct {platform} API"
                }
            else:
                return {"success": False, "message": f"Direct {platform} API failed"}
                
        except Exception as e:
            return {"success": False, "message": f"Direct {platform} API error: {str(e)}"}
    
    async def _try_integrator_campaign_pause(self, campaign_id: str, platform: str, 
                                           account_id: str) -> Dict:
        """Try campaign pause via integrator"""
        for integrator_name, integrator in self.integrators.items():
            try:
                if hasattr(integrator, 'pause_campaign'):
                    success = await integrator.pause_campaign(campaign_id)
                    if success:
                        return {
                            "success": True,
                            "source": integrator_name,
                            "message": f"Campaign paused via {integrator_name}"
                        }
            except Exception as e:
                logger.warning(f"Integrator {integrator_name} campaign pause failed: {e}")
                continue
        
        return {"success": False, "message": "All integrators failed"}
    
    async def _try_platform_campaign_pause(self, campaign_id: str, platform: str, 
                                         account_id: str) -> Dict:
        """Try campaign pause via direct platform API"""
        if platform not in self.platforms:
            return {"success": False, "message": f"Platform {platform} not available"}
        
        try:
            platform_connector = self.platforms[platform]
            success = await platform_connector.pause_campaign(campaign_id)
            
            if success:
                return {
                    "success": True,
                    "source": f"direct_{platform}",
                    "message": f"Campaign paused via direct {platform} API"
                }
            else:
                return {"success": False, "message": f"Direct {platform} API failed"}
                
        except Exception as e:
            return {"success": False, "message": f"Direct {platform} API error: {str(e)}"}
    
    def _calculate_data_quality_score(self, data_sources: List[Tuple[str, Dict]]) -> float:
        """Calculate data quality score based on source consistency"""
        if not data_sources:
            return 0.0
        
        if len(data_sources) == 1:
            return 0.8  # Single source gets 80% quality score
        
        # Compare data consistency across sources
        source_data = [data for _, data in data_sources]
        
        # Calculate variance in key metrics
        spend_values = [data.get("spend", 0) for data in source_data]
        impression_values = [data.get("impressions", 0) for data in source_data]
        
        # Simple variance calculation
        spend_variance = self._calculate_variance(spend_values)
        impression_variance = self._calculate_variance(impression_values)
        
        # Lower variance = higher quality score
        quality_score = max(0.0, 1.0 - (spend_variance + impression_variance) / 2)
        
        return min(quality_score, 1.0)
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance / (mean ** 2) if mean != 0 else 0.0  # Coefficient of variation

# Global middleware instance
integration_middleware = IntegrationMiddleware()
