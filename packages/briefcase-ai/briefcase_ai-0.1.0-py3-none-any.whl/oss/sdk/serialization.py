"""
Serialization and deserialization utilities for Briefcase snapshots.

This module provides deterministic serialization to ensure reproducible
snapshots across different environments and platforms.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import ValidationError

from .models import DecisionSnapshot, Snapshot, SerializedSnapshot, SnapshotDict


class SnapshotSerializer:
    """
    Handles serialization and deserialization of Briefcase snapshots.

    Ensures deterministic output for reproducible snapshots.
    """

    def __init__(
        self,
        sort_keys: bool = True,
        indent: Optional[int] = None,
        ensure_ascii: bool = False,
        include_checksum: bool = True,
    ):
        """
        Initialize the serializer.

        Args:
            sort_keys: Sort dictionary keys for deterministic output
            indent: JSON indentation level (None for compact output)
            ensure_ascii: Escape non-ASCII characters
            include_checksum: Whether to include data integrity checksums
        """
        self.sort_keys = sort_keys
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.include_checksum = include_checksum

    def serialize_snapshot(self, snapshot: Snapshot) -> str:
        """
        Serialize a snapshot to JSON string.

        Args:
            snapshot: The snapshot to serialize

        Returns:
            JSON string representation of the snapshot
        """
        snapshot_dict = self._snapshot_to_dict(snapshot)

        # Add checksum if requested
        if self.include_checksum:
            checksum = self._calculate_checksum(snapshot_dict)
            # Make a copy to avoid mutating the original
            snapshot_dict = self._deep_copy_dict(snapshot_dict)
            snapshot_dict["metadata"]["checksum"] = checksum

        return json.dumps(
            snapshot_dict,
            sort_keys=self.sort_keys,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            default=self._json_default,
        )

    def deserialize_snapshot(self, data: Union[str, bytes, Dict[str, Any]]) -> Snapshot:
        """
        Deserialize a snapshot from JSON string or dictionary.

        Args:
            data: Serialized snapshot data

        Returns:
            Deserialized Snapshot object

        Raises:
            ValueError: If the data is invalid or checksum verification fails
            ValidationError: If the data doesn't match the snapshot schema
        """
        if isinstance(data, (str, bytes)):
            snapshot_dict = json.loads(data)
        elif isinstance(data, dict):
            snapshot_dict = data
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        # Verify checksum if present
        if self.include_checksum and "metadata" in snapshot_dict:
            stored_checksum = snapshot_dict.get("metadata", {}).get("checksum")
            if stored_checksum:
                # Create a copy without checksum for verification
                dict_for_checksum = self._deep_copy_dict(snapshot_dict)
                if "checksum" in dict_for_checksum.get("metadata", {}):
                    dict_for_checksum["metadata"]["checksum"] = None
                calculated_checksum = self._calculate_checksum(dict_for_checksum)

                if stored_checksum != calculated_checksum:
                    raise ValueError("Checksum verification failed - data may be corrupted")

        try:
            return Snapshot.model_validate(snapshot_dict)
        except ValidationError as e:
            raise ValidationError(f"Invalid snapshot data: {e}")

    def serialize_decision(self, decision: DecisionSnapshot) -> str:
        """
        Serialize a single decision snapshot to JSON string.

        Args:
            decision: The decision snapshot to serialize

        Returns:
            JSON string representation of the decision
        """
        decision_dict = self._decision_to_dict(decision)

        # Add checksum if requested
        if self.include_checksum:
            checksum = self._calculate_checksum(decision_dict)
            # Make a copy to avoid mutating the original
            decision_dict = self._deep_copy_dict(decision_dict)
            decision_dict["metadata"]["checksum"] = checksum

        return json.dumps(
            decision_dict,
            sort_keys=self.sort_keys,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            default=self._json_default,
        )

    def deserialize_decision(self, data: Union[str, bytes, Dict[str, Any]]) -> DecisionSnapshot:
        """
        Deserialize a decision snapshot from JSON string or dictionary.

        Args:
            data: Serialized decision snapshot data

        Returns:
            Deserialized DecisionSnapshot object

        Raises:
            ValueError: If the data is invalid or checksum verification fails
            ValidationError: If the data doesn't match the decision schema
        """
        if isinstance(data, (str, bytes)):
            decision_dict = json.loads(data)
        elif isinstance(data, dict):
            decision_dict = data
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        # Verify checksum if present
        if self.include_checksum and "metadata" in decision_dict:
            stored_checksum = decision_dict.get("metadata", {}).get("checksum")
            if stored_checksum:
                # Create a copy without checksum for verification
                dict_for_checksum = self._deep_copy_dict(decision_dict)
                if "checksum" in dict_for_checksum.get("metadata", {}):
                    dict_for_checksum["metadata"]["checksum"] = None
                calculated_checksum = self._calculate_checksum(dict_for_checksum)

                if stored_checksum != calculated_checksum:
                    raise ValueError("Checksum verification failed - data may be corrupted")

        try:
            return DecisionSnapshot.model_validate(decision_dict)
        except ValidationError as e:
            raise ValidationError(f"Invalid decision snapshot data: {e}")

    def _snapshot_to_dict(self, snapshot: Snapshot) -> SnapshotDict:
        """Convert a snapshot to a dictionary."""
        return snapshot.model_dump()

    def _decision_to_dict(self, decision: DecisionSnapshot) -> SnapshotDict:
        """Convert a decision snapshot to a dictionary."""
        return decision.model_dump()

    def _calculate_checksum(self, data: SnapshotDict) -> str:
        """
        Calculate SHA-256 checksum for data integrity.

        Args:
            data: Dictionary to calculate checksum for

        Returns:
            Hexadecimal checksum string
        """
        # Convert to deterministic JSON string
        json_str = json.dumps(
            data,
            sort_keys=True,
            ensure_ascii=True,
            default=self._json_default,
        )

        # Calculate SHA-256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _json_default(self, obj: Any) -> Any:
        """
        JSON serializer for objects not serializable by default.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'dict'):
            # For Pydantic models
            return obj.dict()
        else:
            return str(obj)

    def _deep_copy_dict(self, original: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary."""
        return json.loads(json.dumps(original, default=self._json_default))


# Module-level convenience functions
_default_serializer = SnapshotSerializer()


def serialize_snapshot(snapshot: Snapshot, **kwargs) -> str:
    """
    Serialize a snapshot using the default serializer.

    Args:
        snapshot: The snapshot to serialize
        **kwargs: Additional arguments passed to SnapshotSerializer

    Returns:
        JSON string representation of the snapshot
    """
    if kwargs:
        serializer = SnapshotSerializer(**kwargs)
        return serializer.serialize_snapshot(snapshot)
    return _default_serializer.serialize_snapshot(snapshot)


def deserialize_snapshot(data: SerializedSnapshot, **kwargs) -> Snapshot:
    """
    Deserialize a snapshot using the default serializer.

    Args:
        data: Serialized snapshot data
        **kwargs: Additional arguments passed to SnapshotSerializer

    Returns:
        Deserialized Snapshot object
    """
    if kwargs:
        serializer = SnapshotSerializer(**kwargs)
        return serializer.deserialize_snapshot(data)
    return _default_serializer.deserialize_snapshot(data)


def serialize_decision(decision: DecisionSnapshot, **kwargs) -> str:
    """
    Serialize a decision snapshot using the default serializer.

    Args:
        decision: The decision snapshot to serialize
        **kwargs: Additional arguments passed to SnapshotSerializer

    Returns:
        JSON string representation of the decision
    """
    if kwargs:
        serializer = SnapshotSerializer(**kwargs)
        return serializer.serialize_decision(decision)
    return _default_serializer.serialize_decision(decision)


def deserialize_decision(data: SerializedSnapshot, **kwargs) -> DecisionSnapshot:
    """
    Deserialize a decision snapshot using the default serializer.

    Args:
        data: Serialized decision snapshot data
        **kwargs: Additional arguments passed to SnapshotSerializer

    Returns:
        Deserialized DecisionSnapshot object
    """
    if kwargs:
        serializer = SnapshotSerializer(**kwargs)
        return serializer.deserialize_decision(data)
    return _default_serializer.deserialize_decision(data)


def calculate_snapshot_hash(snapshot: Snapshot) -> str:
    """
    Calculate a hash for a snapshot for quick comparison.

    Args:
        snapshot: The snapshot to hash

    Returns:
        SHA-256 hash of the snapshot
    """
    serializer = SnapshotSerializer(include_checksum=False)
    snapshot_dict = serializer._snapshot_to_dict(snapshot)
    return serializer._calculate_checksum(snapshot_dict)


def validate_snapshot_integrity(data: SerializedSnapshot) -> bool:
    """
    Validate the integrity of serialized snapshot data.

    Args:
        data: Serialized snapshot data

    Returns:
        True if the data is valid and passes checksum verification
    """
    try:
        deserialize_snapshot(data)
        return True
    except (ValueError, ValidationError):
        return False
