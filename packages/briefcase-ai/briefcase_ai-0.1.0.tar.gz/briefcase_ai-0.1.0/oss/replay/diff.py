"""
Comparison and Diff Tools for Replay Analysis

This module provides comprehensive diff and comparison capabilities for analyzing
differences between original snapshots and replay results. It includes visual
diff generation, statistical analysis, and detailed comparison reports.
"""

import difflib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, ConfigDict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

from ..sdk.models import DecisionSnapshot, Input, Output, Snapshot


class DiffType(str, Enum):
    """Types of differences that can be detected."""
    IDENTICAL = "identical"
    MODIFIED = "modified"
    ADDED = "added"
    REMOVED = "removed"
    TYPE_CHANGED = "type_changed"
    VALUE_CHANGED = "value_changed"
    TIMING_CHANGED = "timing_changed"


class DiffSeverity(str, Enum):
    """Severity levels for differences."""
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


@dataclass
class DiffLocation:
    """Represents the location of a difference."""
    path: str
    line_number: Optional[int] = None
    description: str = ""

    def __str__(self) -> str:
        if self.line_number:
            return f"{self.path}:{self.line_number} - {self.description}"
        return f"{self.path} - {self.description}"


class FieldDiff(BaseModel):
    """Represents a difference in a specific field."""
    model_config = ConfigDict(frozen=True)

    field_path: str = Field(..., description="Path to the field (e.g., 'outputs[0].value')")
    diff_type: DiffType = Field(..., description="Type of difference")
    severity: DiffSeverity = Field(default=DiffSeverity.MINOR, description="Severity of the difference")
    original_value: Optional[Any] = Field(None, description="Original value")
    replayed_value: Optional[Any] = Field(None, description="Replayed value")
    message: str = Field(..., description="Human-readable description of the difference")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def is_critical(self) -> bool:
        """Whether this difference is critical."""
        return self.severity == DiffSeverity.CRITICAL

    @property
    def is_data_change(self) -> bool:
        """Whether this difference represents a data change."""
        return self.diff_type in (DiffType.VALUE_CHANGED, DiffType.TYPE_CHANGED, DiffType.MODIFIED)


class DecisionDiff(BaseModel):
    """Represents differences between two decision snapshots."""
    model_config = ConfigDict(frozen=True)

    original_id: Optional[str] = Field(None, description="ID of original decision")
    replayed_id: Optional[str] = Field(None, description="ID of replayed decision")
    function_name: str = Field(..., description="Name of the function")
    diff_type: DiffType = Field(..., description="Overall type of difference")
    field_diffs: List[FieldDiff] = Field(default_factory=list, description="Differences in specific fields")
    execution_time_diff_ms: Optional[float] = Field(None, description="Difference in execution time")

    @property
    def has_critical_diffs(self) -> bool:
        """Whether this decision has critical differences."""
        return any(diff.is_critical for diff in self.field_diffs)

    @property
    def has_data_changes(self) -> bool:
        """Whether this decision has data changes."""
        return any(diff.is_data_change for diff in self.field_diffs)

    def get_diffs_by_type(self, diff_type: DiffType) -> List[FieldDiff]:
        """Get field diffs of a specific type."""
        return [diff for diff in self.field_diffs if diff.diff_type == diff_type]


class DiffSummary(BaseModel):
    """Summary statistics for a diff result."""
    model_config = ConfigDict(frozen=True)

    total_decisions: int = Field(..., description="Total number of decisions compared")
    identical_decisions: int = Field(default=0, description="Number of identical decisions")
    modified_decisions: int = Field(default=0, description="Number of modified decisions")
    added_decisions: int = Field(default=0, description="Number of added decisions")
    removed_decisions: int = Field(default=0, description="Number of removed decisions")
    critical_differences: int = Field(default=0, description="Number of critical differences")
    minor_differences: int = Field(default=0, description="Number of minor differences")
    avg_execution_time_diff_ms: Optional[float] = Field(None, description="Average execution time difference")

    @property
    def has_changes(self) -> bool:
        """Whether there are any changes."""
        return (self.modified_decisions > 0 or
                self.added_decisions > 0 or
                self.removed_decisions > 0)

    @property
    def similarity_percentage(self) -> float:
        """Percentage of decisions that are identical."""
        if self.total_decisions == 0:
            return 100.0
        return (self.identical_decisions / self.total_decisions) * 100


