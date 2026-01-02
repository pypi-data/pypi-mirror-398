"""
explain-ok: Calculation-Level Model Explainability
===================================================

A Python library that provides transparent, step-by-step explanations
of computational operations.

Basic Usage
-----------
Using as a decorator:

    from explain_ok import explain
    
    @explain
    def calculate(x, y):
        a = x * 2
        b = a + y
        return b / 3
    
    result, explanation = calculate(5, 3)
    print(explanation.to_markdown())

Using with a context manager:

    from explain_ok import TraceContext, trace_value
    
    with TraceContext() as ctx:
        x = trace_value(5, "x")
        y = trace_value(3, "y")
        result = (x + y) * 2
        explanation = ctx.build_explanation(result)
    
    print(explanation.to_json())

Features
--------
- Traces arithmetic, comparison, and logical operations
- Produces JSON, Markdown, and plain text explanations
- Thread-safe using context variables
- Zero external dependencies
- Python 3.9+ compatible

For more information, see the README at:
https://github.com/yourusername/explain-ok
"""

from .api import explain, trace_value, explain_call
from .context import TraceContext
from .tracer import TracedValue
from .serializer import Explanation
from .nodes import OperationType, OperationNode
from .exceptions import ExplainOkError, NoActiveContextError, TracingError, SerializationError

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = [
    # Main API
    "explain",
    "trace_value",
    "explain_call",
    
    # Core classes
    "TraceContext",
    "TracedValue",
    "Explanation",
    
    # Node types
    "OperationType",
    "OperationNode",
    
    # Exceptions
    "ExplainOkError",
    "NoActiveContextError",
    "TracingError",
    "SerializationError",
    
    # Metadata
    "__version__",
]
