"""
Operation nodes for computation tracing.

This module defines the atomic units of computation tracking:
- OperationType: Enum of all supported operations
- OperationNode: Dataclass representing a single computation step
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from enum import Enum
import threading
import time


class OperationType(Enum):
    """Enumeration of all traceable operation types."""
    
    # Arithmetic operations
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    FLOOR_DIVIDE = "floor_divide"
    MODULO = "modulo"
    POWER = "power"
    NEGATE = "negate"
    POSITIVE = "positive"
    ABS = "abs"
    
    # Comparison operations
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    LESS_THAN = "less_than"
    LESS_EQUAL = "less_equal"
    GREATER_THAN = "greater_than"
    GREATER_EQUAL = "greater_equal"
    
    # Logical operations
    AND = "and"
    OR = "or"
    NOT = "not"
    
    # Bitwise operations
    BITWISE_AND = "bitwise_and"
    BITWISE_OR = "bitwise_or"
    BITWISE_XOR = "bitwise_xor"
    BITWISE_NOT = "bitwise_not"
    LEFT_SHIFT = "left_shift"
    RIGHT_SHIFT = "right_shift"
    
    # Special operations
    INPUT = "input"
    OUTPUT = "output"
    FUNCTION_CALL = "function_call"


# Mapping from operation type to symbol for display
OPERATION_SYMBOLS = {
    OperationType.ADD: "+",
    OperationType.SUBTRACT: "-",
    OperationType.MULTIPLY: "*",
    OperationType.DIVIDE: "/",
    OperationType.FLOOR_DIVIDE: "//",
    OperationType.MODULO: "%",
    OperationType.POWER: "**",
    OperationType.NEGATE: "-",
    OperationType.EQUAL: "==",
    OperationType.NOT_EQUAL: "!=",
    OperationType.LESS_THAN: "<",
    OperationType.LESS_EQUAL: "<=",
    OperationType.GREATER_THAN: ">",
    OperationType.GREATER_EQUAL: ">=",
    OperationType.AND: "and",
    OperationType.OR: "or",
    OperationType.NOT: "not",
    OperationType.BITWISE_AND: "&",
    OperationType.BITWISE_OR: "|",
    OperationType.BITWISE_XOR: "^",
    OperationType.BITWISE_NOT: "~",
    OperationType.LEFT_SHIFT: "<<",
    OperationType.RIGHT_SHIFT: ">>",
}


# Thread-safe counter for generating unique IDs
_id_counter = 0
_id_lock = threading.Lock()


def _generate_id() -> str:
    """Generate a unique identifier using thread-safe counter."""
    global _id_counter
    with _id_lock:
        _id_counter += 1
        return f"op_{_id_counter}"


@dataclass
class OperationNode:
    """
    Represents a single computation step in the trace.
    
    Attributes:
        id: Unique identifier for this operation
        operation: Type of operation performed
        operands: Input values to the operation
        result: Output value of the operation
        label: Optional variable name if this is an assignment
        timestamp_ns: Nanosecond timestamp relative to trace start
        parent_ids: IDs of nodes that produced the operands
    """
    
    id: str = field(default_factory=_generate_id)
    operation: OperationType = OperationType.INPUT
    operands: List[Any] = field(default_factory=list)
    result: Any = None
    label: Optional[str] = None
    timestamp_ns: int = field(default_factory=time.time_ns)
    parent_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """
        Serialize the operation node to a dictionary.
        
        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "id": self.id,
            "operation": self.operation.value,
            "operands": [self._serialize_value(op) for op in self.operands],
            "result": self._serialize_value(self.result),
            "label": self.label,
            "parent_ids": self.parent_ids,
        }
    
    def _serialize_value(self, value: Any) -> Any:
        """Convert a value to a serializable form."""
        # Handle TracedValue objects
        if hasattr(value, 'value'):
            return value.value
        return value
    
    def to_expression(self) -> str:
        """
        Convert the operation to a human-readable expression.
        
        Returns:
            String representation like "5 + 3 = 8"
        """
        if self.operation == OperationType.INPUT:
            if self.label:
                return f"{self.label} = {self._serialize_value(self.result)}"
            return str(self._serialize_value(self.result))
        
        symbol = OPERATION_SYMBOLS.get(self.operation, self.operation.value)
        serialized_operands = [self._serialize_value(op) for op in self.operands]
        serialized_result = self._serialize_value(self.result)
        
        # Unary operations
        if len(serialized_operands) == 1:
            return f"{symbol}({serialized_operands[0]}) = {serialized_result}"
        
        # Binary operations
        if len(serialized_operands) == 2:
            left, right = serialized_operands
            return f"{left} {symbol} {right} = {serialized_result}"
        
        # Fallback for other operations
        args = ", ".join(str(op) for op in serialized_operands)
        return f"{self.operation.value}({args}) = {serialized_result}"
    
    def __repr__(self) -> str:
        return f"OperationNode(id={self.id!r}, op={self.operation.value}, result={self.result})"
