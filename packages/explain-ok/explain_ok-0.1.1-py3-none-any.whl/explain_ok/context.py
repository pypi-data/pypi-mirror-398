"""
Trace context management for computation tracing.

This module provides the TraceContext class that manages active tracing sessions
using Python's contextvars for thread-safety.
"""

from contextvars import ContextVar
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import time

from .nodes import OperationNode, OperationType
from .exceptions import TracingError

if TYPE_CHECKING:
    from .tracer import TracedValue
    from .serializer import Explanation


# Default maximum operations to prevent memory exhaustion
DEFAULT_MAX_OPERATIONS = 100_000

# Context variable for thread-safe tracing
# Each thread/async task gets its own context
_active_context: ContextVar[Optional['TraceContext']] = ContextVar(
    'explain_ok_trace_context',
    default=None
)


@dataclass
class TraceContext:
    """
    Manages an active computation tracing session.
    
    Use as a context manager to activate tracing:
    
        with TraceContext() as ctx:
            x = ctx.register_input("x", 5)
            y = ctx.register_input("y", 3)
            result = x + y  # Automatically traced
            explanation = ctx.build_explanation(result)
    
    Attributes:
        operations: List of all recorded operations
        inputs: Dictionary of named input values
    """
    
    operations: List[OperationNode] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    max_operations: int = DEFAULT_MAX_OPERATIONS
    _start_time_ns: int = field(default_factory=time.time_ns)
    _token: Any = field(default=None, repr=False)
    
    def __enter__(self) -> 'TraceContext':
        """Activate this context for the current thread/task."""
        self._token = _active_context.set(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Deactivate this context."""
        if self._token is not None:
            _active_context.reset(self._token)
            self._token = None
        return False  # Don't suppress exceptions
    
    def record(self, node: OperationNode) -> None:
        """
        Record an operation to the trace.
        
        Args:
            node: The operation node to record.
        
        Raises:
            TracingError: If maximum operations limit is exceeded.
        """
        # Check operation limit to prevent memory exhaustion
        if len(self.operations) >= self.max_operations:
            raise TracingError(
                f"Maximum operations limit ({self.max_operations}) exceeded. "
                f"Use TraceContext(max_operations=N) to increase the limit."
            )
        
        # Set relative timestamp
        node.timestamp_ns = time.time_ns() - self._start_time_ns
        self.operations.append(node)
    
    def register_input(self, name: str, value: Any) -> 'TracedValue':
        """
        Register an input value and return a traced wrapper.
        
        Args:
            name: The name/label for this input.
            value: The actual value.
        
        Returns:
            A TracedValue wrapping the input that will trace operations.
        """
        from .tracer import TracedValue
        
        # Create an input node
        node = OperationNode(
            operation=OperationType.INPUT,
            operands=[],
            result=value,
            label=name
        )
        self.record(node)
        
        # Store in inputs dict
        self.inputs[name] = value
        
        # Return wrapped value
        return TracedValue(value, node_id=node.id, label=name)
    
    def build_explanation(self, final_result: Any) -> 'Explanation':
        """
        Build the final explanation from the collected trace.
        
        Args:
            final_result: The final output of the computation.
        
        Returns:
            An Explanation object containing the full trace.
        """
        from .serializer import Explanation
        
        # Unwrap if TracedValue
        if hasattr(final_result, 'value'):
            output_value = final_result.value
        else:
            output_value = final_result
        
        return Explanation(
            operations=self.operations.copy(),
            inputs=self.inputs.copy(),
            output=output_value
        )
    
    @staticmethod
    def get_current() -> Optional['TraceContext']:
        """
        Get the currently active TraceContext, if any.
        
        Returns:
            The active TraceContext, or None if not in a tracing session.
        """
        return _active_context.get()
    
    @staticmethod
    def is_active() -> bool:
        """
        Check if there is an active tracing context.
        
        Returns:
            True if currently inside a TraceContext, False otherwise.
        """
        return _active_context.get() is not None
    
    def __repr__(self) -> str:
        return f"TraceContext(operations={len(self.operations)}, inputs={list(self.inputs.keys())})"
