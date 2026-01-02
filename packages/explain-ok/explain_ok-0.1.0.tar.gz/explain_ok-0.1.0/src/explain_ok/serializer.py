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
                lines.append(f"- **{name}**: `{value}`")
        else:
            lines.append("_No inputs registered._")
        
        lines.extend([
            "",
            "## Computation Steps",
            ""
        ])
        
        if self.operations:
            lines.extend([
                "| Step | Operation | Expression | Result |",
                "|------|-----------|------------|--------|"
            ])
            
            for i, op in enumerate(self.operations, 1):
                expr = op.to_expression()
                result = self._unwrap(op.result)
                lines.append(f"| {i} | `{op.operation.value}` | `{expr}` | `{result}` |")
        else:
            lines.append("_No operations recorded._")
        
        lines.extend([
            "",
            "## Final Output",
            "",
            f"**Result**: `{self._unwrap(self.output)}`"
        ])
        
        return "\n".join(lines)
    
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
