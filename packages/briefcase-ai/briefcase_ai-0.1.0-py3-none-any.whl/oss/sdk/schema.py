"""Utility helpers for generating JSON schema artifacts from Briefcase models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Union

from .models import Snapshot, DecisionSnapshot

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def snapshot_schema() -> Dict[str, Any]:
    """Return the JSON schema for the Snapshot model."""
    return Snapshot.model_json_schema()


def decision_schema() -> Dict[str, Any]:
    """Return the JSON schema for the DecisionSnapshot model."""
    return DecisionSnapshot.model_json_schema()


def _dump_schema(schema: Dict[str, Any]) -> str:
    """Serialize schema dict to a formatted JSON string."""
    return json.dumps(schema, indent=2, sort_keys=True)


def write_schema_files(directory: Union[Path, str] = SCHEMA_DIR) -> Dict[str, Path]:
    """Generate schema files on disk and return their paths."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    snapshot_path = directory / "snapshot.schema.json"
    decision_path = directory / "decision.schema.json"

    snapshot_path.write_text(_dump_schema(snapshot_schema()), encoding="utf-8")
    decision_path.write_text(_dump_schema(decision_schema()), encoding="utf-8")

    return {"snapshot": snapshot_path, "decision": decision_path}


def main() -> None:
    """CLI entry point for generating schema artifacts."""
    written = write_schema_files()
    print("Generated schema files:")
    for name, path in written.items():
        print(f" - {name}: {path}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
