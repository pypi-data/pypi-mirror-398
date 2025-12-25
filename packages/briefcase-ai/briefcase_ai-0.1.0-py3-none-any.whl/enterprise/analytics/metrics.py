"""
Advanced Metrics Collection

Provides enterprise-grade metrics collection and analysis for
performance monitoring and business insights.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


class MetricType(Enum):
    """Types of metrics collected"""

    # Performance metrics
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_USAGE = "memory_usage"

    # Business metrics
    ACTIVE_USERS = "active_users"
    SNAPSHOT_COUNT = "snapshot_count"
    REPLAY_SUCCESS_RATE = "replay_success_rate"
    FEATURE_USAGE = "feature_usage"

    # Cost metrics
    COMPUTE_COST = "compute_cost"
    STORAGE_COST = "storage_cost"
    BANDWIDTH_COST = "bandwidth_cost"

    # Security metrics
    FAILED_LOGINS = "failed_logins"
    PERMISSION_DENIALS = "permission_denials"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class Metric:
    """Represents a single metric data point"""

    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


class MetricsCollector(ABC):
    """
    Abstract base class for metrics collection.

    This interface allows OSS core to emit metrics without depending
    on enterprise implementation details.
    """

    @abstractmethod
    async def emit_metric(self, metric: Metric):
        """Emit a single metric"""
        pass

    @abstractmethod
    async def emit_counter(self, name: str, value: float = 1, tags: Dict[str, str] = None):
        """Emit a counter metric"""
        pass

    @abstractmethod
    async def emit_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Emit a gauge metric"""
        pass

    @abstractmethod
    async def emit_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Emit a histogram metric"""
        pass

    @abstractmethod
    async def query_metrics(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime,
        aggregation: str = "avg",
        interval: str = "1h"
    ) -> List[Dict[str, Any]]:
        """Query metrics with aggregation"""
        pass


class DefaultMetricsCollector(MetricsCollector):
    """
    Default metrics collector implementation

    In production, this would integrate with:
    - Prometheus/Grafana
    - DataDog
    - CloudWatch
    - New Relic
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics_buffer: List[Metric] = []
        self.buffer_size = self.config.get("buffer_size", 1000)

    async def emit_metric(self, metric: Metric):
        """Emit a single metric"""
        self.metrics_buffer.append(metric)

        # Flush buffer if it's full
        if len(self.metrics_buffer) >= self.buffer_size:
            await self._flush_buffer()

    async def emit_counter(self, name: str, value: float = 1, tags: Dict[str, str] = None):
        """Emit a counter metric"""
        # Map name to MetricType if possible
        try:
            metric_type = MetricType(name)
        except ValueError:
            metric_type = MetricType.FEATURE_USAGE

        metric = Metric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        await self.emit_metric(metric)

    async def emit_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Emit a gauge metric"""
        try:
            metric_type = MetricType(name)
        except ValueError:
            metric_type = MetricType.CPU_UTILIZATION  # Default for gauge

        metric = Metric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        await self.emit_metric(metric)

    async def emit_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Emit a histogram metric"""
        try:
            metric_type = MetricType(name)
        except ValueError:
            metric_type = MetricType.RESPONSE_TIME  # Default for histogram

        metric = Metric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        await self.emit_metric(metric)

    async def query_metrics(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime,
        aggregation: str = "avg",
        interval: str = "1h"
    ) -> List[Dict[str, Any]]:
        """Query metrics with aggregation"""
        # Filter metrics by type and time range
        filtered_metrics = [
            m for m in self.metrics_buffer
            if m.metric_type == metric_type
            and start_time <= m.timestamp <= end_time
        ]

        # Group by interval
        interval_groups = self._group_by_interval(filtered_metrics, interval)

        # Apply aggregation
        result = []
        for interval_start, metrics in interval_groups.items():
            if not metrics:
                continue

            values = [m.value for m in metrics]

            if aggregation == "avg":
                aggregated_value = sum(values) / len(values)
            elif aggregation == "sum":
                aggregated_value = sum(values)
            elif aggregation == "max":
                aggregated_value = max(values)
            elif aggregation == "min":
                aggregated_value = min(values)
            elif aggregation == "count":
                aggregated_value = len(values)
            else:
                aggregated_value = sum(values) / len(values)  # Default to avg

            result.append({
                "timestamp": interval_start.isoformat(),
                "value": aggregated_value,
                "count": len(metrics)
            })

        return sorted(result, key=lambda x: x["timestamp"])

    def _group_by_interval(self, metrics: List[Metric], interval: str) -> Dict[datetime, List[Metric]]:
        """Group metrics by time interval"""
        # Parse interval (simplified)
        if interval.endswith('h'):
            interval_seconds = int(interval[:-1]) * 3600
        elif interval.endswith('m'):
            interval_seconds = int(interval[:-1]) * 60
        elif interval.endswith('s'):
            interval_seconds = int(interval[:-1])
        else:
            interval_seconds = 3600  # Default to 1 hour

        groups = {}
        for metric in metrics:
            # Round timestamp to interval boundary
            timestamp_seconds = int(metric.timestamp.timestamp())
            interval_start_seconds = (timestamp_seconds // interval_seconds) * interval_seconds
            interval_start = datetime.fromtimestamp(interval_start_seconds)

            if interval_start not in groups:
                groups[interval_start] = []
            groups[interval_start].append(metric)

        return groups

    async def _flush_buffer(self):
        """Flush metrics buffer to storage/monitoring system"""
        if not self.metrics_buffer:
            return

        # In production, would send to actual monitoring system
        # For now, just clear the buffer
        print(f"Flushing {len(self.metrics_buffer)} metrics to monitoring system")
        self.metrics_buffer.clear()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all metrics"""
        if not self.metrics_buffer:
            return {}

        stats_by_type = {}
        for metric_type in MetricType:
            type_metrics = [m for m in self.metrics_buffer if m.metric_type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                stats_by_type[metric_type.value] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": type_metrics[-1].value,
                    "latest_timestamp": type_metrics[-1].timestamp.isoformat()
                }

        return {
            "total_metrics": len(self.metrics_buffer),
            "by_type": stats_by_type,
            "oldest_metric": min(m.timestamp for m in self.metrics_buffer).isoformat() if self.metrics_buffer else None,
            "newest_metric": max(m.timestamp for m in self.metrics_buffer).isoformat() if self.metrics_buffer else None
        }


# Factory function for OSS integration
def create_metrics_collector(config: Optional[Dict[str, Any]] = None) -> MetricsCollector:
    """
    Factory function to create metrics collector.

    This function can be called by OSS core to get a metrics collector
    without importing enterprise-specific classes.
    """
    return DefaultMetricsCollector(config)