"""
Configuration for the intelligence layer
"""

# MVP Configuration Parameters
MVP_CONFIG = {
    # Budget Allocation Limits
    "min_campaign_budget": 100,  # USD minimum per campaign
    "spend_floor_percentage": 10,  # % of total budget as floor
    "spend_cap_percentage": 50,   # % of total budget as cap
    "explore_budget_percentage": 20,  # % allocated to exploration
    
    # Decision Thresholds
    "impression_threshold": 1000,  # Minimum impressions for decisions
    "min_confidence_for_major_changes": 0.7,
    "statistical_significance_p_value": 0.05,
    "minimum_data_points_for_decisions": 50,
    
    # Mode Switching Logic
    "explore_mode_duration_days": 7,
    "exploit_confidence_threshold": 0.8,
    "min_roas_for_exploit": 2.0,
    
    # Creative Performance
    "creative_fatigue_ctr_drop_threshold": 0.15,
    "creative_refresh_performance_drop": 0.20,
    "min_creative_runtime_hours": 48,
    
    # Budget Management
    "max_single_campaign_budget_percentage": 40,
    "max_daily_budget_increase_percentage": 50,
    "max_daily_budget_decrease_percentage": 80,
}

# Platform-Specific Configuration
PLATFORM_CONFIGS = {
    "google_ads": {
        "api_rate_limit_per_minute": 60,
        "batch_size_for_updates": 50,
        "min_quality_score": 5,
        "target_impression_share": 0.80,
        "search_vs_display_allocation": {"search": 0.7, "display": 0.3}
    },
    "meta_ads": {
        "api_rate_limit_per_hour": 200,
        "learning_phase_min_events": 50,
        "audience_overlap_threshold": 0.25,
        "creative_rotation_frequency_hours": 72,
        "lookalike_audience_size_target": 2000000
    },
    "tiktok_ads": {
        "api_rate_limit_per_minute": 40,
        "video_creative_min_duration_seconds": 9,
        "trending_hashtag_usage_limit": 3,
        "audience_size_min": 100000,
        "bid_strategy_preference": "cost_cap"
    },
    "linkedin_ads": {
        "api_rate_limit_per_minute": 30,
        "b2b_audience_size_min": 50000,
        "sponsored_content_vs_message_ratio": {"content": 0.8, "message": 0.2},
        "professional_targeting_precision_score": 0.85
    }
}

# Risk Management Thresholds
RISK_MANAGEMENT_CONFIG = {
    # Budget Risk Controls
    "daily_spend_variance_alert_threshold": 0.25,  # 25% over target
    "budget_depletion_warning_days": 3,
    "emergency_pause_spend_threshold": 1.5,  # 150% of daily target
    
    # Performance Risk Thresholds
    "roas_decline_alert_percentage": 0.30,  # 30% decline
    "conversion_drop_alert_percentage": 0.40,  # 40% decline
    "ctr_decline_alert_percentage": 0.50,  # 50% decline
    "quality_score_minimum": 4,
    
    # Platform Reliability
    "api_failure_rate_threshold": 0.05,  # 5% failure rate
    "data_sync_delay_alert_minutes": 90,
    "integrator_downtime_fallback_trigger_minutes": 15,
    
    # Portfolio Risk Distribution
    "max_budget_single_platform_percentage": 60,
    "min_platform_diversification": 2,  # At least 2 platforms
    "correlation_risk_threshold": 0.8  # High correlation warning
}
