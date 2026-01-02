"""
Public API for explain-ok library.

This module provides the main user-facing interface:
- explain(): Decorator/function wrapper for computation tracing
- trace_value(): Manual value wrapping utility
"""

from typing import Any, Callable, Dict, Optional, Tuple, Union
from functools import wraps
import inspect

from .context import TraceContext
from .tracer import TracedValue
from .serializer import Explanation


def explain(
    func: Callable = None,
    *,
    include_result: bool = True
) -> Union[Callable, Tuple[Any, Explanation]]:
    """
    Trace and explain the computation performed by a function.
    
    Can be used as a decorator:
    
        @explain
        def calculate(x, y):
            return (x + y) * 2
        
        result, explanation = calculate(5, 3)
    
    Or with configuration:
    
        @explain(include_result=True)
        def calculate(x, y):
            return (x + y) * 2
    
    Args:
        func: The function to trace (when used without parentheses).
        include_result: If True, return (result, explanation) tuple.
                       If False, return only the result but still trace.
    
    Returns:
        When used as decorator: A wrapped function that returns
        (result, explanation) tuple when called.
    
    Example:
        >>> @explain
        ... def add_and_double(a, b):
        ...     return (a + b) * 2
        ...
        >>> result, expl = add_and_double(3, 5)
        >>> print(result)
        16
        >>> print(expl.to_markdown())
        # Computation Explanation
        ...
    """
    
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Union[Tuple[Any, Explanation], Any]:
            with TraceContext() as ctx:
                # Get parameter names from function signature
                sig = inspect.signature(fn)
                param_names = list(sig.parameters.keys())
                
                # Convert positional args to traced values
                traced_args = []
                for i, arg in enumerate(args):
                    if i < len(param_names):
                        name = param_names[i]
                    else:
                        name = f"arg_{i}"
                    traced_args.append(ctx.register_input(name, arg))
                
                # Convert keyword args to traced values
                traced_kwargs = {}
                for key, value in kwargs.items():
                    traced_kwargs[key] = ctx.register_input(key, value)
                
                # Execute the function with traced values
                result = fn(*traced_args, **traced_kwargs)
                
                # Build the explanation
                explanation = ctx.build_explanation(result)
                
                # Unwrap result if it's a TracedValue
                if isinstance(result, TracedValue):
                    final_result = result.value
                else:
                    final_result = result
                
                if include_result:
                    return final_result, explanation
                else:
                    return final_result
        
        return wrapper
    
    # Handle @explain without parentheses
    if func is not None:
        return decorator(func)
    
    # Handle @explain() with parentheses
    return decorator


def trace_value(value: Any, name: Optional[str] = None) -> TracedValue:
    """
    Manually wrap a value for tracing.
    
    Useful when you want to trace specific values inside existing code
    without using the decorator pattern.
    
    Args:
        value: The value to trace.
        name: Optional label for the value.
    
    Returns:
        A TracedValue that will record operations when used within
        a TraceContext.
    
    Example:
        >>> with TraceContext() as ctx:
        ...     x = trace_value(5, "x")
        ...     y = trace_value(3, "y")
        ...     result = x + y
        ...     explanation = ctx.build_explanation(result)
        >>> print(explanation.to_text())
    """
    ctx = TraceContext.get_current()
    
    if ctx is not None:
        return ctx.register_input(name or "value", value)
    
    # Not in a context, return a plain TracedValue
    return TracedValue(value, label=name)


def explain_call(
    func: Callable,
    *args,
    **kwargs
) -> Tuple[Any, Explanation]:
    """
    Trace a single function call without using the decorator.
    
    Useful for tracing functions you don't own or can't decorate.
    
    Args:
        func: The function to call and trace.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
    
    Returns:
        Tuple of (result, explanation).
    
    Example:
        >>> def external_function(x, y):
        ...     return x ** 2 + y ** 2
        ...
        >>> result, explanation = explain_call(external_function, 3, 4)
        >>> print(result)
        25
    """
    wrapped = explain(func)
    return wrapped(*args, **kwargs)
