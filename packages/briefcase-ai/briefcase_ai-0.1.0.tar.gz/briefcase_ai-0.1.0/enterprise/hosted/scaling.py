"""
Auto-scaling for Hosted Infrastructure

Provides intelligent resource management and auto-scaling capabilities
for enterprise hosted deployments.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio


class MetricType(Enum):
    """Types of metrics for scaling decisions"""
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    QUEUE_LENGTH = "queue_length"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"


class ScaleDirection(Enum):
    """Direction of scaling operation"""
    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class ScalingMetric:
    """Represents a metric used for scaling decisions"""

    metric_type: MetricType
    current_value: float
    threshold_up: float
    threshold_down: float
    weight: float = 1.0  # Weight in scaling decision
    evaluation_period: int = 300  # seconds


@dataclass
class ScalingPolicy:
    """Defines auto-scaling policy"""

    name: str
    metrics: List[ScalingMetric]
    min_instances: int
    max_instances: int
    scale_up_cooldown: int = 300  # seconds
    scale_down_cooldown: int = 600  # seconds
    scale_up_step: int = 1  # instances to add
    scale_down_step: int = 1  # instances to remove
    enabled: bool = True


@dataclass
class ScalingEvent:
    """Represents a scaling event"""

    timestamp: datetime
    direction: ScaleDirection
    instances_before: int
    instances_after: int
    reason: str
    triggered_by: List[MetricType]
    duration_seconds: Optional[float] = None


class AutoScaler(ABC):
    """
    Abstract base class for auto-scaling.

    This interface allows hosted services to scale resources automatically
    based on demand and performance metrics.
    """

    @abstractmethod
    async def evaluate_scaling(self) -> ScaleDirection:
        """Evaluate current metrics and determine if scaling is needed"""
        pass

    @abstractmethod
    async def scale_up(self, instances: int = 1) -> bool:
        """Scale up by specified number of instances"""
        pass

    @abstractmethod
    async def scale_down(self, instances: int = 1) -> bool:
        """Scale down by specified number of instances"""
        pass

    @abstractmethod
    async def get_current_capacity(self) -> int:
        """Get current number of instances"""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[MetricType, float]:
        """Get current metric values"""
        pass

    @abstractmethod
    async def get_scaling_history(self, hours: int = 24) -> List[ScalingEvent]:
        """Get scaling event history"""
        pass


class DefaultAutoScaler(AutoScaler):
    """
    Default auto-scaler implementation

    In production, this would integrate with cloud provider APIs
    (AWS Auto Scaling, Azure Scale Sets, GKE Autopilot, etc.)
    """

    def __init__(self, policy: ScalingPolicy, resource_manager=None):
        self.policy = policy
        self.resource_manager = resource_manager
        self.current_instances = policy.min_instances
        self.scaling_history: List[ScalingEvent] = []
        self.last_scale_up = None
        self.last_scale_down = None
        self._metrics_history: Dict[MetricType, List[tuple]] = {}
        self._monitoring_task = None

    async def start_monitoring(self):
        """Start the auto-scaling monitoring loop"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop the auto-scaling monitoring loop"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

    async def evaluate_scaling(self) -> ScaleDirection:
        """Evaluate current metrics and determine if scaling is needed"""
        if not self.policy.enabled:
            return ScaleDirection.NONE

        current_metrics = await self.get_metrics()
        scale_up_votes = 0
        scale_down_votes = 0
        total_weight = 0

        for metric in self.policy.metrics:
            current_value = current_metrics.get(metric.metric_type, 0.0)
            total_weight += metric.weight

            if current_value > metric.threshold_up:
                scale_up_votes += metric.weight
            elif current_value < metric.threshold_down:
                scale_down_votes += metric.weight

        # Calculate scaling decision based on weighted votes
        scale_up_ratio = scale_up_votes / total_weight if total_weight > 0 else 0
        scale_down_ratio = scale_down_votes / total_weight if total_weight > 0 else 0

        # Need majority vote to scale
        if scale_up_ratio > 0.5:
            # Check cooldown
            if self._can_scale_up():
                return ScaleDirection.UP
        elif scale_down_ratio > 0.5:
            # Check cooldown
            if self._can_scale_down():
                return ScaleDirection.DOWN

        return ScaleDirection.NONE

    async def scale_up(self, instances: int = 1) -> bool:
        """Scale up by specified number of instances"""
        if not self._can_scale_up():
            return False

        instances_to_add = min(instances, self.policy.max_instances - self.current_instances)
        if instances_to_add <= 0:
            return False

        # Record scaling event
        event = ScalingEvent(
            timestamp=datetime.utcnow(),
            direction=ScaleDirection.UP,
            instances_before=self.current_instances,
            instances_after=self.current_instances + instances_to_add,
            reason="Auto-scaling triggered by metric thresholds",
            triggered_by=[m.metric_type for m in self.policy.metrics]
        )

        # Perform scaling (in production, would call cloud provider APIs)
        start_time = datetime.utcnow()
        success = await self._provision_instances(instances_to_add)

        if success:
            self.current_instances += instances_to_add
            self.last_scale_up = datetime.utcnow()
            event.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            self.scaling_history.append(event)
            return True

        return False

    async def scale_down(self, instances: int = 1) -> bool:
        """Scale down by specified number of instances"""
        if not self._can_scale_down():
            return False

        instances_to_remove = min(instances, self.current_instances - self.policy.min_instances)
        if instances_to_remove <= 0:
            return False

        # Record scaling event
        event = ScalingEvent(
            timestamp=datetime.utcnow(),
            direction=ScaleDirection.DOWN,
            instances_before=self.current_instances,
            instances_after=self.current_instances - instances_to_remove,
            reason="Auto-scaling triggered by low utilization",
            triggered_by=[m.metric_type for m in self.policy.metrics]
        )

        # Perform scaling (in production, would call cloud provider APIs)
        start_time = datetime.utcnow()
        success = await self._terminate_instances(instances_to_remove)

        if success:
            self.current_instances -= instances_to_remove
            self.last_scale_down = datetime.utcnow()
            event.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            self.scaling_history.append(event)
            return True

        return False

    async def get_current_capacity(self) -> int:
        """Get current number of instances"""
        return self.current_instances

    async def get_metrics(self) -> Dict[MetricType, float]:
        """Get current metric values"""
        # In production, would query actual monitoring systems
        # For now, return simulated metrics

        import random

        metrics = {}
        for metric in self.policy.metrics:
            if metric.metric_type == MetricType.CPU_UTILIZATION:
                # Simulate CPU utilization (0-100%)
                metrics[metric.metric_type] = random.uniform(20, 90)
            elif metric.metric_type == MetricType.MEMORY_UTILIZATION:
                # Simulate memory utilization (0-100%)
                metrics[metric.metric_type] = random.uniform(30, 85)
            elif metric.metric_type == MetricType.QUEUE_LENGTH:
                # Simulate queue length
                metrics[metric.metric_type] = random.uniform(0, 50)
            elif metric.metric_type == MetricType.REQUEST_RATE:
                # Simulate requests per second
                metrics[metric.metric_type] = random.uniform(10, 200)
            elif metric.metric_type == MetricType.RESPONSE_TIME:
                # Simulate response time in milliseconds
                metrics[metric.metric_type] = random.uniform(100, 2000)
            elif metric.metric_type == MetricType.ERROR_RATE:
                # Simulate error rate (0-10%)
                metrics[metric.metric_type] = random.uniform(0, 5)

        # Store metrics history
        now = datetime.utcnow()
        for metric_type, value in metrics.items():
            if metric_type not in self._metrics_history:
                self._metrics_history[metric_type] = []
            self._metrics_history[metric_type].append((now, value))

            # Keep only recent history (last hour)
            cutoff = now - timedelta(hours=1)
            self._metrics_history[metric_type] = [
                (ts, val) for ts, val in self._metrics_history[metric_type]
                if ts > cutoff
            ]

        return metrics

    async def get_scaling_history(self, hours: int = 24) -> List[ScalingEvent]:
        """Get scaling event history"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [event for event in self.scaling_history if event.timestamp > cutoff]

    def _can_scale_up(self) -> bool:
        """Check if scale up is allowed (cooldown and limits)"""
        if self.current_instances >= self.policy.max_instances:
            return False

        if self.last_scale_up:
            time_since_scale = (datetime.utcnow() - self.last_scale_up).total_seconds()
            return time_since_scale >= self.policy.scale_up_cooldown

        return True

    def _can_scale_down(self) -> bool:
        """Check if scale down is allowed (cooldown and limits)"""
        if self.current_instances <= self.policy.min_instances:
            return False

        if self.last_scale_down:
            time_since_scale = (datetime.utcnow() - self.last_scale_down).total_seconds()
            return time_since_scale >= self.policy.scale_down_cooldown

        return True

    async def _provision_instances(self, count: int) -> bool:
        """Provision new instances (placeholder)"""
        # In production, would call cloud provider APIs to:
        # - Launch new instances
        # - Register with load balancer
        # - Wait for health checks
        # - Configure monitoring

        await asyncio.sleep(2)  # Simulate provisioning time
        return True

    async def _terminate_instances(self, count: int) -> bool:
        """Terminate instances (placeholder)"""
        # In production, would call cloud provider APIs to:
        # - Drain connections gracefully
        # - Remove from load balancer
        # - Terminate instances
        # - Clean up resources

        await asyncio.sleep(1)  # Simulate termination time
        return True

    async def _monitoring_loop(self):
        """Main monitoring loop for auto-scaling"""
        while True:
            try:
                # Evaluate scaling decision
                scale_decision = await self.evaluate_scaling()

                if scale_decision == ScaleDirection.UP:
                    await self.scale_up(self.policy.scale_up_step)
                elif scale_decision == ScaleDirection.DOWN:
                    await self.scale_down(self.policy.scale_down_step)

                # Sleep between evaluations
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                print(f"Error in scaling monitoring: {e}")
                await asyncio.sleep(60)

    def get_optimization_recommendations(self) -> List[str]:
        """Get cost and performance optimization recommendations"""
        recommendations = []

        # Analyze scaling history
        recent_events = self.scaling_history[-10:] if self.scaling_history else []

        # Check for frequent scaling
        scale_ups = [e for e in recent_events if e.direction == ScaleDirection.UP]
        scale_downs = [e for e in recent_events if e.direction == ScaleDirection.DOWN]

        if len(scale_ups) > 5 and len(scale_downs) > 5:
            recommendations.append(
                "Consider adjusting scaling thresholds to reduce frequent scaling oscillation"
            )

        # Check for underutilization
        if len(scale_downs) > len(scale_ups) * 2:
            recommendations.append(
                "Resources appear to be over-provisioned, consider reducing min_instances"
            )

        # Check for constant high utilization
        if len(scale_ups) > len(scale_downs) * 2:
            recommendations.append(
                "Consider increasing min_instances to handle baseline load more efficiently"
            )

        return recommendations


# Predefined scaling policies
WEB_SERVICE_POLICY = ScalingPolicy(
    name="web_service_scaling",
    metrics=[
        ScalingMetric(
            metric_type=MetricType.CPU_UTILIZATION,
            current_value=0,
            threshold_up=70.0,
            threshold_down=30.0,
            weight=1.0
        ),
        ScalingMetric(
            metric_type=MetricType.RESPONSE_TIME,
            current_value=0,
            threshold_up=1000.0,  # 1 second
            threshold_down=300.0,  # 300ms
            weight=0.8
        )
    ],
    min_instances=2,
    max_instances=20,
    scale_up_cooldown=300,
    scale_down_cooldown=600
)

BATCH_PROCESSING_POLICY = ScalingPolicy(
    name="batch_processing_scaling",
    metrics=[
        ScalingMetric(
            metric_type=MetricType.QUEUE_LENGTH,
            current_value=0,
            threshold_up=10.0,
            threshold_down=2.0,
            weight=1.0
        ),
        ScalingMetric(
            metric_type=MetricType.CPU_UTILIZATION,
            current_value=0,
            threshold_up=80.0,
            threshold_down=20.0,
            weight=0.7
        )
    ],
    min_instances=0,
    max_instances=50,
    scale_up_cooldown=60,
    scale_down_cooldown=300
)


# Factory function for OSS integration
def create_auto_scaler(policy: ScalingPolicy, config: Optional[Dict[str, Any]] = None) -> AutoScaler:
    """
    Factory function to create auto-scaler.

    This function can be called by hosted services to get an auto-scaler
    without importing enterprise-specific classes.
    """
    return DefaultAutoScaler(policy)