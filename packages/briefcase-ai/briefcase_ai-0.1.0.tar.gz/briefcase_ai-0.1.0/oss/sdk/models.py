"""
Immutable snapshot data models for Briefcase.

These models define the core schema for capturing AI decisions and ensuring
deterministic replay. All models are immutable by design.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp helper."""
    return datetime.now(timezone.utc)


class ImmutableBase(BaseModel):
    """Base class for all immutable Briefcase models."""

    model_config = ConfigDict(frozen=True, use_enum_values=True)


class Input(ImmutableBase):
    """Represents input data to a decision point."""

    name: str = Field(..., description="Name or identifier for this input")
    value: Any = Field(..., description="The actual input value")
    data_type: str = Field(..., description="Type of the input data")
    schema_version: str = Field(default="1.0", description="Schema version for this input")

    @field_validator('data_type', mode='before')
    def validate_data_type(cls, v):
        """Ensure data_type is a string representation of the type."""
        if hasattr(v, '__name__'):
            return v.__name__
        return str(v)


class Output(ImmutableBase):
    """Represents output data from a decision point."""

    name: str = Field(..., description="Name or identifier for this output")
    value: Any = Field(..., description="The actual output value")
    data_type: str = Field(..., description="Type of the output data")
    confidence: Optional[float] = Field(None, description="Confidence score if applicable")
    schema_version: str = Field(default="1.0", description="Schema version for this output")

    @field_validator('data_type', mode='before')
    def validate_data_type(cls, v):
        """Ensure data_type is a string representation of the type."""
        if hasattr(v, '__name__'):
            return v.__name__
        return str(v)

    @field_validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1 if provided."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Confidence must be between 0 and 1")
        return v


class ModelParameters(ImmutableBase):
    """Represents model parameters and configuration."""

    model_name: str = Field(..., description="Name or identifier of the model")
    model_version: str = Field(..., description="Version of the model")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Hyperparameters")
    weights_hash: Optional[str] = Field(None, description="Hash of model weights for reproducibility")

    @field_validator('parameters', 'hyperparameters', mode='before')
    def ensure_dict(cls, v):
        """Ensure parameters are dictionaries."""
        return v if isinstance(v, dict) else {}


class ExecutionContext(ImmutableBase):
    """Represents the execution context of a decision."""

    session_id: UUID = Field(default_factory=uuid4, description="Session identifier")
    trace_id: UUID = Field(default_factory=uuid4, description="Trace identifier for the decision chain")
    parent_trace_id: Optional[UUID] = Field(None, description="Parent trace ID for nested decisions")
    user_id: Optional[str] = Field(None, description="User identifier if applicable")
    environment: str = Field(default="production", description="Environment (dev, staging, production)")
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags for categorization")

    @field_validator('tags', mode='before')
    def ensure_tags_dict(cls, v):
        """Ensure tags is a dictionary of strings."""
        if not isinstance(v, dict):
            return {}
        return {str(k): str(v) for k, v in v.items()}


class SnapshotMetadata(ImmutableBase):
    """Metadata for a snapshot."""

    snapshot_id: UUID = Field(default_factory=uuid4, description="Unique snapshot identifier")
    timestamp: datetime = Field(default_factory=_utcnow, description="When the snapshot was created")
    schema_version: str = Field(default="1.0", description="Schema version for the snapshot")
    sdk_version: str = Field(default="0.1.0", description="Briefcase SDK version")
    created_by: Optional[str] = Field(None, description="Creator of the snapshot")
    checksum: Optional[str] = Field(None, description="Checksum for data integrity")


class DecisionSnapshot(ImmutableBase):
    """Represents a complete decision snapshot."""

    metadata: SnapshotMetadata = Field(default_factory=SnapshotMetadata)
    context: ExecutionContext = Field(default_factory=ExecutionContext)
    function_name: str = Field(..., description="Name of the function being instrumented")
    module_name: str = Field(..., description="Module containing the function")
    inputs: List[Input] = Field(default_factory=list, description="All inputs to the decision")
    outputs: List[Output] = Field(default_factory=list, description="All outputs from the decision")
    model_parameters: Optional[ModelParameters] = Field(None, description="Model parameters if applicable")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if the decision failed")

    @field_validator('execution_time_ms')
    def validate_execution_time(cls, v):
        """Ensure execution time is positive if provided."""
        if v is not None and v < 0:
            raise ValueError("Execution time must be positive")
        return v


class Snapshot(ImmutableBase):
    """
    Root snapshot model that can contain one or more decision snapshots.

    This is the primary model for storing and replaying AI decisions.
    """

    metadata: SnapshotMetadata = Field(default_factory=SnapshotMetadata)
    decisions: List[DecisionSnapshot] = Field(default_factory=list, description="All decisions in this snapshot")
    snapshot_type: str = Field(default="decision", description="Type of snapshot (decision, batch, etc.)")

    def add_decision(self, decision: DecisionSnapshot) -> "Snapshot":
        """
        Add a decision to the snapshot.

        Since the model is immutable, this returns a new Snapshot instance.
        """
        new_decisions = self.decisions + [decision]
        return self.__class__(
            metadata=self.metadata,
            decisions=new_decisions,
            snapshot_type=self.snapshot_type,
        )

    def get_decision_by_id(self, snapshot_id: UUID) -> Optional[DecisionSnapshot]:
        """Get a specific decision by its snapshot ID."""
        for decision in self.decisions:
            if decision.metadata.snapshot_id == snapshot_id:
                return decision
        return None

    def get_decisions_by_function(self, function_name: str) -> List[DecisionSnapshot]:
        """Get all decisions for a specific function."""
        return [
            decision for decision in self.decisions
            if decision.function_name == function_name
        ]

    @property
    def total_decisions(self) -> int:
        """Total number of decisions in this snapshot."""
        return len(self.decisions)

    @property
    def total_execution_time_ms(self) -> float:
        """Total execution time across all decisions."""
        return sum(
            decision.execution_time_ms or 0
            for decision in self.decisions
        )


# Type aliases for convenience
SnapshotDict = Dict[str, Any]
SerializedSnapshot = Union[str, bytes, Dict[str, Any]]
