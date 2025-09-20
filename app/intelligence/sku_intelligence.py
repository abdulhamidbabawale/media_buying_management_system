"""
SKU Intelligence Engine - Core decision making logic
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.intelligence.config import MVP_CONFIG, PLATFORM_CONFIGS, RISK_MANAGEMENT_CONFIG
from app.db.campaign_queries import get_campaigns_by_sku, update_campaign_budget, pause_campaign, activate_campaign
from app.db.sku_queries import get_sku_by_id, update_sku
from app.db.connection import db
import logging

logger = logging.getLogger(__name__)

class SKUIntelligence:
    """Core intelligence engine for SKU-level optimization"""
    
    def __init__(self, config: Dict = None):
        self.config = config or MVP_CONFIG
        # Defer Motor collection access to runtime to avoid binding to a closed loop in tests
        
    @property
    def performance_collection(self):
        return db.performance_metrics

    @property
    def decisions_collection(self):
        return db.intelligence_decisions

    async def make_hourly_decisions(self, sku_id: str) -> Dict:
        """Main decision-making process for a SKU"""
        try:
            # Get current SKU data
            sku = await get_sku_by_id(sku_id)
            if not sku:
                return {"success": False, "message": "SKU not found"}
            
            # Get current performance data
            performance = await self.get_sku_performance(sku_id)
            
            # Determine mode (explore vs exploit)
            mode = await self.determine_mode(sku_id, performance)
            
            # Make budget allocation decisions
            if mode == "explore":
                decisions = await self.explore_mode_decisions(sku_id, performance)
            else:
                decisions = await self.exploit_mode_decisions(sku_id, performance)
            
            # Execute decisions
            execution_results = await self.execute_decisions(decisions)
            
            # Log decisions
            await self.log_decisions(sku_id, sku["client_id"], decisions, mode, execution_results)
            
            return {
                "success": True,
                "mode": mode,
                "decisions": decisions,
                "execution_results": execution_results
            }
            
        except Exception as e:
            logger.error(f"Error in SKU intelligence for {sku_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def determine_mode(self, sku_id: str, performance: Dict) -> str:
        """
        Determine EXPLORE vs EXPLOIT mode based on performance data
        """
        campaign_age = performance.get('days_running', 0)
        data_confidence = performance.get('confidence_score', 0.0)
        total_impressions = performance.get('total_impressions', 0)
        avg_roas = performance.get('avg_roas', 0.0)
        
        # Always explore for new campaigns
        if campaign_age < self.config['explore_mode_duration_days']:
            return "explore"
        
        # Check impression threshold
        if total_impressions < self.config['impression_threshold']:
            return "explore"
        
        # Switch to exploit if we have high confidence and good performance
        if (data_confidence > self.config['exploit_confidence_threshold'] and 
            avg_roas > self.config['min_roas_for_exploit']):
            return "exploit"
        
        # Default to explore for learning
        return "explore"
    
    async def explore_mode_decisions(self, sku_id: str, performance: Dict) -> List[Dict]:
        """
        EXPLORE Mode: Bold budget reallocations for learning
        """
        decisions = []
        
        # Get current campaigns
        campaigns = await get_campaigns_by_sku(sku_id)
        active_campaigns = [c for c in campaigns if c.get("status") == "active"]
        
        if not active_campaigns:
            return decisions
        
        # Calculate total budget and exploration budget
        total_budget = sum(c.get("budget_allocated", 0) for c in active_campaigns)
        explore_budget = total_budget * (self.config['explore_budget_percentage'] / 100)
        
        # Sort campaigns by performance (lowest performing first for exploration)
        campaigns_by_performance = sorted(
            active_campaigns,
            key=lambda x: performance.get('campaigns', {}).get(x['_id'], {}).get('roas', 0)
        )
        
        # Allocate exploration budget to underperforming campaigns
        for i, campaign in enumerate(campaigns_by_performance[:3]):  # Top 3 underperformers
            current_budget = campaign.get("budget_allocated", 0)
            new_budget = current_budget + (explore_budget / 3)  # Distribute exploration budget
            
            # Ensure minimum budget
            new_budget = max(new_budget, self.config['min_campaign_budget'])
            
            if new_budget != current_budget:
                decisions.append({
                    "type": "budget_allocation",
                    "campaign_id": campaign["_id"],
                    "old_budget": current_budget,
                    "new_budget": new_budget,
                    "reason": f"Exploration allocation for learning (campaign #{i+1})"
                })
        
        return decisions
    
    async def exploit_mode_decisions(self, sku_id: str, performance: Dict) -> List[Dict]:
        """
        EXPLOIT Mode: Small incremental optimizations
        """
        decisions = []
        
        # Get current campaigns
        campaigns = await get_campaigns_by_sku(sku_id)
        active_campaigns = [c for c in campaigns if c.get("status") == "active"]
        
        if not active_campaigns:
            return decisions
        
        # Sort campaigns by performance (highest performing first)
        campaigns_by_performance = sorted(
            active_campaigns,
            key=lambda x: performance.get('campaigns', {}).get(x['_id'], {}).get('roas', 0),
            reverse=True
        )
        
        # Small budget adjustments based on performance
        for campaign in campaigns_by_performance:
            campaign_performance = performance.get('campaigns', {}).get(campaign['_id'], {})
            current_roas = campaign_performance.get('roas', 0)
            current_budget = campaign.get("budget_allocated", 0)
            
            # Increase budget for high-performing campaigns (max 10% increase)
            if current_roas > 3.0:  # High ROAS threshold
                new_budget = current_budget * 1.1
                new_budget = min(new_budget, current_budget * (1 + self.config['max_daily_budget_increase_percentage'] / 100))
                
                decisions.append({
                    "type": "budget_allocation",
                    "campaign_id": campaign["_id"],
                    "old_budget": current_budget,
                    "new_budget": new_budget,
                    "reason": f"Exploit: High ROAS ({current_roas:.2f}) - increasing budget"
                })
            
            # Decrease budget for low-performing campaigns (max 20% decrease)
            elif current_roas < 1.5:  # Low ROAS threshold
                new_budget = current_budget * 0.8
                new_budget = max(new_budget, self.config['min_campaign_budget'])
                
                decisions.append({
                    "type": "budget_allocation",
                    "campaign_id": campaign["_id"],
                    "old_budget": current_budget,
                    "new_budget": new_budget,
                    "reason": f"Exploit: Low ROAS ({current_roas:.2f}) - decreasing budget"
                })
        
        return decisions
    
    async def execute_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """Execute intelligence decisions"""
        results = []
        
        for decision in decisions:
            try:
                if decision["type"] == "budget_allocation":
                    success = await update_campaign_budget(
                        decision["campaign_id"], 
                        decision["new_budget"]
                    )
                    results.append({
                        "decision": decision,
                        "success": success,
                        "message": "Budget updated successfully" if success else "Budget update failed"
                    })
                
                elif decision["type"] == "pause_campaign":
                    success = await pause_campaign(decision["campaign_id"])
                    results.append({
                        "decision": decision,
                        "success": success,
                        "message": "Campaign paused successfully" if success else "Campaign pause failed"
                    })
                
                elif decision["type"] == "activate_campaign":
                    success = await activate_campaign(decision["campaign_id"])
                    results.append({
                        "decision": decision,
                        "success": success,
                        "message": "Campaign activated successfully" if success else "Campaign activation failed"
                    })
                
            except Exception as e:
                results.append({
                    "decision": decision,
                    "success": False,
                    "message": f"Execution error: {str(e)}"
                })
        
        return results
    
    async def get_sku_performance(self, sku_id: str) -> Dict:
        """Get aggregated performance data for a SKU"""
        try:
            # Get campaigns for this SKU
            campaigns = await get_campaigns_by_sku(sku_id)
            campaign_ids = [str(c["_id"]) for c in campaigns]
            
            if not campaign_ids:
                return {
                    "total_impressions": 0,
                    "total_spend": 0.0,
                    "avg_roas": 0.0,
                    "confidence_score": 0.0,
                    "days_running": 0,
                    "campaigns": {}
                }
            
            # Get performance metrics for last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            pipeline = [
                {
                    "$match": {
                        "sku_id": sku_id,
                        "timestamp": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$campaign_id",
                        "total_spend": {"$sum": "$spend"},
                        "total_impressions": {"$sum": "$impressions"},
                        "total_clicks": {"$sum": "$clicks"},
                        "total_conversions": {"$sum": "$conversions"},
                        "avg_roas": {"$avg": "$roas"},
                        "data_points": {"$sum": 1}
                    }
                }
            ]
            
            results = await db.performance_metrics.aggregate(pipeline).to_list(1000)
            
            # Calculate aggregated metrics
            total_spend = sum(r["total_spend"] for r in results)
            total_impressions = sum(r["total_impressions"] for r in results)
            total_conversions = sum(r["total_conversions"] for r in results)
            avg_roas = (total_conversions / total_spend) if total_spend > 0 else 0.0
            
            # Calculate confidence score based on data points
            total_data_points = sum(r["data_points"] for r in results)
            confidence_score = min(total_data_points / self.config['minimum_data_points_for_decisions'], 1.0)
            
            # Calculate days running (simplified)
            days_running = 7  # For now, assume 7 days of data
            
            # Build campaign-level performance
            campaign_performance = {}
            for result in results:
                campaign_performance[result["_id"]] = {
                    "spend": result["total_spend"],
                    "impressions": result["total_impressions"],
                    "clicks": result["total_clicks"],
                    "conversions": result["total_conversions"],
                    "roas": result["avg_roas"],
                    "data_points": result["data_points"]
                }
            
            return {
                "total_impressions": total_impressions,
                "total_spend": total_spend,
                "total_conversions": total_conversions,
                "avg_roas": avg_roas,
                "confidence_score": confidence_score,
                "days_running": days_running,
                "campaigns": campaign_performance
            }
            
        except Exception as e:
            logger.error(f"Error getting SKU performance for {sku_id}: {e}")
            return {
                "total_impressions": 0,
                "total_spend": 0.0,
                "avg_roas": 0.0,
                "confidence_score": 0.0,
                "days_running": 0,
                "campaigns": {}
            }
    
    async def log_decisions(self, sku_id: str, client_id: str, decisions: List[Dict], 
                          mode: str, execution_results: List[Dict]):
        """Log intelligence decisions for analysis"""
        try:
            decision_log = {
                "sku_id": sku_id,
                "client_id": client_id,
                "timestamp": datetime.now(),
                "decision_type": "hourly_optimization",
                "mode": mode,
                "decisions": decisions,
                "execution_results": execution_results,
                "data_points_used": sum(len(r.get("campaigns", {})) for r in execution_results),
                "confidence_score": 0.8  # Simplified confidence score
            }
            
            await db.intelligence_decisions.insert_one(decision_log)
            
        except Exception as e:
            logger.error(f"Error logging decisions for {sku_id}: {e}")

class IntelligenceScheduler:
    """Scheduler for running intelligence decisions"""
    
    def __init__(self):
        self.intelligence = SKUIntelligence()
        self.running = False
    
    async def start_hourly_optimization(self):
        """Start the hourly optimization process"""
        self.running = True
        logger.info("Starting hourly intelligence optimization")
        
        while self.running:
            try:
                # Get all active SKUs
                sku_collection = db.skus
                active_skus = await sku_collection.find({"status": "active"}).to_list(1000)
                
                # Process each SKU
                for sku in active_skus:
                    sku_id = str(sku["_id"])
                    result = await self.intelligence.make_hourly_decisions(sku_id)
                    
                    if result["success"]:
                        logger.info(f"Intelligence decisions completed for SKU {sku_id} in {result['mode']} mode")
                    else:
                        logger.error(f"Intelligence decisions failed for SKU {sku_id}: {result['message']}")
                
                # Wait for next hour
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in hourly optimization: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def stop_optimization(self):
        """Stop the optimization process"""
        self.running = False
        logger.info("Stopping hourly intelligence optimization")

