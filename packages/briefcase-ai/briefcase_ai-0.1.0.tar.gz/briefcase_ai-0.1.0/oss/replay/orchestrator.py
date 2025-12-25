"""
Replay Orchestrator for Batch Operations and Scheduling

This module provides orchestration capabilities for running replay operations
at scale. It includes batch processing, scheduling, parallel execution,
and comprehensive reporting for large-scale replay validations.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

from ..sdk.models import Snapshot
from ..sdk.serialization import SnapshotSerializer
from .diff import DiffEngine, DiffResult
from .engine import ReplayEngine, ReplayContext, ReplayMode, ReplayResult
from .policies import PolicyFramework, PolicyResult


class BatchStatus(str, Enum):
    """Status of batch replay operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class BatchReplayConfig(BaseModel):
    """Configuration for batch replay operations."""
    model_config = ConfigDict(frozen=True)

    batch_id: UUID = Field(default_factory=uuid4, description="Unique batch identifier")
    max_concurrent_replays: int = Field(default=10, description="Maximum concurrent replay operations")
    timeout_seconds: Optional[float] = Field(None, description="Timeout for individual replays")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed replays")
    retry_delay_seconds: float = Field(default=1.0, description="Delay between retry attempts")
    continue_on_failure: bool = Field(default=True, description="Continue batch even if some replays fail")
    replay_mode: ReplayMode = Field(default=ReplayMode.TOLERANT, description="Default replay mode")
    enable_diff_analysis: bool = Field(default=True, description="Enable detailed diff analysis")
    enable_policy_validation: bool = Field(default=True, description="Enable policy validation")
    save_results: bool = Field(default=True, description="Save results to storage")

    @field_validator('max_concurrent_replays')
    def validate_concurrency(cls, v):
        if v < 1:
            raise ValueError("max_concurrent_replays must be at least 1")
        return v


class ReplayTask(BaseModel):
    """Represents a single replay task within a batch."""
    model_config = ConfigDict(frozen=True)

    task_id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    snapshot: Snapshot = Field(..., description="Snapshot to replay")
    context: Optional[ReplayContext] = Field(None, description="Custom replay context")
    priority: int = Field(default=0, description="Task priority (higher = more important)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom task metadata")


class BatchReplayResult(BaseModel):
    """Result of a batch replay operation."""
    model_config = ConfigDict(frozen=True)

    config: BatchReplayConfig = Field(..., description="Configuration used for the batch")
    status: BatchStatus = Field(..., description="Overall status of the batch")
    start_time: datetime = Field(..., description="When the batch started")
    end_time: Optional[datetime] = Field(None, description="When the batch completed")
    total_tasks: int = Field(..., description="Total number of tasks")
    successful_replays: int = Field(default=0, description="Number of successful replays")
    failed_replays: int = Field(default=0, description="Number of failed replays")
    cancelled_replays: int = Field(default=0, description="Number of cancelled replays")
    total_execution_time_ms: float = Field(default=0, description="Total execution time")
    replay_results: List[ReplayResult] = Field(default_factory=list, description="Individual replay results")
    diff_results: List[DiffResult] = Field(default_factory=list, description="Diff analysis results")
    policy_results: List[PolicyResult] = Field(default_factory=list, description="Policy validation results")
    error_summary: Dict[str, int] = Field(default_factory=dict, description="Summary of errors by type")

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_tasks == 0:
            return 100.0
        return (self.successful_replays / self.total_tasks) * 100

    @property
    def duration_seconds(self) -> float:
        """Duration of the batch operation in seconds."""
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def get_failed_tasks(self) -> List[ReplayResult]:
        """Get results for failed replay tasks."""
        return [result for result in self.replay_results if not result.success]

    def get_critical_policy_violations(self) -> List[PolicyResult]:
        """Get policy results with critical violations."""
        return [result for result in self.policy_results
                if not result.passed and result.critical_violations]