class DiffResult(BaseModel):
    """Complete result of a diff operation."""
    model_config = ConfigDict(frozen=True)

    original_snapshot_id: Optional[str] = Field(None, description="ID of original snapshot")
    replayed_snapshot_id: Optional[str] = Field(None, description="ID of replayed snapshot")
    timestamp: datetime = Field(default_factory=_utcnow, description="When diff was performed")
    summary: DiffSummary = Field(..., description="Summary statistics")
    decision_diffs: List[DecisionDiff] = Field(default_factory=list, description="Differences per decision")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def is_identical(self) -> bool:
        """Whether the snapshots are identical."""
        return not self.summary.has_changes and self.summary.critical_differences == 0

    def get_critical_diffs(self) -> List[DecisionDiff]:
        """Get decisions with critical differences."""
        return [diff for diff in self.decision_diffs if diff.has_critical_diffs]

    def get_modified_decisions(self) -> List[DecisionDiff]:
        """Get decisions that were modified."""
        return [diff for diff in self.decision_diffs if diff.diff_type == DiffType.MODIFIED]


class DiffEngine:
    """
    Engine for performing detailed comparisons between snapshots and decisions.

    This engine provides comprehensive diff capabilities including field-level
    comparisons, visual diff generation, and statistical analysis.
    """

    def __init__(
        self,
        tolerance: float = 0.0,
        ignore_timing: bool = False,
        ignore_metadata: bool = True,
        custom_comparators: Optional[Dict[str, callable]] = None
    ):
        """
        Initialize the diff engine.

        Args:
            tolerance: Tolerance for numeric comparisons
            ignore_timing: Whether to ignore timing differences
            ignore_metadata: Whether to ignore metadata differences
            custom_comparators: Custom comparison functions by field path
        """
        self.tolerance = tolerance
        self.ignore_timing = ignore_timing
        self.ignore_metadata = ignore_metadata
        self.custom_comparators = custom_comparators or {}

    def compare_snapshots(
        self,
        original: Snapshot,
        replayed: Optional[Snapshot] = None
    ) -> DiffResult:
        """
        Compare two snapshots and generate a detailed diff result.

        Args:
            original: Original snapshot
            replayed: Replayed snapshot (None if replay failed)

        Returns:
            DiffResult containing all differences
        """
        if replayed is None:
            return self._create_failed_replay_diff(original)

        # Compare decisions
        decision_diffs = self._compare_decision_lists(
            original.decisions,
            replayed.decisions
        )

        # Generate summary
        summary = self._generate_summary(decision_diffs)

        return DiffResult(
            original_snapshot_id=str(original.metadata.snapshot_id),
            replayed_snapshot_id=str(replayed.metadata.snapshot_id),
            summary=summary,
            decision_diffs=decision_diffs
        )

    def compare_decisions(
        self,
        original: DecisionSnapshot,
        replayed: Optional[DecisionSnapshot] = None
    ) -> DecisionDiff:
        """
        Compare two decision snapshots.

        Args:
            original: Original decision
            replayed: Replayed decision (None if decision failed to replay)

        Returns:
            DecisionDiff containing all differences
        """
        if replayed is None:
            return DecisionDiff(
                original_id=str(original.metadata.snapshot_id),
                replayed_id=None,
                function_name=original.function_name,
                diff_type=DiffType.REMOVED,
                field_diffs=[FieldDiff(
                    field_path="decision",
                    diff_type=DiffType.REMOVED,
                    severity=DiffSeverity.CRITICAL,
                    original_value="present",
                    replayed_value=None,
                    message="Decision failed to replay"
                )]
            )

        field_diffs = []

        # Compare inputs
        field_diffs.extend(self._compare_input_lists(
            original.inputs,
            replayed.inputs,
            "inputs"
        ))

        # Compare outputs
        field_diffs.extend(self._compare_output_lists(
            original.outputs,
            replayed.outputs,
            "outputs"
        ))

        # Compare execution time
        execution_time_diff = None
        if not self.ignore_timing and original.execution_time_ms and replayed.execution_time_ms:
            execution_time_diff = replayed.execution_time_ms - original.execution_time_ms

            if abs(execution_time_diff) > self.tolerance:
                field_diffs.append(FieldDiff(
                    field_path="execution_time_ms",
                    diff_type=DiffType.TIMING_CHANGED,
                    severity=DiffSeverity.MINOR,
                    original_value=original.execution_time_ms,
                    replayed_value=replayed.execution_time_ms,
                    message=f"Execution time changed by {execution_time_diff:.2f}ms"
                ))

        # Compare error status
        if original.error != replayed.error:
            field_diffs.append(FieldDiff(
                field_path="error",
                diff_type=DiffType.VALUE_CHANGED,
                severity=DiffSeverity.CRITICAL if replayed.error else DiffSeverity.MAJOR,
                original_value=original.error,
                replayed_value=replayed.error,
                message="Error status changed"
            ))

        # Determine overall diff type
        if not field_diffs:
            diff_type = DiffType.IDENTICAL
        else:
            diff_type = DiffType.MODIFIED

        return DecisionDiff(
            original_id=str(original.metadata.snapshot_id),
            replayed_id=str(replayed.metadata.snapshot_id),
            function_name=original.function_name,
            diff_type=diff_type,
            field_diffs=field_diffs,
            execution_time_diff_ms=execution_time_diff
        )

    def generate_visual_diff(
        self,
        original: Union[Snapshot, DecisionSnapshot],
        replayed: Optional[Union[Snapshot, DecisionSnapshot]] = None,
        context_lines: int = 3
    ) -> str:
        """
        Generate a visual diff in unified diff format.

        Args:
            original: Original snapshot or decision
            replayed: Replayed snapshot or decision
            context_lines: Number of context lines to show

        Returns:
            Visual diff as a string
        """
        # Convert to JSON for comparison
        original_json = self._to_pretty_json(original)
        replayed_json = self._to_pretty_json(replayed) if replayed else ""

        original_lines = original_json.splitlines(keepends=True)
        replayed_lines = replayed_json.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            replayed_lines,
            fromfile="original",
            tofile="replayed",
            n=context_lines
        )

        return "".join(diff)

    def generate_html_diff(
        self,
        original: Union[Snapshot, DecisionSnapshot],
        replayed: Optional[Union[Snapshot, DecisionSnapshot]] = None
    ) -> str:
        """
        Generate an HTML diff for web display.

        Args:
            original: Original snapshot or decision
            replayed: Replayed snapshot or decision

        Returns:
            HTML diff as a string
        """
        original_json = self._to_pretty_json(original)
        replayed_json = self._to_pretty_json(replayed) if replayed else ""

        original_lines = original_json.splitlines()
        replayed_lines = replayed_json.splitlines()

        differ = difflib.HtmlDiff()
        return differ.make_file(
            original_lines,
            replayed_lines,
            fromdesc="Original",
            todesc="Replayed"
        )

    def _create_failed_replay_diff(self, original: Snapshot) -> DiffResult:
        """Create a diff result for a failed replay."""
        decision_diffs = []

        for decision in original.decisions:
            decision_diffs.append(DecisionDiff(
                original_id=str(decision.metadata.snapshot_id),
                replayed_id=None,
                function_name=decision.function_name,
                diff_type=DiffType.REMOVED,
                field_diffs=[FieldDiff(
                    field_path="decision",
                    diff_type=DiffType.REMOVED,
                    severity=DiffSeverity.CRITICAL,
                    original_value="present",
                    replayed_value=None,
                    message="Decision not replayed due to replay failure"
                )]
            ))

        summary = DiffSummary(
            total_decisions=len(original.decisions),
            removed_decisions=len(original.decisions),
            critical_differences=len(original.decisions)
        )

        return DiffResult(
            original_snapshot_id=str(original.metadata.snapshot_id),
            replayed_snapshot_id=None,
            summary=summary,
            decision_diffs=decision_diffs
        )

    def _compare_decision_lists(
        self,
        original_decisions: List[DecisionSnapshot],
        replayed_decisions: List[DecisionSnapshot]
    ) -> List[DecisionDiff]:
        """Compare two lists of decisions."""
        decision_diffs = []

        # Create mapping of decisions by function name for comparison
        original_by_function = defaultdict(list)
        for decision in original_decisions:
            key = f"{decision.module_name}.{decision.function_name}"
            original_by_function[key].append(decision)

        replayed_by_function = defaultdict(list)
        for decision in replayed_decisions:
            key = f"{decision.module_name}.{decision.function_name}"
            replayed_by_function[key].append(decision)

        # Compare decisions
        all_functions = set(original_by_function.keys()) | set(replayed_by_function.keys())

        for function_key in all_functions:
            orig_decisions = original_by_function[function_key]
            repl_decisions = replayed_by_function[function_key]

            # Handle different counts
            max_count = max(len(orig_decisions), len(repl_decisions))

            for i in range(max_count):
                orig_decision = orig_decisions[i] if i < len(orig_decisions) else None
                repl_decision = repl_decisions[i] if i < len(repl_decisions) else None

                if orig_decision and repl_decision:
                    # Compare both decisions
                    decision_diffs.append(self.compare_decisions(orig_decision, repl_decision))
                elif orig_decision:
                    # Original exists but replay doesn't
                    decision_diffs.append(self.compare_decisions(orig_decision, None))
                elif repl_decision:
                    # Replay exists but original doesn't (added)
                    decision_diffs.append(DecisionDiff(
                        original_id=None,
                        replayed_id=str(repl_decision.metadata.snapshot_id),
                        function_name=repl_decision.function_name,
                        diff_type=DiffType.ADDED,
                        field_diffs=[FieldDiff(
                            field_path="decision",
                            diff_type=DiffType.ADDED,
                            severity=DiffSeverity.MAJOR,
                            original_value=None,
                            replayed_value="present",
                            message="Additional decision found in replay"
                        )]
                    ))

        return decision_diffs

    def _compare_input_lists(
        self,
        original_inputs: List[Input],
        replayed_inputs: List[Input],
        prefix: str
    ) -> List[FieldDiff]:
        """Compare two lists of inputs."""
        diffs = []

        # Create mappings by name
        original_by_name = {inp.name: inp for inp in original_inputs}
        replayed_by_name = {inp.name: inp for inp in replayed_inputs}

        all_names = set(original_by_name.keys()) | set(replayed_by_name.keys())

        for name in all_names:
            field_path = f"{prefix}.{name}"
            original_input = original_by_name.get(name)
            replayed_input = replayed_by_name.get(name)

            if original_input and replayed_input:
                diffs.extend(self._compare_input_values(original_input, replayed_input, field_path))
            elif original_input:
                diffs.append(FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.REMOVED,
                    severity=DiffSeverity.MAJOR,
                    original_value=original_input.value,
                    replayed_value=None,
                    message=f"Input '{name}' removed"
                ))
            else:
                diffs.append(FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.ADDED,
                    severity=DiffSeverity.MAJOR,
                    original_value=None,
                    replayed_value=replayed_input.value,
                    message=f"Input '{name}' added"
                ))

        return diffs

    def _compare_output_lists(
        self,
        original_outputs: List[Output],
        replayed_outputs: List[Output],
        prefix: str
    ) -> List[FieldDiff]:
        """Compare two lists of outputs."""
        diffs = []

        # Create mappings by name
        original_by_name = {out.name: out for out in original_outputs}
        replayed_by_name = {out.name: out for out in replayed_outputs}

        all_names = set(original_by_name.keys()) | set(replayed_by_name.keys())

        for name in all_names:
            field_path = f"{prefix}.{name}"
            original_output = original_by_name.get(name)
            replayed_output = replayed_by_name.get(name)

            if original_output and replayed_output:
                diffs.extend(self._compare_output_values(original_output, replayed_output, field_path))
            elif original_output:
                diffs.append(FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.REMOVED,
                    severity=DiffSeverity.CRITICAL,
                    original_value=original_output.value,
                    replayed_value=None,
                    message=f"Output '{name}' removed"
                ))
            else:
                diffs.append(FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.ADDED,
                    severity=DiffSeverity.MAJOR,
                    original_value=None,
                    replayed_value=replayed_output.value,
                    message=f"Output '{name}' added"
                ))

        return diffs

    def _compare_input_values(self, original: Input, replayed: Input, field_path: str) -> List[FieldDiff]:
        """Compare values of two inputs."""
        diffs = []

        # Compare data type
        if original.data_type != replayed.data_type:
            diffs.append(FieldDiff(
                field_path=f"{field_path}.data_type",
                diff_type=DiffType.TYPE_CHANGED,
                severity=DiffSeverity.MAJOR,
                original_value=original.data_type,
                replayed_value=replayed.data_type,
                message=f"Input data type changed from {original.data_type} to {replayed.data_type}"
            ))

        # Compare value
        if not self._values_equal(original.value, replayed.value):
            diffs.append(FieldDiff(
                field_path=f"{field_path}.value",
                diff_type=DiffType.VALUE_CHANGED,
                severity=DiffSeverity.MINOR,
                original_value=original.value,
                replayed_value=replayed.value,
                message=f"Input value changed"
            ))

        return diffs

    def _compare_output_values(self, original: Output, replayed: Output, field_path: str) -> List[FieldDiff]:
        """Compare values of two outputs."""
        diffs = []

        # Compare data type
        if original.data_type != replayed.data_type:
            diffs.append(FieldDiff(
                field_path=f"{field_path}.data_type",
                diff_type=DiffType.TYPE_CHANGED,
                severity=DiffSeverity.MAJOR,
                original_value=original.data_type,
                replayed_value=replayed.data_type,
                message=f"Output data type changed from {original.data_type} to {replayed.data_type}"
            ))

        # Compare value
        if not self._values_equal(original.value, replayed.value):
            diffs.append(FieldDiff(
                field_path=f"{field_path}.value",
                diff_type=DiffType.VALUE_CHANGED,
                severity=DiffSeverity.CRITICAL,
                original_value=original.value,
                replayed_value=replayed.value,
                message=f"Output value changed"
            ))

        # Compare confidence
        if original.confidence != replayed.confidence:
            if not self._values_equal(original.confidence, replayed.confidence):
                diffs.append(FieldDiff(
                    field_path=f"{field_path}.confidence",
                    diff_type=DiffType.VALUE_CHANGED,
                    severity=DiffSeverity.MINOR,
                    original_value=original.confidence,
                    replayed_value=replayed.confidence,
                    message=f"Output confidence changed"
                ))

        return diffs

    def _values_equal(self, value1: Any, value2: Any) -> bool:
        """Check if two values are equal within tolerance."""
        if value1 is None and value2 is None:
            return True
        if value1 is None or value2 is None:
            return False

        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return abs(value1 - value2) <= self.tolerance

        return value1 == value2

    def _generate_summary(self, decision_diffs: List[DecisionDiff]) -> DiffSummary:
        """Generate summary statistics from decision diffs."""
        total = len(decision_diffs)
        identical = sum(1 for diff in decision_diffs if diff.diff_type == DiffType.IDENTICAL)
        modified = sum(1 for diff in decision_diffs if diff.diff_type == DiffType.MODIFIED)
        added = sum(1 for diff in decision_diffs if diff.diff_type == DiffType.ADDED)
        removed = sum(1 for diff in decision_diffs if diff.diff_type == DiffType.REMOVED)

        critical = sum(1 for diff in decision_diffs if diff.has_critical_diffs)
        minor = sum(len(diff.field_diffs) for diff in decision_diffs) - critical

        # Calculate average execution time difference
        time_diffs = [diff.execution_time_diff_ms for diff in decision_diffs
                     if diff.execution_time_diff_ms is not None]
        avg_time_diff = sum(time_diffs) / len(time_diffs) if time_diffs else None

        return DiffSummary(
            total_decisions=total,
            identical_decisions=identical,
            modified_decisions=modified,
            added_decisions=added,
            removed_decisions=removed,
            critical_differences=critical,
            minor_differences=minor,
            avg_execution_time_diff_ms=avg_time_diff
        )

    def _to_pretty_json(self, obj: Union[Snapshot, DecisionSnapshot, None]) -> str:
        """Convert object to pretty-printed JSON."""
        if obj is None:
            return ""

        return json.dumps(obj.dict(), indent=2, sort_keys=True, default=str)


# Convenience functions for common diff operations

def quick_diff(original: Snapshot, replayed: Optional[Snapshot] = None) -> DiffResult:
    """
    Quick diff between two snapshots.

    Args:
        original: Original snapshot
        replayed: Replayed snapshot

    Returns:
        DiffResult
    """
    engine = DiffEngine()
    return engine.compare_snapshots(original, replayed)


def visual_diff(original: Snapshot, replayed: Optional[Snapshot] = None) -> str:
    """
    Generate visual diff between two snapshots.

    Args:
        original: Original snapshot
        replayed: Replayed snapshot

    Returns:
        Visual diff as string
    """
    engine = DiffEngine()
    return engine.generate_visual_diff(original, replayed)
