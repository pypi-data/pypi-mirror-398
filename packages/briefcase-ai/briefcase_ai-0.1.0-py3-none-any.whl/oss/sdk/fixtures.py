"""Reusable fixtures for SDK tests and demo data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Union, Optional
from uuid import UUID

from .models import (
    Snapshot,
    SnapshotMetadata,
    DecisionSnapshot,
    ExecutionContext,
    Input,
    Output,
    ModelParameters,
)
from .serialization import SnapshotSerializer

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_FIXTURE_PATH = FIXTURES_DIR / "sample_snapshot.json"


def sample_snapshot() -> Snapshot:
    """Return a deterministic Snapshot used for documentation and tests."""
    decision_metadata = SnapshotMetadata(
        snapshot_id=UUID("22222222-2222-2222-2222-222222222222"),
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        schema_version="1.0",
        sdk_version="0.1.0",
        created_by="demo-user",
    )

    context = ExecutionContext(
        session_id=UUID("11111111-1111-1111-1111-111111111111"),
        trace_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        parent_trace_id=None,
        user_id="demo-user",
        environment="demo",
        tags={"scenario": "payments-fraud"},
    )

    inputs = [
        Input(name="prompt", value="Hello, Briefcase", data_type="str"),
        Input(name="temperature", value=0.2, data_type="float"),
    ]

    outputs = [
        Output(name="response", value="Hi there!", data_type="str", confidence=0.92),
    ]

    decision = DecisionSnapshot(
        metadata=decision_metadata,
        context=context,
        function_name="demo.generate_response",
        module_name="demo.pipeline",
        inputs=inputs,
        outputs=outputs,
        model_parameters=ModelParameters(
            model_name="gpt-4",
            model_version="2024-01-01",
            parameters={"temperature": 0.2, "max_tokens": 100},
            hyperparameters={"top_p": 0.9},
            weights_hash="abc123",
        ),
        execution_time_ms=12.5,
        error=None,
    )

    snapshot_metadata = SnapshotMetadata(
        snapshot_id=UUID("33333333-3333-3333-3333-333333333333"),
        timestamp=datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        schema_version="1.0",
        sdk_version="0.1.0",
        created_by="demo-user",
    )

    return Snapshot(
        metadata=snapshot_metadata,
        decisions=[decision],
        snapshot_type="decision",
    )


def write_sample_snapshot(
    path: Union[Path, str] = DEFAULT_FIXTURE_PATH,
    serializer: Optional[SnapshotSerializer] = None,
) -> Path:
    """Write the deterministic sample snapshot to disk."""
    serializer = serializer or SnapshotSerializer()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = serializer.serialize_snapshot(sample_snapshot())
    path.write_text(payload + "\n", encoding="utf-8")
    return path


def load_sample_snapshot(serializer: Optional[SnapshotSerializer] = None) -> Snapshot:
    """Load the sample snapshot from disk (generates file if missing)."""
    target = DEFAULT_FIXTURE_PATH
    if not target.exists():
        write_sample_snapshot(target, serializer)

    serializer = serializer or SnapshotSerializer()
    return serializer.deserialize_snapshot(target.read_text(encoding="utf-8"))


def main() -> None:
    """CLI entry point for regenerating sample fixtures."""
    path = write_sample_snapshot()
    print(f"Wrote sample snapshot fixture to {path}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