class ReplayScheduler:
    """Scheduler for managing replay operations over time."""

    def __init__(self):
        self.scheduled_batches: Dict[datetime, BatchReplayConfig] = {}
        self.recurring_schedules: Dict[str, Callable] = {}
        self.running = False

    def schedule_batch(
        self,
        config: BatchReplayConfig,
        run_time: datetime,
        snapshots: List[Snapshot]
    ) -> None:
        """Schedule a batch replay to run at a specific time."""
        # Store configuration with snapshots
        config_with_snapshots = {
            'config': config,
            'snapshots': snapshots
        }
        self.scheduled_batches[run_time] = config_with_snapshots

    def schedule_recurring(
        self,
        name: str,
        interval: timedelta,
        config_factory: Callable[[], Tuple[BatchReplayConfig, List[Snapshot]]]
    ) -> None:
        """Schedule a recurring batch replay."""
        self.recurring_schedules[name] = {
            'interval': interval,
            'config_factory': config_factory,
            'last_run': None
        }

    async def start_scheduler(self) -> None:
        """Start the scheduler background task."""
        self.running = True
        while self.running:
            await self._check_and_run_scheduled()
            await asyncio.sleep(60)  # Check every minute

    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        self.running = False

    async def _check_and_run_scheduled(self) -> None:
        """Check for scheduled tasks that should run."""
        now = _utcnow()

        # Check one-time schedules
        due_schedules = [time for time in self.scheduled_batches.keys() if time <= now]
        for schedule_time in due_schedules:
            config_data = self.scheduled_batches.pop(schedule_time)
            orchestrator = ReplayOrchestrator()
            await orchestrator.run_batch_replay(
                config_data['snapshots'],
                config_data['config']
            )

        # Check recurring schedules
        for name, schedule in self.recurring_schedules.items():
            last_run = schedule.get('last_run')
            interval = schedule['interval']

            if last_run is None or (now - last_run) >= interval:
                config, snapshots = schedule['config_factory']()
                orchestrator = ReplayOrchestrator()
                await orchestrator.run_batch_replay(snapshots, config)
                schedule['last_run'] = now


