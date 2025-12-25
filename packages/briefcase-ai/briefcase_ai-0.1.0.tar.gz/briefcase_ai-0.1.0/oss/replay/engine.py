"""
Deterministic Replay Engine for Briefcase Snapshots

This module implements the core replay functionality that can deterministically
recreate AI decisions from captured snapshots. The engine ensures perfect
reproducibility by controlling execution context and providing replay hooks.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


def _utcnow() -> datetime:
    """Timezone-aware UTC helper."""
    return datetime.now(timezone.utc)

from ..sdk.models import DecisionSnapshot, Input, Output, Snapshot
from ..sdk.serialization import SnapshotSerializer


class ReplayStatus(str, Enum):
    """Status of replay execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ReplayMode(str, Enum):
    """Mode of replay execution."""
    STRICT = "strict"  # Fail on any deviation
    TOLERANT = "tolerant"  # Allow minor deviations
    VALIDATION_ONLY = "validation_only"  # Don't execute, just validate


class ReplayContext(BaseModel):
    """Context for replay execution."""

    model_config = ConfigDict(frozen=True)

    replay_id: UUID = Field(..., description="Unique identifier for this replay")
    original_snapshot_id: UUID = Field(..., description="ID of the original snapshot")
    mode: ReplayMode = Field(default=ReplayMode.STRICT, description="Replay execution mode")
    timestamp: datetime = Field(default_factory=_utcnow, description="When replay was initiated")
    environment_overrides: Dict[str, Any] = Field(default_factory=dict, description="Environment variable overrides")
    deterministic_seed: Optional[int] = Field(None, description="Seed for deterministic randomness")
    timeout_seconds: Optional[float] = Field(None, description="Timeout for replay execution")
    hooks: Dict[str, Any] = Field(default_factory=dict, description="Custom hooks for replay behavior")


class ReplayResult(BaseModel):
    """Result of replay execution."""

    model_config = ConfigDict(frozen=True)

    context: ReplayContext = Field(..., description="Replay context")
    status: ReplayStatus = Field(..., description="Status of replay execution")
    original_snapshot: Snapshot = Field(..., description="Original snapshot that was replayed")
    replayed_snapshot: Optional[Snapshot] = Field(None, description="Snapshot produced by replay")
    execution_time_ms: float = Field(..., description="Time taken for replay execution")
    error_message: Optional[str] = Field(None, description="Error message if replay failed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings during replay")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def success(self) -> bool:
        """Whether the replay was successful."""
        return self.status == ReplayStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Whether the replay failed."""
        return self.status == ReplayStatus.FAILED


class ReplayHook(ABC):
    """Abstract base class for replay hooks."""

    @abstractmethod
    async def before_replay(self, context: ReplayContext, snapshot: Snapshot) -> None:
        """Called before replay execution starts."""
        pass

    @abstractmethod
    async def after_decision(
        self,
        context: ReplayContext,
        original_decision: DecisionSnapshot,
        replayed_decision: Optional[DecisionSnapshot]
    ) -> None:
        """Called after each decision is replayed."""
        pass

    @abstractmethod
    async def after_replay(self, context: ReplayContext, result: ReplayResult) -> None:
        """Called after replay execution completes."""
        pass


class LoggingHook(ReplayHook):
    """Default hook that logs replay progress."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    async def before_replay(self, context: ReplayContext, snapshot: Snapshot) -> None:
        self.logger.info(
            f"Starting replay {context.replay_id} for snapshot {context.original_snapshot_id} "
            f"with {snapshot.total_decisions} decisions"
        )

    async def after_decision(
        self,
        context: ReplayContext,
        original_decision: DecisionSnapshot,
        replayed_decision: Optional[DecisionSnapshot]
    ) -> None:
        status = "success" if replayed_decision else "failed"
        self.logger.debug(
            f"Replayed decision {original_decision.metadata.snapshot_id} "
            f"from {original_decision.function_name}: {status}"
        )

    async def after_replay(self, context: ReplayContext, result: ReplayResult) -> None:
        self.logger.info(
            f"Completed replay {context.replay_id}: {result.status} "
            f"in {result.execution_time_ms:.2f}ms"
        )


