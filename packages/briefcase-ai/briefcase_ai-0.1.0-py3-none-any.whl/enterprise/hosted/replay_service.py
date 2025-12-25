"""
Hosted Replay Service

Provides cloud-hosted replay infrastructure with auto-scaling,
multi-tenancy, and enterprise management features.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio


class ReplayStatus(Enum):
    """Status of a replay execution"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InfrastructureProvider(Enum):
    """Supported cloud infrastructure providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"


@dataclass
class ReplayRequest:
    """Represents a request to execute a replay"""

    request_id: str
    tenant_id: str
    snapshot_id: str
    user_id: str
    priority: int = 5  # 1-10, 10 = highest
    resource_requirements: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 3600
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReplayResult:
    """Result of a replay execution"""

    request_id: str
    status: ReplayStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    resource_usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    artifacts_location: Optional[str] = None


@dataclass
class ReplayInfrastructure:
    """Represents replay infrastructure configuration"""

    provider: InfrastructureProvider
    region: str
    instance_types: List[str]
    auto_scaling_enabled: bool = True
    min_instances: int = 0
    max_instances: int = 100
    scale_up_threshold: float = 0.8  # CPU utilization
    scale_down_threshold: float = 0.3
    cost_optimization: bool = True


class HostedReplayService(ABC):
    """
    Abstract base class for hosted replay services.

    This interface allows OSS core to submit replays to hosted infrastructure
    without depending on enterprise implementation details.
    """

    @abstractmethod
    async def submit_replay(self, request: ReplayRequest) -> str:
        """Submit a replay request and return request ID"""
        pass

    @abstractmethod
    async def get_replay_status(self, request_id: str) -> ReplayStatus:
        """Get status of a replay request"""
        pass

    @abstractmethod
    async def get_replay_result(self, request_id: str) -> Optional[ReplayResult]:
        """Get detailed result of a replay request"""
        pass

    @abstractmethod
    async def cancel_replay(self, request_id: str) -> bool:
        """Cancel a running or queued replay"""
        pass

    @abstractmethod
    async def list_replays(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[ReplayStatus] = None,
        limit: int = 100
    ) -> List[ReplayResult]:
        """List replay executions with optional filters"""
        pass

    @abstractmethod
    async def get_infrastructure_stats(self) -> Dict[str, Any]:
        """Get infrastructure utilization and performance stats"""
        pass


class DefaultHostedReplayService(HostedReplayService):
    """
    Default hosted replay service implementation

    In production, this would integrate with actual cloud providers
    and orchestration systems like Kubernetes.
    """

    def __init__(self, infrastructure: ReplayInfrastructure):
        self.infrastructure = infrastructure
        self.replay_queue: List[ReplayRequest] = []
        self.active_replays: Dict[str, ReplayResult] = {}
        self.completed_replays: List[ReplayResult] = []
        self._worker_task = None

    async def start(self):
        """Start the replay service worker"""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._replay_worker())

    async def stop(self):
        """Stop the replay service worker"""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    async def submit_replay(self, request: ReplayRequest) -> str:
        """Submit a replay request and return request ID"""
        # Add to queue sorted by priority
        self.replay_queue.append(request)
        self.replay_queue.sort(key=lambda x: x.priority, reverse=True)

        # Initialize result tracking
        result = ReplayResult(
            request_id=request.request_id,
            status=ReplayStatus.QUEUED
        )
        self.active_replays[request.request_id] = result

        return request.request_id

    async def get_replay_status(self, request_id: str) -> ReplayStatus:
        """Get status of a replay request"""
        if request_id in self.active_replays:
            return self.active_replays[request_id].status

        # Check completed replays
        for replay in self.completed_replays:
            if replay.request_id == request_id:
                return replay.status

        return ReplayStatus.FAILED

    async def get_replay_result(self, request_id: str) -> Optional[ReplayResult]:
        """Get detailed result of a replay request"""
        if request_id in self.active_replays:
            return self.active_replays[request_id]

        for replay in self.completed_replays:
            if replay.request_id == request_id:
                return replay

        return None

    async def cancel_replay(self, request_id: str) -> bool:
        """Cancel a running or queued replay"""
        # Remove from queue if still queued
        self.replay_queue = [r for r in self.replay_queue if r.request_id != request_id]

        # Mark as cancelled if active
        if request_id in self.active_replays:
            result = self.active_replays[request_id]
            result.status = ReplayStatus.CANCELLED
            result.completed_at = datetime.utcnow()

            # Move to completed
            self.completed_replays.append(result)
            del self.active_replays[request_id]
            return True

        return False

    async def list_replays(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[ReplayStatus] = None,
        limit: int = 100
    ) -> List[ReplayResult]:
        """List replay executions with optional filters"""
        all_replays = list(self.active_replays.values()) + self.completed_replays

        # Apply filters
        filtered_replays = all_replays
        if status:
            filtered_replays = [r for r in filtered_replays if r.status == status]

        # Sort by most recent first
        filtered_replays.sort(
            key=lambda x: x.started_at or datetime.min,
            reverse=True
        )

        return filtered_replays[:limit]

    async def get_infrastructure_stats(self) -> Dict[str, Any]:
        """Get infrastructure utilization and performance stats"""
        return {
            "provider": self.infrastructure.provider.value,
            "region": self.infrastructure.region,
            "active_instances": len(self.active_replays),
            "queued_requests": len(self.replay_queue),
            "completed_today": len([
                r for r in self.completed_replays
                if r.completed_at and r.completed_at.date() == datetime.utcnow().date()
            ]),
            "average_execution_time": self._calculate_average_execution_time(),
            "success_rate": self._calculate_success_rate(),
            "cost_estimate": self._estimate_costs()
        }

    async def _replay_worker(self):
        """Background worker to process replay queue"""
        while True:
            try:
                if self.replay_queue and len(self.active_replays) < self.infrastructure.max_instances:
                    # Get next request from queue
                    request = self.replay_queue.pop(0)

                    # Start execution
                    await self._execute_replay(request)

                await asyncio.sleep(1)  # Check every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue processing
                print(f"Error in replay worker: {e}")
                await asyncio.sleep(5)

    async def _execute_replay(self, request: ReplayRequest):
        """Execute a replay request"""
        result = self.active_replays[request.request_id]
        result.status = ReplayStatus.RUNNING
        result.started_at = datetime.utcnow()

        try:
            # Simulate replay execution
            # In production, this would:
            # 1. Provision compute resources
            # 2. Load snapshot data
            # 3. Execute replay
            # 4. Store results
            # 5. Clean up resources

            await asyncio.sleep(5)  # Simulate execution time

            result.status = ReplayStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.execution_time_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.resource_usage = {
                "cpu_hours": 0.1,
                "memory_gb_hours": 0.5,
                "storage_gb": 1.0
            }
            result.artifacts_location = f"s3://briefcase-replays/{request.request_id}/"

        except Exception as e:
            result.status = ReplayStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.error_message = str(e)

        finally:
            # Move to completed
            self.completed_replays.append(result)
            del self.active_replays[request.request_id]

            # Send callback if configured
            if request.callback_url:
                await self._send_callback(request.callback_url, result)

    async def _send_callback(self, callback_url: str, result: ReplayResult):
        """Send completion callback"""
        # In production, would make HTTP POST to callback URL
        pass

    def _calculate_average_execution_time(self) -> float:
        """Calculate average execution time for completed replays"""
        completed_with_time = [
            r for r in self.completed_replays
            if r.execution_time_seconds is not None
        ]

        if not completed_with_time:
            return 0.0

        return sum(r.execution_time_seconds for r in completed_with_time) / len(completed_with_time)

    def _calculate_success_rate(self) -> float:
        """Calculate success rate for completed replays"""
        if not self.completed_replays:
            return 0.0

        successful = len([
            r for r in self.completed_replays
            if r.status == ReplayStatus.COMPLETED
        ])

        return successful / len(self.completed_replays)

    def _estimate_costs(self) -> Dict[str, float]:
        """Estimate infrastructure costs"""
        # Simple cost estimation based on usage
        total_cpu_hours = sum(
            r.resource_usage.get("cpu_hours", 0)
            for r in self.completed_replays
            if r.resource_usage
        )

        return {
            "compute_cost_usd": total_cpu_hours * 0.10,  # $0.10 per CPU hour
            "storage_cost_usd": len(self.completed_replays) * 0.02,  # $0.02 per replay
            "total_cost_usd": (total_cpu_hours * 0.10) + (len(self.completed_replays) * 0.02)
        }


# Factory function for OSS integration
def create_hosted_replay_service(config: Dict[str, Any]) -> HostedReplayService:
    """
    Factory function to create hosted replay service.

    This function can be called by OSS core to get a hosted replay service
    without importing enterprise-specific classes.
    """
    infrastructure = ReplayInfrastructure(
        provider=InfrastructureProvider(config.get("provider", "aws")),
        region=config.get("region", "us-east-1"),
        instance_types=config.get("instance_types", ["m5.large"]),
        auto_scaling_enabled=config.get("auto_scaling", True),
        min_instances=config.get("min_instances", 0),
        max_instances=config.get("max_instances", 10)
    )

    return DefaultHostedReplayService(infrastructure)