class ReplayOrchestrator:
    """
    Orchestrates batch replay operations with parallel execution,
    failure handling, and comprehensive reporting.
    """

    def __init__(
        self,
        replay_engine: Optional[ReplayEngine] = None,
        diff_engine: Optional[DiffEngine] = None,
        policy_framework: Optional[PolicyFramework] = None,
        serializer: Optional[SnapshotSerializer] = None
    ):
        """
        Initialize the replay orchestrator.

        Args:
            replay_engine: Replay engine for executing replays
            diff_engine: Diff engine for comparison analysis
            policy_framework: Policy framework for validation
            serializer: Serializer for data handling
        """
        self.replay_engine = replay_engine or ReplayEngine()
        self.diff_engine = diff_engine or DiffEngine()
        self.policy_framework = policy_framework or PolicyFramework()
        self.serializer = serializer or SnapshotSerializer()
        self.logger = logging.getLogger(__name__)

        self._active_batches: Set[UUID] = set()
        self._cancelled_batches: Set[UUID] = set()

    async def run_batch_replay(
        self,
        snapshots: List[Snapshot],
        config: Optional[BatchReplayConfig] = None
    ) -> BatchReplayResult:
        """
        Run a batch replay operation on multiple snapshots.

        Args:
            snapshots: List of snapshots to replay
            config: Batch configuration (default if not provided)

        Returns:
            BatchReplayResult with comprehensive results
        """
        if config is None:
            config = BatchReplayConfig()

        if config.batch_id in self._active_batches:
            raise ValueError(f"Batch {config.batch_id} is already running")

        self._active_batches.add(config.batch_id)
        start_time = _utcnow()

        try:
            # Create tasks from snapshots
            tasks = [
                ReplayTask(snapshot=snapshot, priority=i)
                for i, snapshot in enumerate(snapshots)
            ]

            self.logger.info(f"Starting batch replay {config.batch_id} with {len(tasks)} tasks")

            # Execute tasks with concurrency control
            replay_results = await self._execute_tasks_parallel(tasks, config)

            # Run diff analysis if enabled
            diff_results = []
            if config.enable_diff_analysis:
                diff_results = await self._run_diff_analysis(replay_results)

            # Run policy validation if enabled
            policy_results = []
            if config.enable_policy_validation:
                policy_results = await self._run_policy_validation(replay_results)

            # Calculate statistics
            successful = sum(1 for result in replay_results if result.success)
            failed = sum(1 for result in replay_results if result.failed)
            total_time = sum(result.execution_time_ms for result in replay_results)

            # Create error summary
            error_summary = self._create_error_summary(replay_results)

            end_time = _utcnow()
            status = self._determine_batch_status(successful, failed, len(tasks), config)

            result = BatchReplayResult(
                config=config,
                status=status,
                start_time=start_time,
                end_time=end_time,
                total_tasks=len(tasks),
                successful_replays=successful,
                failed_replays=failed,
                total_execution_time_ms=total_time,
                replay_results=replay_results,
                diff_results=diff_results,
                policy_results=policy_results,
                error_summary=error_summary
            )

            self.logger.info(
                f"Completed batch replay {config.batch_id}: "
                f"{successful}/{len(tasks)} successful ({result.success_rate:.1f}%)"
            )

            return result

        except Exception as e:
            self.logger.error(f"Batch replay {config.batch_id} failed: {str(e)}")
            raise

        finally:
            self._active_batches.discard(config.batch_id)
            self._cancelled_batches.discard(config.batch_id)

    async def run_from_files(
        self,
        file_paths: List[Union[str, Path]],
        config: Optional[BatchReplayConfig] = None
    ) -> BatchReplayResult:
        """
        Run batch replay from snapshot files.

        Args:
            file_paths: List of file paths containing snapshots
            config: Batch configuration

        Returns:
            BatchReplayResult
        """
        snapshots = []

        for file_path in file_paths:
            try:
                path = Path(file_path)
                with open(path, 'r') as f:
                    data = f.read()
                snapshot = self.serializer.deserialize_snapshot(data)
                snapshots.append(snapshot)
            except Exception as e:
                self.logger.error(f"Failed to load snapshot from {file_path}: {str(e)}")
                continue

        return await self.run_batch_replay(snapshots, config)

    def cancel_batch(self, batch_id: UUID) -> bool:
        """
        Cancel a running batch replay.

        Args:
            batch_id: ID of the batch to cancel

        Returns:
            True if batch was cancelled, False if not found
        """
        if batch_id in self._active_batches:
            self._cancelled_batches.add(batch_id)
            self.logger.info(f"Batch replay {batch_id} marked for cancellation")
            return True
        return False

    def get_active_batches(self) -> Set[UUID]:
        """Get set of currently active batch IDs."""
        return self._active_batches.copy()

    async def _execute_tasks_parallel(
        self,
        tasks: List[ReplayTask],
        config: BatchReplayConfig
    ) -> List[ReplayResult]:
        """Execute replay tasks with parallel execution and retry logic."""
        results = []
        semaphore = asyncio.Semaphore(config.max_concurrent_replays)

        async def execute_single_task(task: ReplayTask) -> ReplayResult:
            async with semaphore:
                # Check for cancellation
                if config.batch_id in self._cancelled_batches:
                    from .engine import ReplayStatus
                    return ReplayResult(
                        context=ReplayContext(
                            replay_id=task.task_id,
                            original_snapshot_id=task.snapshot.metadata.snapshot_id
                        ),
                        status=ReplayStatus.FAILED,
                        original_snapshot=task.snapshot,
                        replayed_snapshot=None,
                        execution_time_ms=0.0,
                        error_message="Batch was cancelled"
                    )

                # Execute with retry logic
                last_error = None
                for attempt in range(config.retry_attempts):
                    try:
                        context = task.context or ReplayContext(
                            replay_id=task.task_id,
                            original_snapshot_id=task.snapshot.metadata.snapshot_id,
                            mode=config.replay_mode,
                            timeout_seconds=config.timeout_seconds
                        )

                        result = await self.replay_engine.replay_snapshot(task.snapshot, context)

                        if result.success or not config.continue_on_failure:
                            return result

                        last_error = result.error_message

                    except Exception as e:
                        last_error = str(e)
                        self.logger.warning(
                            f"Retry {attempt + 1}/{config.retry_attempts} failed for task {task.task_id}: {str(e)}"
                        )

                        if attempt < config.retry_attempts - 1:
                            await asyncio.sleep(config.retry_delay_seconds)

                # All retries failed
                from .engine import ReplayStatus
                return ReplayResult(
                    context=ReplayContext(
                        replay_id=task.task_id,
                        original_snapshot_id=task.snapshot.metadata.snapshot_id
                    ),
                    status=ReplayStatus.FAILED,
                    original_snapshot=task.snapshot,
                    replayed_snapshot=None,
                    execution_time_ms=0.0,
                    error_message=f"All {config.retry_attempts} retry attempts failed. Last error: {last_error}"
                )

        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        # Execute all tasks
        task_coroutines = [execute_single_task(task) for task in sorted_tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Task {sorted_tasks[i].task_id} raised exception: {str(result)}")
                from .engine import ReplayStatus
                final_results.append(ReplayResult(
                    context=ReplayContext(
                        replay_id=sorted_tasks[i].task_id,
                        original_snapshot_id=sorted_tasks[i].snapshot.metadata.snapshot_id
                    ),
                    status=ReplayStatus.FAILED,
                    original_snapshot=sorted_tasks[i].snapshot,
                    replayed_snapshot=None,
                    execution_time_ms=0.0,
                    error_message=f"Exception during execution: {str(result)}"
                ))
            else:
                final_results.append(result)

        return final_results

    async def _run_diff_analysis(self, replay_results: List[ReplayResult]) -> List[DiffResult]:
        """Run diff analysis on replay results."""
        diff_results = []

        for replay_result in replay_results:
            if replay_result.success and replay_result.replayed_snapshot:
                try:
                    diff_result = self.diff_engine.compare_snapshots(
                        replay_result.original_snapshot,
                        replay_result.replayed_snapshot
                    )
                    diff_results.append(diff_result)
                except Exception as e:
                    self.logger.error(f"Diff analysis failed for snapshot {replay_result.context.replay_id}: {str(e)}")

        return diff_results

    async def _run_policy_validation(self, replay_results: List[ReplayResult]) -> List[PolicyResult]:
        """Run policy validation on replay results."""
        policy_results = []

        for replay_result in replay_results:
            if replay_result.success:
                try:
                    results = await self.policy_framework.evaluate_replay_result(replay_result)
                    policy_results.extend(results)
                except Exception as e:
                    self.logger.error(f"Policy validation failed for snapshot {replay_result.context.replay_id}: {str(e)}")

        return policy_results

    def _create_error_summary(self, replay_results: List[ReplayResult]) -> Dict[str, int]:
        """Create a summary of errors by type."""
        error_summary = {}

        for result in replay_results:
            if result.failed and result.error_message:
                # Categorize errors
                error_key = self._categorize_error(result.error_message)
                error_summary[error_key] = error_summary.get(error_key, 0) + 1

        return error_summary

    def _categorize_error(self, error_message: str) -> str:
        """Categorize an error message."""
        message_lower = error_message.lower()

        if "timeout" in message_lower:
            return "timeout"
        elif "memory" in message_lower:
            return "memory"
        elif "network" in message_lower:
            return "network"
        elif "permission" in message_lower:
            return "permission"
        elif "validation" in message_lower:
            return "validation"
        elif "serialization" in message_lower:
            return "serialization"
        else:
            return "other"

    def _determine_batch_status(
        self,
        successful: int,
        failed: int,
        total: int,
        config: BatchReplayConfig
    ) -> BatchStatus:
        """Determine the overall status of the batch."""
        if config.batch_id in self._cancelled_batches:
            return BatchStatus.CANCELLED

        if failed == 0:
            return BatchStatus.COMPLETED
        elif successful == 0:
            return BatchStatus.FAILED
        else:
            return BatchStatus.PARTIAL


# Convenience functions for common orchestration operations

async def quick_batch_replay(snapshots: List[Snapshot]) -> BatchReplayResult:
    """
    Quick batch replay with default settings.

    Args:
        snapshots: Snapshots to replay

    Returns:
        BatchReplayResult
    """
    orchestrator = ReplayOrchestrator()
    return await orchestrator.run_batch_replay(snapshots)


async def batch_replay_from_directory(directory: Union[str, Path]) -> BatchReplayResult:
    """
    Run batch replay on all snapshot files in a directory.

    Args:
        directory: Directory containing snapshot files

    Returns:
        BatchReplayResult
    """
    dir_path = Path(directory)
    snapshot_files = list(dir_path.glob("*.json"))

    orchestrator = ReplayOrchestrator()
    return await orchestrator.run_from_files(snapshot_files)
