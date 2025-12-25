"""
Policy Framework for Replay Validation

This module provides a flexible policy framework for validating replay results.
Policies can check output consistency, timing constraints, data integrity,
and custom business rules. The framework supports both built-in and custom policies.
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..sdk.models import DecisionSnapshot, Input, Output, Snapshot
from .engine import ReplayResult


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PolicyScope(str, Enum):
    """Scope of policy application."""
    DECISION = "decision"  # Apply to individual decisions
    SNAPSHOT = "snapshot"  # Apply to entire snapshots
    COMPARISON = "comparison"  # Apply to comparisons between original and replayed


class PolicyViolation(BaseModel):
    """Represents a policy violation."""
    model_config = ConfigDict(frozen=True)

    policy_name: str = Field(..., description="Name of the violated policy")
    severity: PolicySeverity = Field(..., description="Severity of the violation")
    message: str = Field(..., description="Human-readable violation message")
    location: str = Field(..., description="Location of the violation")
    expected: Optional[Any] = Field(None, description="Expected value")
    actual: Optional[Any] = Field(None, description="Actual value")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def is_critical(self) -> bool:
        """Whether this violation is critical."""
        return self.severity in (PolicySeverity.ERROR, PolicySeverity.CRITICAL)


class PolicyResult(BaseModel):
    """Result of policy evaluation."""
    model_config = ConfigDict(frozen=True)

    policy_name: str = Field(..., description="Name of the evaluated policy")
    passed: bool = Field(..., description="Whether the policy passed")
    violations: List[PolicyViolation] = Field(default_factory=list, description="List of violations")
    execution_time_ms: float = Field(..., description="Time taken to evaluate the policy")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def critical_violations(self) -> List[PolicyViolation]:
        """Get only critical violations."""
        return [v for v in self.violations if v.is_critical]

    @property
    def warning_violations(self) -> List[PolicyViolation]:
        """Get only warning violations."""
        return [v for v in self.violations if v.severity == PolicySeverity.WARNING]


class ValidationPolicy(ABC):
    """Abstract base class for validation policies."""

    def __init__(self, name: str, severity: PolicySeverity = PolicySeverity.ERROR):
        """
        Initialize the policy.

        Args:
            name: Name of the policy
            severity: Default severity for violations
        """
        self.name = name
        self.severity = severity
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        """
        Evaluate the policy against the provided context.

        Args:
            context: Context containing data to validate

        Returns:
            PolicyResult with evaluation outcome
        """
        pass

    def create_violation(
        self,
        message: str,
        location: str,
        severity: Optional[PolicySeverity] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None,
        **metadata
    ) -> PolicyViolation:
        """Create a policy violation."""
        return PolicyViolation(
            policy_name=self.name,
            severity=severity or self.severity,
            message=message,
            location=location,
            expected=expected,
            actual=actual,
            metadata=metadata
        )


class OutputConsistencyPolicy(ValidationPolicy):
    """Policy that validates output consistency between original and replayed decisions."""

    def __init__(
        self,
        tolerance: float = 0.0,
        ignore_fields: Optional[Set[str]] = None,
        severity: PolicySeverity = PolicySeverity.ERROR
    ):
        """
        Initialize the output consistency policy.

        Args:
            tolerance: Tolerance for numeric comparisons
            ignore_fields: Fields to ignore during comparison
            severity: Severity level for violations
        """
        super().__init__("output_consistency", severity)
        self.tolerance = tolerance
        self.ignore_fields = ignore_fields or set()

    async def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate output consistency between original and replayed decisions."""
        import time
        start_time = time.time()

        violations = []
        original_decision = context.get("original_decision")
        replayed_decision = context.get("replayed_decision")

        if not original_decision or not replayed_decision:
            violations.append(self.create_violation(
                "Missing original or replayed decision for comparison",
                "decision_comparison"
            ))
        else:
            # Compare outputs
            violations.extend(self._compare_outputs(
                original_decision.outputs,
                replayed_decision.outputs,
                f"decision.{original_decision.metadata.snapshot_id}"
            ))

        execution_time_ms = (time.time() - start_time) * 1000

        return PolicyResult(
            policy_name=self.name,
            passed=len(violations) == 0,
            violations=violations,
            execution_time_ms=execution_time_ms
        )

    def _compare_outputs(
        self,
        original_outputs: List[Output],
        replayed_outputs: List[Output],
        location: str
    ) -> List[PolicyViolation]:
        """Compare two lists of outputs."""
        violations = []

        # Check count
        if len(original_outputs) != len(replayed_outputs):
            violations.append(self.create_violation(
                f"Output count mismatch",
                f"{location}.outputs",
                expected=len(original_outputs),
                actual=len(replayed_outputs)
            ))
            return violations

        # Compare each output
        for i, (orig, repl) in enumerate(zip(original_outputs, replayed_outputs)):
            output_location = f"{location}.outputs[{i}]"

            # Check name
            if orig.name != repl.name:
                violations.append(self.create_violation(
                    f"Output name mismatch",
                    f"{output_location}.name",
                    expected=orig.name,
                    actual=repl.name
                ))

            # Check data type
            if orig.data_type != repl.data_type:
                violations.append(self.create_violation(
                    f"Output data type mismatch",
                    f"{output_location}.data_type",
                    expected=orig.data_type,
                    actual=repl.data_type
                ))

            # Check value with tolerance
            if not self._values_equal(orig.value, repl.value):
                violations.append(self.create_violation(
                    f"Output value mismatch",
                    f"{output_location}.value",
                    expected=orig.value,
                    actual=repl.value
                ))

        return violations

    def _values_equal(self, value1: Any, value2: Any) -> bool:
        """Check if two values are equal within tolerance."""
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return abs(value1 - value2) <= self.tolerance
        return value1 == value2


