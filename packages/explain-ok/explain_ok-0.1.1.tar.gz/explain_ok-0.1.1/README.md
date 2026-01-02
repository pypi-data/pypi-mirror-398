# explain-ok

**Calculation-Level Explainability for Python Computations**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`explain-ok` is a Python library that provides transparent, step-by-step explanations of computational operations. Instead of answering *"Which feature was important?"*, it answers:

> **"What exact sequence of calculations was executed to produce this output?"**

## Features

- 🔍 **Traces all operations**: Arithmetic, comparison, and logical operations
- 📊 **Multiple output formats**: JSON, Markdown, plain text
- 🧵 **Thread-safe**: Uses Python's `contextvars` for safe concurrent usage
- 🪶 **Zero dependencies**: Pure Python with no external requirements
- 🐍 **Python 3.9+**: Modern Python compatibility

## Installation

```bash
pip install explain-ok
```

## Quick Start

### Using the `@explain` Decorator

```python
from explain_ok import explain

@explain
def calculate_interest(principal, rate, years):
    interest = principal * rate * years
    total = principal + interest
    return total

result, explanation = calculate_interest(1000, 0.05, 3)

print(f"Result: {result}")
print(explanation.to_markdown())
```

**Output:**
```
Result: 1150.0

# Computation Explanation

## Inputs
- **principal**: `1000`
- **rate**: `0.05`
- **years**: `3`

## Computation Steps
| Step | Operation | Expression | Result |
|------|-----------|------------|--------|
| 1 | `input` | `principal = 1000` | `1000` |
| 2 | `input` | `rate = 0.05` | `0.05` |
| 3 | `input` | `years = 3` | `3` |
| 4 | `multiply` | `1000 * 0.05 = 50.0` | `50.0` |
| 5 | `multiply` | `50.0 * 3 = 150.0` | `150.0` |
| 6 | `add` | `1000 + 150.0 = 1150.0` | `1150.0` |

## Final Output
**Result**: `1150.0`
```

### Using TraceContext Directly

```python
from explain_ok import TraceContext, trace_value

with TraceContext() as ctx:
    x = trace_value(5, "x")
    y = trace_value(3, "y")
    
    result = (x + y) ** 2
    
    explanation = ctx.build_explanation(result)

print(explanation.to_json())
```

### Tracing External Functions

```python
from explain_ok import explain_call

def external_formula(a, b, c):
    return (-b + (b**2 - 4*a*c)**0.5) / (2*a)

result, explanation = explain_call(external_formula, 1, -5, 6)
print(f"Root: {result}")  # Root: 3.0
```

## Output Formats

### JSON

```python
explanation.to_json()
```

Returns a JSON string with full trace data, perfect for APIs and storage.

### Markdown

```python
explanation.to_markdown()
```

Human-readable Markdown table, ideal for reports and documentation.

### Plain Text

```python
explanation.to_text()
# or
print(explanation)
```

Simple text format for quick debugging.

### Dictionary

```python
explanation.to_dict()
```

Python dictionary for programmatic access.

## API Reference

### `@explain`

Decorator to trace a function's computations.

```python
@explain
def my_function(x, y):
    return x + y

result, explanation = my_function(5, 3)
```

### `explain_call(func, *args, **kwargs)`

Trace a single function call without decoration.

```python
result, explanation = explain_call(some_function, arg1, arg2)
```

### `trace_value(value, name=None)`

Manually wrap a value for tracing.

```python
with TraceContext() as ctx:
    x = trace_value(5, "x")
    # ... use x in calculations
```

### `TraceContext`

Context manager for manual tracing sessions.

```python
with TraceContext() as ctx:
    # Register inputs
    a = ctx.register_input("a", 10)
    b = ctx.register_input("b", 20)
    
    # Perform calculations
    result = a + b
    
    # Build explanation
    explanation = ctx.build_explanation(result)
```

### `Explanation`

The output object containing the trace.

- `.steps` - List of operation dictionaries
- `.step_count` - Number of operations
- `.inputs` - Input values dictionary
- `.output` - Final result
- `.to_json()` - JSON string
- `.to_markdown()` - Markdown string
- `.to_text()` - Plain text string
- `.to_dict()` - Dictionary

## Supported Operations

### Arithmetic
`+`, `-`, `*`, `/`, `//`, `%`, `**`, unary `-`, `abs()`

### Comparison
`==`, `!=`, `<`, `<=`, `>`, `>=`

### Bitwise
`&`, `|`, `^`, `~`, `<<`, `>>`

## Use Cases

- **Debugging**: Understand exactly what your calculations are doing
- **Auditing**: Create audit trails for financial or scientific computations
- **Education**: Teach how formulas work step-by-step
- **Reproducibility**: Document computation paths for research
- **Validation**: Verify that formulas are implemented correctly

## Security Considerations

> ⚠️ **Sensitive Data Warning**: All intermediate values are captured in the trace. **Do not** use `explain-ok` on functions that handle:
> - Passwords or credentials
> - API keys or tokens
> - Personally identifiable information (PII)
> - Any other sensitive data

### Operation Limits

To prevent memory exhaustion, `TraceContext` has a default limit of 100,000 operations. You can adjust this:

```python
# Increase limit for large computations
with TraceContext(max_operations=500_000) as ctx:
    # ... many operations
```

## License

MIT License - see [LICENSE](LICENSE) for details.
