"""
Decision capture interfaces and instrumentation decorators for Briefcase.

This module provides both synchronous and asynchronous interfaces for capturing
AI decisions with deterministic replay capabilities.
"""

import asyncio
import functools
import inspect
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, TYPE_CHECKING
from uuid import UUID

from .models import (
    DecisionSnapshot,
    ExecutionContext,
    Input,
    ModelParameters,
    Output,
    SnapshotMetadata,
)

if TYPE_CHECKING:  # pragma: no cover - avoids circular import at runtime
    from .client import BriefcaseClient

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class BriefcaseInstrument:
    """
    Context manager and decorator for instrumenting AI decisions.

    This is the primary interface for capturing decisions with Briefcase.
    """

    def __init__(
        self,
        function_name: Optional[str] = None,
        model_parameters: Optional[ModelParameters] = None,
        context: Optional[ExecutionContext] = None,
        capture_inputs: bool = True,
        capture_outputs: bool = True,
        auto_serialize: bool = True,
    ):
        """
        Initialize the instrumentation.

        Args:
            function_name: Override the function name for the snapshot
            model_parameters: Model parameters to include in the snapshot
            context: Execution context (created if not provided)
            capture_inputs: Whether to capture function inputs
            capture_outputs: Whether to capture function outputs
            auto_serialize: Whether to automatically serialize complex objects
        """
        self.function_name = function_name
        self.model_parameters = model_parameters
        self.context = context or ExecutionContext()
        self.capture_inputs = capture_inputs
        self.capture_outputs = capture_outputs
        self.auto_serialize = auto_serialize

        # Internal state
        self._start_time: Optional[float] = None
        self._inputs: List[Input] = []
        self._outputs: List[Output] = []
        self._error: Optional[str] = None

    def add_input(self, name: str, value: Any, data_type: Optional[str] = None) -> None:
        """Add an input to the current decision snapshot."""
        if not self.capture_inputs:
            return

        if data_type is None:
            data_type = type(value).__name__

        input_obj = Input(
            name=name,
            value=self._serialize_if_needed(value),
            data_type=data_type,
        )
        self._inputs.append(input_obj)

    def add_output(
        self,
        name: str,
        value: Any,
        data_type: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> None:
        """Add an output to the current decision snapshot."""
        if not self.capture_outputs:
            return

        if data_type is None:
            data_type = type(value).__name__

        output_obj = Output(
            name=name,
            value=self._serialize_if_needed(value),
            data_type=data_type,
            confidence=confidence,
        )
        self._outputs.append(output_obj)

    def set_error(self, error: Union[str, Exception]) -> None:
        """Set an error for the current decision snapshot."""
        self._error = str(error)

    def _serialize_if_needed(self, value: Any) -> Any:
        """Serialize complex objects if auto_serialize is enabled."""
        if not self.auto_serialize:
            return value

        # Handle common serializable types
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            return value

        # For complex objects, convert to string representation
        try:
            # Try to use object's __dict__ if available
            if hasattr(value, '__dict__'):
                return value.__dict__
            else:
                return str(value)
        except Exception:
            return f"<{type(value).__name__} object>"

    def create_snapshot(self, actual_function_name: Optional[str] = None) -> DecisionSnapshot:
        """Create a decision snapshot from the captured data."""
        execution_time = None
        if self._start_time is not None:
            execution_time = (time.time() - self._start_time) * 1000  # Convert to ms

        # Determine module name from the calling frame
        frame = inspect.currentframe()
        module_name = "unknown"
        try:
            # Go up the call stack to find the actual module
            while frame is not None:
                if frame.f_code.co_filename != __file__:
                    module_name = frame.f_globals.get('__name__', 'unknown')
                    break
                frame = frame.f_back
        except Exception:
            pass

        return DecisionSnapshot(
            metadata=SnapshotMetadata(),
            context=self.context,
            function_name=self.function_name or actual_function_name or "unknown",
            module_name=module_name,
            inputs=self._inputs.copy(),
            outputs=self._outputs.copy(),
            model_parameters=self.model_parameters,
            execution_time_ms=execution_time,
            error=self._error,
        )

    def __enter__(self) -> "BriefcaseInstrument":
        """Enter the context manager."""
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        if exc_type is not None:
            self.set_error(exc_val)

    async def __aenter__(self) -> "BriefcaseInstrument":
        """Enter the async context manager."""
        self._start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager."""
        if exc_type is not None:
            self.set_error(exc_val)


def instrument_function(
    function_name: Optional[str] = None,
    model_parameters: Optional[ModelParameters] = None,
    context: Optional[ExecutionContext] = None,
    capture_inputs: bool = True,
    capture_outputs: bool = True,
    auto_serialize: bool = True,
    persist_snapshot: bool = True,
    client: Optional["BriefcaseClient"] = None,
    on_snapshot: Optional[Callable[[DecisionSnapshot], None]] = None,
) -> Callable[[F], F]:
    """
    Decorator to instrument a function for decision capture.

    Args:
        function_name: Override the function name for the snapshot
        model_parameters: Model parameters to include in the snapshot
        context: Execution context (created if not provided)
        capture_inputs: Whether to capture function inputs
        capture_outputs: Whether to capture function outputs
        auto_serialize: Whether to automatically serialize complex objects
        persist_snapshot: Automatically save the decision via the Briefcase client
        client: Optional client override (defaults to global client)
        on_snapshot: Optional callback invoked with the generated snapshot

    Returns:
        Decorated function that captures decisions
    """

    def decorator(func: F) -> F:
        def _persist_snapshot(snapshot: DecisionSnapshot) -> None:
            """Persist snapshot via provided or default client."""
            if not persist_snapshot:
                return

            target_client = client
            if target_client is None:
                try:
                    from .client import get_default_client  # Local import avoids circular dependency

                    target_client = get_default_client()
                except Exception:
                    target_client = None

            if target_client is not None:
                target_client.save_decision(snapshot)

        def _handle_snapshot(
            snapshot: DecisionSnapshot,
            wrapper: Callable[..., Any],
        ) -> None:
            """Record and persist snapshot for the current invocation."""
            if on_snapshot is not None:
                on_snapshot(snapshot)

            _persist_snapshot(snapshot)
            setattr(wrapper, "__briefcase_last_snapshot__", snapshot)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with BriefcaseInstrument(
                function_name=function_name or func.__name__,
                model_parameters=model_parameters,
                context=context,
                capture_inputs=capture_inputs,
                capture_outputs=capture_outputs,
                auto_serialize=auto_serialize,
            ) as instrument:
                # Capture inputs
                if capture_inputs:
                    # Capture positional arguments
                    for i, arg in enumerate(args):
                        instrument.add_input(f"arg_{i}", arg)

                    # Capture keyword arguments
                    for key, value in kwargs.items():
                        instrument.add_input(key, value)

                try:
                    result = func(*args, **kwargs)

                    # Capture output
                    if capture_outputs:
                        instrument.add_output("return", result)

                except Exception as e:
                    instrument.set_error(e)
                    snapshot = instrument.create_snapshot(actual_function_name=func.__name__)
                    _handle_snapshot(snapshot, sync_wrapper)
                    raise

                snapshot = instrument.create_snapshot(actual_function_name=func.__name__)
                _handle_snapshot(snapshot, sync_wrapper)
                return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with BriefcaseInstrument(
                function_name=function_name or func.__name__,
                model_parameters=model_parameters,
                context=context,
                capture_inputs=capture_inputs,
                capture_outputs=capture_outputs,
                auto_serialize=auto_serialize,
            ) as instrument:
                # Capture inputs
                if capture_inputs:
                    # Capture positional arguments
                    for i, arg in enumerate(args):
                        instrument.add_input(f"arg_{i}", arg)

                    # Capture keyword arguments
                    for key, value in kwargs.items():
                        instrument.add_input(key, value)

                try:
                    result = await func(*args, **kwargs)

                    # Capture output
                    if capture_outputs:
                        instrument.add_output("return", result)

                except Exception as e:
                    instrument.set_error(e)
                    snapshot = instrument.create_snapshot(actual_function_name=func.__name__)
                    _handle_snapshot(snapshot, async_wrapper)
                    raise

                snapshot = instrument.create_snapshot(actual_function_name=func.__name__)
                _handle_snapshot(snapshot, async_wrapper)
                return result

        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def instrument_class(
    methods: Optional[List[str]] = None,
    exclude_methods: Optional[List[str]] = None,
    model_parameters: Optional[ModelParameters] = None,
    context: Optional[ExecutionContext] = None,
    capture_inputs: bool = True,
    capture_outputs: bool = True,
    auto_serialize: bool = True,
    persist_snapshot: bool = True,
    client: Optional["BriefcaseClient"] = None,
    on_snapshot: Optional[Callable[[DecisionSnapshot], None]] = None,
) -> Callable[[type], type]:
    """
    Class decorator to instrument multiple methods for decision capture.

    Args:
        methods: List of method names to instrument (None = all public methods)
        exclude_methods: List of method names to exclude from instrumentation
        model_parameters: Model parameters to include in snapshots
        context: Execution context (created if not provided)
        capture_inputs: Whether to capture method inputs
        capture_outputs: Whether to capture method outputs
        auto_serialize: Whether to automatically serialize complex objects
        persist_snapshot: Automatically persist snapshots via Briefcase client
        client: Optional client override
        on_snapshot: Optional callback invoked for each snapshot

    Returns:
        Decorated class with instrumented methods
    """
    exclude_methods = exclude_methods or []
    exclude_methods.extend(['__init__', '__del__', '__repr__', '__str__'])

    def decorator(cls: type) -> type:
        # Get all methods to instrument
        if methods is None:
            # Get all public methods
            method_names = [
                name for name in dir(cls)
                if not name.startswith('_')
                and callable(getattr(cls, name))
                and name not in exclude_methods
            ]
        else:
            method_names = [name for name in methods if name not in exclude_methods]

        # Instrument each method
        for method_name in method_names:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                instrumented_method = instrument_function(
                    function_name=f"{cls.__name__}.{method_name}",
                    model_parameters=model_parameters,
                    context=context,
                    capture_inputs=capture_inputs,
                    capture_outputs=capture_outputs,
                    auto_serialize=auto_serialize,
                    persist_snapshot=persist_snapshot,
                    client=client,
                    on_snapshot=on_snapshot,
                )(original_method)
                setattr(cls, method_name, instrumented_method)

        return cls

    return decorator


def capture_decision(
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    model_parameters: Optional[ModelParameters] = None,
    context: Optional[ExecutionContext] = None,
    function_name: str = "manual_capture",
) -> DecisionSnapshot:
    """
    Manually capture a decision snapshot.

    This is useful for capturing decisions that don't fit the decorator pattern.

    Args:
        inputs: Dictionary of inputs to capture
        outputs: Dictionary of outputs to capture
        model_parameters: Model parameters to include
        context: Execution context
        function_name: Name for the captured decision

    Returns:
        The created decision snapshot
    """
    instrument = BriefcaseInstrument(
        function_name=function_name,
        model_parameters=model_parameters,
        context=context,
    )

    # Add inputs
    if inputs:
        for name, value in inputs.items():
            instrument.add_input(name, value)

    # Add outputs
    if outputs:
        for name, value in outputs.items():
            instrument.add_output(name, value)

    return instrument.create_snapshot()


@contextmanager
def create_context(
    session_id: Optional[UUID] = None,
    trace_id: Optional[UUID] = None,
    parent_trace_id: Optional[UUID] = None,
    user_id: Optional[str] = None,
    environment: str = "production",
    tags: Optional[Dict[str, str]] = None,
):
    """
    Context manager for creating and managing execution context.

    Args:
        session_id: Session identifier
        trace_id: Trace identifier
        parent_trace_id: Parent trace ID
        user_id: User identifier
        environment: Environment name
        tags: Custom tags

    Yields:
        ExecutionContext: The created execution context
    """
    context = ExecutionContext(
        session_id=session_id,
        trace_id=trace_id,
        parent_trace_id=parent_trace_id,
        user_id=user_id,
        environment=environment,
        tags=tags or {},
    )

    yield context


# Convenience aliases
briefcase_instrument = BriefcaseInstrument
capture = instrument_function