class TimingPolicy(ValidationPolicy):
    """Policy that validates execution timing constraints."""

    def __init__(
        self,
        max_duration_ms: Optional[float] = None,
        max_variance_percent: float = 50.0,
        severity: PolicySeverity = PolicySeverity.WARNING
    ):
        """
        Initialize the timing policy.

        Args:
            max_duration_ms: Maximum allowed execution duration
            max_variance_percent: Maximum allowed variance from original timing
            severity: Severity level for violations
        """
        super().__init__("timing", severity)
        self.max_duration_ms = max_duration_ms
        self.max_variance_percent = max_variance_percent

    async def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate timing constraints."""
        import time
        start_time = time.time()

        violations = []

        # Check replay result timing
        replay_result = context.get("replay_result")
        if replay_result and self.max_duration_ms:
            if replay_result.execution_time_ms > self.max_duration_ms:
                violations.append(self.create_violation(
                    f"Replay execution exceeded maximum duration",
                    "replay.execution_time",
                    expected=f"<= {self.max_duration_ms}ms",
                    actual=f"{replay_result.execution_time_ms}ms"
                ))

        # Check decision-level timing
        original_decision = context.get("original_decision")
        replayed_decision = context.get("replayed_decision")

        if (original_decision and replayed_decision and
            original_decision.execution_time_ms and replayed_decision.execution_time_ms):

            original_time = original_decision.execution_time_ms
            replayed_time = replayed_decision.execution_time_ms

            variance_percent = abs(replayed_time - original_time) / original_time * 100

            if variance_percent > self.max_variance_percent:
                violations.append(self.create_violation(
                    f"Decision execution time variance exceeds threshold",
                    f"decision.{original_decision.metadata.snapshot_id}.execution_time",
                    expected=f"within {self.max_variance_percent}% of {original_time}ms",
                    actual=f"{replayed_time}ms ({variance_percent:.1f}% variance)"
                ))

        execution_time_ms = (time.time() - start_time) * 1000

        return PolicyResult(
            policy_name=self.name,
            passed=len(violations) == 0,
            violations=violations,
            execution_time_ms=execution_time_ms
        )


class DataIntegrityPolicy(ValidationPolicy):
    """Policy that validates data integrity and format compliance."""

    def __init__(
        self,
        required_fields: Optional[List[str]] = None,
        field_patterns: Optional[Dict[str, str]] = None,
        severity: PolicySeverity = PolicySeverity.ERROR
    ):
        """
        Initialize the data integrity policy.

        Args:
            required_fields: List of required fields in outputs
            field_patterns: Regex patterns for field validation
            severity: Severity level for violations
        """
        super().__init__("data_integrity", severity)
        self.required_fields = required_fields or []
        self.field_patterns = field_patterns or {}

    async def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate data integrity constraints."""
        import time
        start_time = time.time()

        violations = []

        # Check replayed decision data integrity
        replayed_decision = context.get("replayed_decision")
        if replayed_decision:
            violations.extend(self._validate_decision_integrity(replayed_decision))

        execution_time_ms = (time.time() - start_time) * 1000

        return PolicyResult(
            policy_name=self.name,
            passed=len(violations) == 0,
            violations=violations,
            execution_time_ms=execution_time_ms
        )

    def _validate_decision_integrity(self, decision: DecisionSnapshot) -> List[PolicyViolation]:
        """Validate integrity of a decision snapshot."""
        violations = []
        location = f"decision.{decision.metadata.snapshot_id}"

        # Check required fields
        for field_name in self.required_fields:
            found = False
            for output in decision.outputs:
                if output.name == field_name:
                    found = True
                    break

            if not found:
                violations.append(self.create_violation(
                    f"Required field '{field_name}' not found in outputs",
                    f"{location}.outputs"
                ))

        # Check field patterns
        for output in decision.outputs:
            if output.name in self.field_patterns:
                pattern = self.field_patterns[output.name]
                if not re.match(pattern, str(output.value)):
                    violations.append(self.create_violation(
                        f"Field '{output.name}' does not match required pattern",
                        f"{location}.outputs.{output.name}",
                        expected=pattern,
                        actual=str(output.value)
                    ))

        return violations