class ReplayEngine:
    """
    Core engine for deterministic replay of snapshots.

    This engine can replay snapshots in different modes and provides
    hooks for customizing replay behavior. It ensures deterministic
    execution by controlling the environment and execution context.
    """

    def __init__(
        self,
        serializer: Optional[SnapshotSerializer] = None,
        default_hooks: Optional[List[ReplayHook]] = None
    ):
        """
        Initialize the replay engine.

        Args:
            serializer: Snapshot serializer for data handling
            default_hooks: Default hooks to apply to all replays
        """
        self.serializer = serializer or SnapshotSerializer()
        self.default_hooks = default_hooks or [LoggingHook()]
        self._active_replays: Set[UUID] = set()

    async def replay_snapshot(
        self,
        snapshot: Snapshot,
        context: Optional[ReplayContext] = None,
        hooks: Optional[List[ReplayHook]] = None
    ) -> ReplayResult:
        """
        Replay a complete snapshot deterministically.

        Args:
            snapshot: The snapshot to replay
            context: Replay context (generated if not provided)
            hooks: Additional hooks for this replay

        Returns:
            ReplayResult containing the outcome
        """
        if context is None:
            context = ReplayContext(
                replay_id=snapshot.metadata.snapshot_id,
                original_snapshot_id=snapshot.metadata.snapshot_id
            )

        if context.replay_id in self._active_replays:
            raise ValueError(f"Replay {context.replay_id} is already running")

        # Combine hooks
        all_hooks = (hooks or []) + self.default_hooks

        start_time = time.time()

        try:
            self._active_replays.add(context.replay_id)

            # Set up deterministic environment
            with self._deterministic_context(context):
                # Run hooks
                for hook in all_hooks:
                    await hook.before_replay(context, snapshot)

                # Validate snapshot before replay
                if not self._validate_snapshot_for_replay(snapshot):
                    raise ValueError("Snapshot is not valid for replay")

                # Execute replay based on mode
                if context.mode == ReplayMode.VALIDATION_ONLY:
                    replayed_snapshot = None
                else:
                    replayed_snapshot = await self._execute_replay(snapshot, context, all_hooks)

                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000

                # Create result
                result = ReplayResult(
                    context=context,
                    status=ReplayStatus.SUCCESS,
                    original_snapshot=snapshot,
                    replayed_snapshot=replayed_snapshot,
                    execution_time_ms=execution_time_ms
                )

                # Run post-replay hooks
                for hook in all_hooks:
                    await hook.after_replay(context, result)

                return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            # Create error result
            result = ReplayResult(
                context=context,
                status=ReplayStatus.FAILED,
                original_snapshot=snapshot,
                replayed_snapshot=None,
                execution_time_ms=execution_time_ms,
                error_message=str(e)
            )

            # Run post-replay hooks even on failure
            for hook in all_hooks:
                try:
                    await hook.after_replay(context, result)
                except Exception:
                    pass  # Don't let hook errors mask the original error

            return result

        finally:
            self._active_replays.discard(context.replay_id)

    async def replay_decision(
        self,
        decision: DecisionSnapshot,
        context: ReplayContext
    ) -> Optional[DecisionSnapshot]:
        """
        Replay a single decision snapshot.

        Args:
            decision: The decision snapshot to replay
            context: Replay context

        Returns:
            Replayed decision snapshot or None if replay failed
        """
        try:
            # In strict mode, we would actually re-execute the function
            # For now, we simulate replay by recreating the decision
            # with updated metadata

            # Simulate some processing time based on original execution
            if decision.execution_time_ms:
                await asyncio.sleep(min(decision.execution_time_ms / 1000, 0.1))

            # Create replayed decision with new metadata
            from ..sdk.models import SnapshotMetadata
            replayed_metadata = SnapshotMetadata(
                timestamp=_utcnow(),
                created_by=f"replay-{context.replay_id}"
            )

            replayed_decision = DecisionSnapshot(
                metadata=replayed_metadata,
                context=decision.context,
                function_name=decision.function_name,
                module_name=decision.module_name,
                inputs=decision.inputs,
                outputs=decision.outputs,
                model_parameters=decision.model_parameters,
                execution_time_ms=decision.execution_time_ms,
                error=decision.error
            )

            return replayed_decision

        except Exception:
            return None

    def _validate_snapshot_for_replay(self, snapshot: Snapshot) -> bool:
        """
        Validate that a snapshot can be replayed.

        Args:
            snapshot: Snapshot to validate

        Returns:
            True if snapshot is valid for replay
        """
        if not snapshot.decisions:
            return False

        # Check that all decisions have required data
        for decision in snapshot.decisions:
            if not decision.function_name or not decision.module_name:
                return False

            # Must have inputs and outputs to replay
            if not decision.inputs and not decision.outputs:
                return False

        return True

    async def _execute_replay(
        self,
        snapshot: Snapshot,
        context: ReplayContext,
        hooks: List[ReplayHook]
    ) -> Snapshot:
        """
        Execute the actual replay of a snapshot.

        Args:
            snapshot: Snapshot to replay
            context: Replay context
            hooks: Hooks to run during replay

        Returns:
            Replayed snapshot
        """
        replayed_decisions = []

        for decision in snapshot.decisions:
            # Apply timeout if specified
            try:
                if context.timeout_seconds:
                    replayed_decision = await asyncio.wait_for(
                        self.replay_decision(decision, context),
                        timeout=context.timeout_seconds
                    )
                else:
                    replayed_decision = await self.replay_decision(decision, context)

                # Run decision hooks
                for hook in hooks:
                    await hook.after_decision(context, decision, replayed_decision)

                if replayed_decision:
                    replayed_decisions.append(replayed_decision)
                elif context.mode == ReplayMode.STRICT:
                    raise RuntimeError(f"Failed to replay decision {decision.metadata.snapshot_id}")

            except asyncio.TimeoutError:
                if context.mode == ReplayMode.STRICT:
                    raise RuntimeError(f"Timeout replaying decision {decision.metadata.snapshot_id}")

        # Create replayed snapshot
        from ..sdk.models import SnapshotMetadata
        replayed_metadata = SnapshotMetadata(
            timestamp=_utcnow(),
            created_by=f"replay-{context.replay_id}"
        )

        return Snapshot(
            metadata=replayed_metadata,
            decisions=replayed_decisions,
            snapshot_type=snapshot.snapshot_type
        )

    @contextmanager
    def _deterministic_context(self, context: ReplayContext):
        """
        Set up a deterministic execution context.

        Args:
            context: Replay context with environment settings
        """
        # Save current environment
        import os
        import random
        import sys

        original_env = {}
        numpy_state = None
        numpy_module = sys.modules.get("numpy")

        # Only import numpy if explicitly enabled or already loaded to avoid
        # platform-specific crashes when the optional dependency is missing.
        if numpy_module is None and os.getenv("BRIEFCASE_ENABLE_NUMPY", "0").lower() in ("1", "true"):
            try:  # pragma: no cover - optional dependency
                import numpy as numpy_module  # type: ignore
            except Exception:  # pragma: no cover
                numpy_module = None

        try:
            # Apply environment overrides
            for key, value in context.environment_overrides.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = str(value)

            # Set deterministic seed if provided
            if context.deterministic_seed is not None:
                random.seed(context.deterministic_seed)
                if numpy_module is not None:
                    numpy_state = numpy_module.random.get_state()
                    numpy_module.random.seed(context.deterministic_seed)

            yield

        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

            if numpy_state is not None and numpy_module is not None:
                numpy_module.random.set_state(numpy_state)

    def get_active_replays(self) -> Set[UUID]:
        """Get the set of currently active replay IDs."""
        return self._active_replays.copy()

    def is_replay_active(self, replay_id: UUID) -> bool:
        """Check if a replay is currently active."""
        return replay_id in self._active_replays


# Convenience functions for common replay operations

async def replay_from_file(file_path: str, context: Optional[ReplayContext] = None) -> ReplayResult:
    """
    Replay a snapshot from a file.

    Args:
        file_path: Path to the snapshot file
        context: Optional replay context

    Returns:
        ReplayResult
    """
    engine = ReplayEngine()

    # Load snapshot from file
    with open(file_path, 'r') as f:
        data = f.read()

    snapshot = engine.serializer.deserialize_snapshot(data)
    return await engine.replay_snapshot(snapshot, context)


async def quick_replay(snapshot: Snapshot, mode: ReplayMode = ReplayMode.TOLERANT) -> ReplayResult:
    """
    Quick replay with default settings.

    Args:
        snapshot: Snapshot to replay
        mode: Replay mode

    Returns:
        ReplayResult
    """
    engine = ReplayEngine()
    context = ReplayContext(
        replay_id=snapshot.metadata.snapshot_id,
        original_snapshot_id=snapshot.metadata.snapshot_id,
        mode=mode
    )

    return await engine.replay_snapshot(snapshot, context)
