"""
Briefcase SDK - Deterministic Observability & Replay for AI Systems

This package provides:
- Immutable snapshot capture
- Decision instrumentation
- Deterministic replay capabilities
- Type-safe serialization
"""

from .models import (
    Snapshot,
    DecisionSnapshot,
    Input,
    Output,
    ModelParameters,
    ExecutionContext,
    SnapshotMetadata,
)
from .capture import (
    BriefcaseInstrument,
    capture_decision,
    instrument_function,
    instrument_class,
    create_context,
)
from .client import BriefcaseClient, get_default_client, set_default_client
from .serialization import (
    SnapshotSerializer,
    serialize_snapshot,
    deserialize_snapshot,
)
from .schema import (
    snapshot_schema,
    decision_schema,
    write_schema_files,
)
from .fixtures import (
    sample_snapshot,
    write_sample_snapshot,
    load_sample_snapshot,
)

__version__ = "0.1.0"
__all__ = [
    # Models
    "Snapshot",
    "DecisionSnapshot",
    "Input",
    "Output",
    "ModelParameters",
    "ExecutionContext",
    "SnapshotMetadata",
    # Capture
    "BriefcaseInstrument",
    "capture_decision",
    "instrument_function",
    "instrument_class",
    "create_context",
    # Client
    "BriefcaseClient",
    "get_default_client",
    "set_default_client",
    # Serialization
    "SnapshotSerializer",
    "serialize_snapshot",
    "deserialize_snapshot",
    # Schema + fixtures
    "snapshot_schema",
    "decision_schema",
    "write_schema_files",
    "sample_snapshot",
    "write_sample_snapshot",
    "load_sample_snapshot",
]