class CustomPolicy(ValidationPolicy):
    """Policy that allows custom validation logic."""

    def __init__(
        self,
        name: str,
        validator_func: Callable[[Dict[str, Any]], List[PolicyViolation]],
        severity: PolicySeverity = PolicySeverity.ERROR
    ):
        """
        Initialize a custom policy.

        Args:
            name: Name of the policy
            validator_func: Function that validates context and returns violations
            severity: Default severity for violations
        """
        super().__init__(name, severity)
        self.validator_func = validator_func

    async def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate the custom validation logic."""
        import time
        start_time = time.time()

        violations = []

        try:
            violations = self.validator_func(context)
        except Exception as e:
            violations.append(self.create_violation(
                f"Custom policy evaluation failed: {str(e)}",
                "custom_policy_execution"
            ))

        execution_time_ms = (time.time() - start_time) * 1000

        return PolicyResult(
            policy_name=self.name,
            passed=len(violations) == 0,
            violations=violations,
            execution_time_ms=execution_time_ms
        )


class PolicyFramework:
    """
    Framework for managing and executing validation policies.

    This class coordinates the execution of multiple policies and provides
    aggregated results for replay validation.
    """

    def __init__(self, policies: Optional[List[ValidationPolicy]] = None):
        """
        Initialize the policy framework.

        Args:
            policies: List of policies to include
        """
        self.policies: List[ValidationPolicy] = policies or []
        self.logger = logging.getLogger(__name__)

    def add_policy(self, policy: ValidationPolicy) -> None:
        """Add a policy to the framework."""
        self.policies.append(policy)

    def remove_policy(self, policy_name: str) -> bool:
        """
        Remove a policy by name.

        Args:
            policy_name: Name of the policy to remove

        Returns:
            True if policy was found and removed
        """
        for i, policy in enumerate(self.policies):
            if policy.name == policy_name:
                del self.policies[i]
                return True
        return False

    def get_policy(self, policy_name: str) -> Optional[ValidationPolicy]:
        """Get a policy by name."""
        for policy in self.policies:
            if policy.name == policy_name:
                return policy
        return None

    async def evaluate_all(self, context: Dict[str, Any]) -> List[PolicyResult]:
        """
        Evaluate all policies against the provided context.

        Args:
            context: Context containing data to validate

        Returns:
            List of PolicyResult objects
        """
        results = []

        for policy in self.policies:
            try:
                result = await policy.evaluate(context)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Policy {policy.name} evaluation failed: {str(e)}")
                # Create an error result
                error_violation = PolicyViolation(
                    policy_name=policy.name,
                    severity=PolicySeverity.CRITICAL,
                    message=f"Policy evaluation failed: {str(e)}",
                    location="policy_execution"
                )
                results.append(PolicyResult(
                    policy_name=policy.name,
                    passed=False,
                    violations=[error_violation],
                    execution_time_ms=0.0
                ))

        return results

    async def evaluate_replay_result(self, replay_result: ReplayResult) -> List[PolicyResult]:
        """
        Evaluate policies against a replay result.

        Args:
            replay_result: Result from replay execution

        Returns:
            List of PolicyResult objects
        """
        context = {
            "replay_result": replay_result,
            "original_snapshot": replay_result.original_snapshot,
            "replayed_snapshot": replay_result.replayed_snapshot
        }

        # Add decision-level context if snapshots exist
        if replay_result.replayed_snapshot:
            decision_results = []

            for orig_decision in replay_result.original_snapshot.decisions:
                # Find corresponding replayed decision
                repl_decision = None
                if replay_result.replayed_snapshot:
                    for repl in replay_result.replayed_snapshot.decisions:
                        if (repl.function_name == orig_decision.function_name and
                            repl.module_name == orig_decision.module_name):
                            repl_decision = repl
                            break

                decision_context = {
                    **context,
                    "original_decision": orig_decision,
                    "replayed_decision": repl_decision
                }

                decision_results.extend(await self.evaluate_all(decision_context))

            return decision_results
        else:
            return await self.evaluate_all(context)

    def create_default_policies(self) -> List[ValidationPolicy]:
        """Create a default set of policies."""
        return [
            OutputConsistencyPolicy(tolerance=0.001),
            TimingPolicy(max_variance_percent=100.0),
            DataIntegrityPolicy()
        ]

    @property
    def policy_names(self) -> List[str]:
        """Get names of all policies."""
        return [policy.name for policy in self.policies]


# Convenience functions for common policy operations

def create_basic_policy_framework() -> PolicyFramework:
    """Create a policy framework with basic policies."""
    framework = PolicyFramework()
    for policy in framework.create_default_policies():
        framework.add_policy(policy)
    return framework


async def validate_replay(replay_result: ReplayResult, policies: Optional[List[ValidationPolicy]] = None) -> List[PolicyResult]:
    """
    Quick validation of a replay result.

    Args:
        replay_result: Result to validate
        policies: Custom policies (uses defaults if not provided)

    Returns:
        List of PolicyResult objects
    """
    framework = PolicyFramework(policies)
    if not policies:
        for policy in framework.create_default_policies():
            framework.add_policy(policy)

    return await framework.evaluate_replay_result(replay_result)
