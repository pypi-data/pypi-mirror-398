"""
Explanation serialization and output formatting.

This module provides the Explanation class that represents the final
output of a traced computation, with support for multiple output formats.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import json

from .nodes import OperationNode


@dataclass
class Explanation:
    """
    The final explanation output containing the full computation trace.
    
    Provides multiple output formats including Python objects, JSON,
    Markdown, and dictionary representations.
    
    Attributes:
        operations: List of all recorded operation nodes.
        inputs: Dictionary mapping input names to their values.
        output: The final output value of the computation.
    """
    
    operations: List[OperationNode]
    inputs: Dict[str, Any]
    output: Any
    
    @property
    def steps(self) -> List[dict]:
        """
        Get all computation steps as a list of dictionaries.
        
        Returns:
            List of operation dictionaries.
        """
        return [op.to_dict() for op in self.operations]
    
    @property
    def step_count(self) -> int:
        """
        Get the number of operations performed.
        
        Returns:
            Count of operation steps.
        """
        return len(self.operations)
    
    @property
    def input_count(self) -> int:
        """
        Get the number of input values.
        
        Returns:
            Count of input values.
        """
        return len(self.inputs)
    
    def to_dict(self) -> dict:
        """
        Serialize the explanation to a dictionary.
        
        Returns:
            Dictionary representation of the explanation.
        """
        return {
            "inputs": self.inputs,
            "output": self._unwrap(self.output),
            "steps": self.steps,
            "step_count": self.step_count
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Serialize the explanation to a JSON string.
        
        Args:
            indent: Number of spaces for indentation (default 2).
        
        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_markdown(self) -> str:
        """
        Generate a human-readable Markdown report.
        
        Returns:
            Markdown formatted string.
        """
        lines = [
            "# Computation Explanation",
            "",
            "## Inputs",
            ""
        ]
        
        if self.inputs:
            for name, value in self.inputs.items():
                lines.append(f"- **{name}** = `{self._format_value(value)}`")
        else:
            lines.append("_No inputs registered._")
        
        lines.extend([
            "",
            "## Computation Steps",
            ""
        ])
        
        # Filter out input operations (they're already shown above)
        computation_ops = [
            op for op in self.operations 
            if op.operation.value != "input"
        ]
        
        if computation_ops:
            for i, op in enumerate(computation_ops, 1):
                # Format the expression cleanly
                expr = self._format_expression(op)
                result = self._format_value(op.result)
                lines.append(f"**Step {i}:** {expr} = `{result}`")
                lines.append("")  # Blank line between steps for readability
        else:
            lines.append("_No computations performed._")
        
        lines.extend([
            "## Result",
            "",
            f"**Output:** `{self._format_value(self.output)}`"
        ])
        
        return "\n".join(lines)
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value for display, rounding floats to reasonable precision.
        
        Args:
            value: The value to format.
        
        Returns:
            Formatted string representation.
        """
        unwrapped = self._unwrap(value)
        
        if isinstance(unwrapped, float):
            # Round to 6 decimal places, remove trailing zeros
            if unwrapped == int(unwrapped):
                return str(int(unwrapped))
            formatted = f"{unwrapped:.6f}".rstrip('0').rstrip('.')
            return formatted
        
        return str(unwrapped)
    
    def _format_expression(self, op) -> str:
        """
        Format an operation as a readable expression.
        
        Args:
            op: The operation node.
        
        Returns:
            Human-readable expression string.
        """
        from .nodes import OperationType, OPERATION_SYMBOLS
        
        operands = [self._format_value(o) for o in op.operands]
        symbol = OPERATION_SYMBOLS.get(op.operation, op.operation.value)
        
        if op.operation == OperationType.NEGATE:
            return f"-({operands[0]})"
        elif op.operation == OperationType.ABS:
            return f"abs({operands[0]})"
        elif op.operation == OperationType.POSITIVE:
            return f"+({operands[0]})"
        elif op.operation in (OperationType.NOT, OperationType.BITWISE_NOT):
            return f"{symbol}({operands[0]})"
        elif len(operands) == 2:
            return f"{operands[0]} {symbol} {operands[1]}"
        elif len(operands) == 1:
            return f"{symbol}({operands[0]})"
        else:
            return f"{op.operation.value}({', '.join(operands)})"
    
    def to_text(self) -> str:
        """
        Generate a plain text representation.
        
        Returns:
            Plain text formatted string.
        """
        lines = [
            "=== Computation Explanation ===",
            "",
            "INPUTS:"
        ]
        
        if self.inputs:
            for name, value in self.inputs.items():
                lines.append(f"  {name} = {value}")
        else:
            lines.append("  (none)")
        
        lines.extend(["", "COMPUTATION STEPS:"])
        
        for i, op in enumerate(self.operations, 1):
            expr = op.to_expression()
            lines.append(f"  [{i}] {expr}")
        
        lines.extend([
            "",
            f"OUTPUT: {self._unwrap(self.output)}",
            ""
        ])
        
        return "\n".join(lines)
    
    def _unwrap(self, value: Any) -> Any:
        """
        Unwrap a TracedValue to its raw value.
        
        Args:
            value: The value to unwrap.
        
        Returns:
            The raw underlying value.
        """
        if hasattr(value, 'value'):
            return value.value
        return value
    
    def __repr__(self) -> str:
        return f"Explanation(steps={self.step_count}, inputs={self.input_count}, output={self._unwrap(self.output)})"
    
    def __str__(self) -> str:
        return self.to_text()
