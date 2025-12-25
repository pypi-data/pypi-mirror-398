"""
Briefcase SDK Client - Main interface for interacting with Briefcase.

This module provides the primary client interface for capturing, storing,
and retrieving AI decision snapshots.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .capture import BriefcaseInstrument, capture_decision, create_context
from .models import (
    DecisionSnapshot,
    ExecutionContext,
    ModelParameters,
    Snapshot,
    SnapshotMetadata,
)
from .serialization import SnapshotSerializer, serialize_snapshot, deserialize_snapshot


class BriefcaseClient:
    """
    Main client interface for Briefcase SDK.

    This class provides a high-level interface for capturing, storing, and
    retrieving AI decision snapshots with deterministic replay capabilities.
    """

    def __init__(
        self,
        auto_capture: bool = True,
        storage_backend: Optional[Any] = None,
        serializer: Optional[SnapshotSerializer] = None,
        default_context: Optional[ExecutionContext] = None,
    ):
        """
        Initialize the Briefcase client.

        Args:
            auto_capture: Whether to automatically capture instrumented functions
            storage_backend: Storage backend for persisting snapshots (optional)
            serializer: Custom serializer for snapshots (uses default if None)
            default_context: Default execution context for all snapshots
        """
        self.auto_capture = auto_capture
        self.storage_backend = storage_backend
        self.serializer = serializer or SnapshotSerializer()
        self.default_context = default_context

        # In-memory snapshot storage (for OSS version)
        self._snapshots: Dict[UUID, Snapshot] = {}
        self._decisions: Dict[UUID, DecisionSnapshot] = {}

    def instrument(
        self,
        function_name: Optional[str] = None,
        model_parameters: Optional[ModelParameters] = None,
        context: Optional[ExecutionContext] = None,
        capture_inputs: bool = True,
        capture_outputs: bool = True,
        auto_serialize: bool = True,
    ) -> BriefcaseInstrument:
        """
        Create an instrumentation context for capturing decisions.

        Args:
            function_name: Name for the instrumented function
            model_parameters: Model parameters to include
            context: Execution context (uses default if None)
            capture_inputs: Whether to capture function inputs
            capture_outputs: Whether to capture function outputs
            auto_serialize: Whether to automatically serialize complex objects

        Returns:
            BriefcaseInstrument: Instrumentation context manager
        """
        effective_context = context or self.default_context or ExecutionContext()

        instrument = BriefcaseInstrument(
            function_name=function_name,
            model_parameters=model_parameters,
            context=effective_context,
            capture_inputs=capture_inputs,
            capture_outputs=capture_outputs,
            auto_serialize=auto_serialize,
        )

        return instrument

    def capture_manual_decision(
        self,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        model_parameters: Optional[ModelParameters] = None,
        context: Optional[ExecutionContext] = None,
        function_name: str = "manual_decision",
    ) -> DecisionSnapshot:
        """
        Manually capture a decision snapshot.

        Args:
            inputs: Dictionary of inputs
            outputs: Dictionary of outputs
            model_parameters: Model parameters
            context: Execution context
            function_name: Name for the decision

        Returns:
            The captured decision snapshot
        """
        effective_context = context or self.default_context or ExecutionContext()

        decision = capture_decision(
            inputs=inputs,
            outputs=outputs,
            model_parameters=model_parameters,
            context=effective_context,
            function_name=function_name,
        )

        # Store the decision if auto_capture is enabled
        if self.auto_capture:
            self._decisions[decision.metadata.snapshot_id] = decision

        return decision

    def save_snapshot(self, snapshot: Snapshot) -> UUID:
        """
        Save a snapshot to storage.

        Args:
            snapshot: The snapshot to save

        Returns:
            The snapshot ID
        """
        snapshot_id = snapshot.metadata.snapshot_id
        self._snapshots[snapshot_id] = snapshot

        # Also index all decisions in the snapshot
        for decision in snapshot.decisions:
            self._decisions[decision.metadata.snapshot_id] = decision

        # If we have a storage backend, use it
        if self.storage_backend:
            self._persist_snapshot(snapshot)

        return snapshot_id

    def save_decision(self, decision: DecisionSnapshot) -> UUID:
        """
        Save a decision snapshot to storage.

        Args:
            decision: The decision snapshot to save

        Returns:
            The decision snapshot ID
        """
        decision_id = decision.metadata.snapshot_id
        self._decisions[decision_id] = decision

        # If we have a storage backend, use it
        if self.storage_backend:
            self._persist_decision(decision)

        return decision_id

    def get_snapshot(self, snapshot_id: UUID) -> Optional[Snapshot]:
        """
        Retrieve a snapshot by ID.

        Args:
            snapshot_id: The snapshot ID to retrieve

        Returns:
            The snapshot if found, None otherwise
        """
        # Try in-memory storage first
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot:
            return snapshot

        # Try storage backend if available
        if self.storage_backend:
            return self._retrieve_snapshot(snapshot_id)

        return None

    def get_decision(self, decision_id: UUID) -> Optional[DecisionSnapshot]:
        """
        Retrieve a decision snapshot by ID.

        Args:
            decision_id: The decision snapshot ID to retrieve

        Returns:
            The decision snapshot if found, None otherwise
        """
        # Try in-memory storage first
        decision = self._decisions.get(decision_id)
        if decision:
            return decision

        # Try storage backend if available
        if self.storage_backend:
            return self._retrieve_decision(decision_id)

        return None

    def list_snapshots(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Snapshot]:
        """
        List snapshots with optional filtering.

        Args:
            limit: Maximum number of snapshots to return
            offset: Number of snapshots to skip
            filters: Dictionary of filters to apply

        Returns:
            List of matching snapshots
        """
        snapshots = list(self._snapshots.values())

        # Apply filters if provided
        if filters:
            snapshots = self._apply_snapshot_filters(snapshots, filters)

        # Apply pagination
        if offset > 0:
            snapshots = snapshots[offset:]
        if limit is not None:
            snapshots = snapshots[:limit]

        return snapshots

    def list_decisions(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DecisionSnapshot]:
        """
        List decision snapshots with optional filtering.

        Args:
            limit: Maximum number of decisions to return
            offset: Number of decisions to skip
            filters: Dictionary of filters to apply

        Returns:
            List of matching decision snapshots
        """
        decisions = list(self._decisions.values())

        # Apply filters if provided
        if filters:
            decisions = self._apply_decision_filters(decisions, filters)

        # Apply pagination
        if offset > 0:
            decisions = decisions[offset:]
        if limit is not None:
            decisions = decisions[:limit]

        return decisions

    def export_snapshot(self, snapshot_id: UUID) -> Optional[str]:
        """
        Export a snapshot as a JSON string.

        Args:
            snapshot_id: The snapshot ID to export

        Returns:
            JSON string representation of the snapshot, or None if not found
        """
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            return None

        return self.serializer.serialize_snapshot(snapshot)

    def import_snapshot(self, data: Union[str, Dict[str, Any]]) -> UUID:
        """
        Import a snapshot from JSON string or dictionary.

        Args:
            data: Serialized snapshot data

        Returns:
            The imported snapshot ID

        Raises:
            ValueError: If the data is invalid
        """
        snapshot = self.serializer.deserialize_snapshot(data)
        return self.save_snapshot(snapshot)

    def create_context(
        self,
        session_id: Optional[UUID] = None,
        trace_id: Optional[UUID] = None,
        parent_trace_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        environment: str = "production",
        tags: Optional[Dict[str, str]] = None,
    ) -> ExecutionContext:
        """
        Create a new execution context.

        Args:
            session_id: Session identifier
            trace_id: Trace identifier
            parent_trace_id: Parent trace ID
            user_id: User identifier
            environment: Environment name
            tags: Custom tags

        Returns:
            The created execution context
        """
        return ExecutionContext(
            session_id=session_id,
            trace_id=trace_id,
            parent_trace_id=parent_trace_id,
            user_id=user_id,
            environment=environment,
            tags=tags or {},
        )

    def create_snapshot(
        self,
        decisions: Optional[List[DecisionSnapshot]] = None,
        metadata: Optional[SnapshotMetadata] = None,
        snapshot_type: str = "decision",
    ) -> Snapshot:
        """
        Create a new snapshot with the given decisions.

        Args:
            decisions: List of decision snapshots to include
            metadata: Custom metadata (created if not provided)
            snapshot_type: Type of snapshot

        Returns:
            The created snapshot
        """
        return Snapshot(
            metadata=metadata or SnapshotMetadata(),
            decisions=decisions or [],
            snapshot_type=snapshot_type,
        )

    def clear_storage(self) -> None:
        """Clear all in-memory storage."""
        self._snapshots.clear()
        self._decisions.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored snapshots and decisions.

        Returns:
            Dictionary with storage statistics
        """
        return {
            "total_snapshots": len(self._snapshots),
            "total_decisions": len(self._decisions),
            "memory_snapshots": len(self._snapshots),
            "memory_decisions": len(self._decisions),
            "has_storage_backend": self.storage_backend is not None,
        }

    # Private methods for storage backend integration

    def _persist_snapshot(self, snapshot: Snapshot) -> None:
        """Persist a snapshot using the storage backend."""
        if hasattr(self.storage_backend, 'save_snapshot'):
            self.storage_backend.save_snapshot(snapshot)

    def _persist_decision(self, decision: DecisionSnapshot) -> None:
        """Persist a decision using the storage backend."""
        if hasattr(self.storage_backend, 'save_decision'):
            self.storage_backend.save_decision(decision)

    def _retrieve_snapshot(self, snapshot_id: UUID) -> Optional[Snapshot]:
        """Retrieve a snapshot using the storage backend."""
        if hasattr(self.storage_backend, 'get_snapshot'):
            return self.storage_backend.get_snapshot(snapshot_id)
        return None

    def _retrieve_decision(self, decision_id: UUID) -> Optional[DecisionSnapshot]:
        """Retrieve a decision using the storage backend."""
        if hasattr(self.storage_backend, 'get_decision'):
            return self.storage_backend.get_decision(decision_id)
        return None

    def _apply_snapshot_filters(
        self, snapshots: List[Snapshot], filters: Dict[str, Any]
    ) -> List[Snapshot]:
        """Apply filters to a list of snapshots."""
        filtered = snapshots

        # Filter by snapshot type
        if 'snapshot_type' in filters:
            filtered = [s for s in filtered if s.snapshot_type == filters['snapshot_type']]

        # Filter by environment
        if 'environment' in filters:
            filtered = [
                s for s in filtered
                if any(d.context.environment == filters['environment'] for d in s.decisions)
            ]

        # Filter by user ID
        if 'user_id' in filters:
            filtered = [
                s for s in filtered
                if any(d.context.user_id == filters['user_id'] for d in s.decisions)
            ]

        # Filter by function name
        if 'function_name' in filters:
            filtered = [
                s for s in filtered
                if any(d.function_name == filters['function_name'] for d in s.decisions)
            ]

        return filtered

    def _apply_decision_filters(
        self, decisions: List[DecisionSnapshot], filters: Dict[str, Any]
    ) -> List[DecisionSnapshot]:
        """Apply filters to a list of decision snapshots."""
        filtered = decisions

        # Filter by function name
        if 'function_name' in filters:
            filtered = [d for d in filtered if d.function_name == filters['function_name']]

        # Filter by environment
        if 'environment' in filters:
            filtered = [d for d in filtered if d.context.environment == filters['environment']]

        # Filter by user ID
        if 'user_id' in filters:
            filtered = [d for d in filtered if d.context.user_id == filters['user_id']]

        # Filter by module name
        if 'module_name' in filters:
            filtered = [d for d in filtered if d.module_name == filters['module_name']]

        # Filter by error status
        if 'has_error' in filters:
            has_error = filters['has_error']
            if has_error:
                filtered = [d for d in filtered if d.error is not None]
            else:
                filtered = [d for d in filtered if d.error is None]

        return filtered


# Global client instance for convenience
_default_client = BriefcaseClient()


def get_default_client() -> BriefcaseClient:
    """Get the default global Briefcase client."""
    return _default_client


def set_default_client(client: BriefcaseClient) -> None:
    """Set the default global Briefcase client."""
    global _default_client
    _default_client = client