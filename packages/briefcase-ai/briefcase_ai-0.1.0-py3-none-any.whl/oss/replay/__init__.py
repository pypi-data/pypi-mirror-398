"""
Briefcase Replay Module

This module provides deterministic replay capabilities for AI decisions captured
in Briefcase snapshots. It includes a replay engine, policy framework for
validation, diff tools for comparison, and orchestration for batch operations.

Key Components:
- ReplayEngine: Core replay functionality with deterministic execution
- PolicyFramework: Validation policies for ensuring correctness
- DiffEngine: Comparison tools for analyzing replay results
- ReplayOrchestrator: Batch replay operations and scheduling

The replay system is designed with the following principles:
1. Perfect determinism - same inputs always produce same outputs
2. Policy-based validation - configurable validation rules
3. Comprehensive diff analysis - detailed comparison capabilities
4. Extensible hooks - support for custom replay behavior
"""

from .engine import ReplayEngine, ReplayResult, ReplayContext
from .policies import PolicyFramework, ValidationPolicy, PolicyResult
from .diff import DiffEngine, DiffResult, DiffType
from .orchestrator import ReplayOrchestrator, BatchReplayResult

__all__ = [
    # Core replay engine
    "ReplayEngine",
    "ReplayResult",
    "ReplayContext",

    # Policy framework
    "PolicyFramework",
    "ValidationPolicy",
    "PolicyResult",

    # Diff engine
    "DiffEngine",
    "DiffResult",
    "DiffType",

    # Orchestrator
    "ReplayOrchestrator",
    "BatchReplayResult",
]

__version__ = "0.1.0"