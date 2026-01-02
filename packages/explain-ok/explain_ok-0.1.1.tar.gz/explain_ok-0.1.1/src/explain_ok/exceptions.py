"""
Custom exceptions for explain-ok library.
"""


class ExplainOkError(Exception):
    """Base exception for all explain-ok errors."""
    pass


class NoActiveContextError(ExplainOkError):
    """Raised when an operation requires an active TraceContext but none exists."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message or "No active TraceContext. Use 'with TraceContext():' or the @explain decorator."
        )


class TracingError(ExplainOkError):
    """Raised when an error occurs during computation tracing."""
    pass


class SerializationError(ExplainOkError):
    """Raised when an error occurs during explanation serialization."""
    pass
