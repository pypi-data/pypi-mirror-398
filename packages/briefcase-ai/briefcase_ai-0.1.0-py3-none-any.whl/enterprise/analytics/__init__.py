"""
Enterprise Analytics

This module provides advanced analytics and insights for enterprise deployments.
"""

from .metrics import MetricsCollector, MetricType
from .insights import InsightsEngine, RecommendationEngine
from .dashboards import DashboardManager, Dashboard

__all__ = [
    "MetricsCollector",
    "MetricType",
    "InsightsEngine",
    "RecommendationEngine",
    "DashboardManager",
    "Dashboard"
]