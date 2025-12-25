"""
Enterprise Dashboards

Provides customizable dashboards and reporting for enterprise users.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class WidgetType(Enum):
    """Types of dashboard widgets"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    GAUGE = "gauge"
    TABLE = "table"
    METRIC = "metric"
    ALERT = "alert"


@dataclass
class Widget:
    """Dashboard widget definition"""

    widget_id: str
    title: str
    widget_type: WidgetType
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height


@dataclass
class Dashboard:
    """Dashboard definition"""

    dashboard_id: str
    name: str
    description: str
    widgets: List[Widget]
    permissions: List[str]
    created_by: str


class DashboardManager:
    """Simple dashboard manager placeholder"""

    def __init__(self):
        self.dashboards: Dict[str, Dashboard] = {}
        self._create_default_dashboards()

    def _create_default_dashboards(self):
        """Create default enterprise dashboards"""
        # System Overview Dashboard
        system_dashboard = Dashboard(
            dashboard_id="system_overview",
            name="System Overview",
            description="High-level system metrics and health",
            widgets=[
                Widget(
                    widget_id="cpu_usage",
                    title="CPU Utilization",
                    widget_type=WidgetType.LINE_CHART,
                    config={"metric": "cpu_utilization", "timespan": "1h"},
                    position={"x": 0, "y": 0, "width": 6, "height": 4}
                ),
                Widget(
                    widget_id="active_users",
                    title="Active Users",
                    widget_type=WidgetType.METRIC,
                    config={"metric": "active_users"},
                    position={"x": 6, "y": 0, "width": 3, "height": 2}
                ),
                Widget(
                    widget_id="error_rate",
                    title="Error Rate",
                    widget_type=WidgetType.GAUGE,
                    config={"metric": "error_rate", "max": 10},
                    position={"x": 9, "y": 0, "width": 3, "height": 2}
                )
            ],
            permissions=["admin", "operator"],
            created_by="system"
        )
        self.dashboards["system_overview"] = system_dashboard

        # Security Dashboard
        security_dashboard = Dashboard(
            dashboard_id="security",
            name="Security Overview",
            description="Security metrics and alerts",
            widgets=[
                Widget(
                    widget_id="failed_logins",
                    title="Failed Login Attempts",
                    widget_type=WidgetType.BAR_CHART,
                    config={"metric": "failed_logins", "timespan": "24h"},
                    position={"x": 0, "y": 0, "width": 6, "height": 4}
                ),
                Widget(
                    widget_id="security_alerts",
                    title="Security Alerts",
                    widget_type=WidgetType.ALERT,
                    config={"severity": ["high", "critical"]},
                    position={"x": 6, "y": 0, "width": 6, "height": 4}
                )
            ],
            permissions=["admin", "security_officer"],
            created_by="system"
        )
        self.dashboards["security"] = security_dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)

    def list_dashboards(self, user_role: str = None) -> List[Dashboard]:
        """List available dashboards"""
        if user_role:
            return [
                dash for dash in self.dashboards.values()
                if user_role in dash.permissions
            ]
        return list(self.dashboards.values())


# Factory function for OSS integration
def create_dashboard_manager() -> DashboardManager:
    """Factory function to create dashboard manager"""
    return DashboardManager()