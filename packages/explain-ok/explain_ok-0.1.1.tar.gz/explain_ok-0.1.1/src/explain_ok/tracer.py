"""
Traced value wrapper for transparent operation tracking.

This module provides the TracedValue class that wraps numeric and boolean values,
intercepting all operations through operator overloading.
"""

from typing import Any, Optional, Union
from .nodes import OperationNode, OperationType
from .context import TraceContext


class TracedValue:
    """
    A wrapper around values that transparently traces all operations.
    
    When used within a TraceContext, all arithmetic, comparison, and logical
    operations are automatically recorded.
    
    Attributes:
        value: The underlying wrapped value.
        node_id: ID of the operation node that produced this value.
        label: Optional name/label for this value.
    """
    
    __slots__ = ('value', 'node_id', 'label')
    
    def __init__(
        self,
        value: Any,
        node_id: Optional[str] = None,
        label: Optional[str] = None
    ):
        """
        Initialize a TracedValue.
        
        Args:
            value: The value to wrap.
            node_id: Optional ID of the producing operation node.
            label: Optional name/label for display purposes.
        """
        self.value = value
        self.node_id = node_id
        self.label = label
    
    def _get_value(self, other: Any) -> Any:
        """Extract the raw value from a TracedValue or return as-is."""
        if isinstance(other, TracedValue):
            return other.value
        return other
    
    def _get_node_id(self, other: Any) -> Optional[str]:
        """Get the node ID from a TracedValue, or None."""
        if isinstance(other, TracedValue):
            return other.node_id
        return None
    
    def _record_binary_op(
        self,
        operation: OperationType,
        other: Any,
        result: Any,
        reverse: bool = False
    ) -> 'TracedValue':
        """
        Record a binary operation and return a new TracedValue.
        
        Args:
            operation: The type of operation.
            other: The other operand.
            result: The result of the operation.
            reverse: If True, 'other' is the left operand.
        
        Returns:
            A new TracedValue wrapping the result.
        """
        ctx = TraceContext.get_current()
        
        if ctx is None:
            # Not in a tracing context, just return the result wrapped
            return TracedValue(result)
        
        other_value = self._get_value(other)
        
        # Determine operand order
        if reverse:
            operands = [other_value, self.value]
            parent_ids = [self._get_node_id(other), self.node_id]
        else:
            operands = [self.value, other_value]
            parent_ids = [self.node_id, self._get_node_id(other)]
        
        # Filter out None parent IDs
        parent_ids = [pid for pid in parent_ids if pid is not None]
        
        # Create and record the operation node
        node = OperationNode(
            operation=operation,
            operands=operands,
            result=result,
            parent_ids=parent_ids
        )
        ctx.record(node)
        
        return TracedValue(result, node_id=node.id)
    
    def _record_unary_op(
        self,
        operation: OperationType,
        result: Any
    ) -> 'TracedValue':
        """
        Record a unary operation and return a new TracedValue.
        
        Args:
            operation: The type of operation.
            result: The result of the operation.
        
        Returns:
            A new TracedValue wrapping the result.
        """
        ctx = TraceContext.get_current()
        
        if ctx is None:
            return TracedValue(result)
        
        parent_ids = [self.node_id] if self.node_id else []
        
        node = OperationNode(
            operation=operation,
            operands=[self.value],
            result=result,
            parent_ids=parent_ids
        )
        ctx.record(node)
        
        return TracedValue(result, node_id=node.id)
    
    # ========== Arithmetic Operations ==========
    
    def __add__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value + other_value
        return self._record_binary_op(OperationType.ADD, other, result)
    
    def __radd__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value + self.value
        return self._record_binary_op(OperationType.ADD, other, result, reverse=True)
    
    def __sub__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value - other_value
        return self._record_binary_op(OperationType.SUBTRACT, other, result)
    
    def __rsub__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value - self.value
        return self._record_binary_op(OperationType.SUBTRACT, other, result, reverse=True)
    
    def __mul__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value * other_value
        return self._record_binary_op(OperationType.MULTIPLY, other, result)
    
    def __rmul__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value * self.value
        return self._record_binary_op(OperationType.MULTIPLY, other, result, reverse=True)
    
    def __truediv__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value / other_value
        return self._record_binary_op(OperationType.DIVIDE, other, result)
    
    def __rtruediv__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value / self.value
        return self._record_binary_op(OperationType.DIVIDE, other, result, reverse=True)
    
    def __floordiv__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value // other_value
        return self._record_binary_op(OperationType.FLOOR_DIVIDE, other, result)
    
    def __rfloordiv__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value // self.value
        return self._record_binary_op(OperationType.FLOOR_DIVIDE, other, result, reverse=True)
    
    def __mod__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value % other_value
        return self._record_binary_op(OperationType.MODULO, other, result)
    
    def __rmod__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value % self.value
        return self._record_binary_op(OperationType.MODULO, other, result, reverse=True)
    
    def __pow__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value ** other_value
        return self._record_binary_op(OperationType.POWER, other, result)
    
    def __rpow__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value ** self.value
        return self._record_binary_op(OperationType.POWER, other, result, reverse=True)
    
    def __neg__(self) -> 'TracedValue':
        result = -self.value
        return self._record_unary_op(OperationType.NEGATE, result)
    
    def __pos__(self) -> 'TracedValue':
        result = +self.value
        return self._record_unary_op(OperationType.POSITIVE, result)
    
    def __abs__(self) -> 'TracedValue':
        result = abs(self.value)
        return self._record_unary_op(OperationType.ABS, result)
    
    # ========== Comparison Operations ==========
    
    def __eq__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value == other_value
        return self._record_binary_op(OperationType.EQUAL, other, result)
    
    def __ne__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value != other_value
        return self._record_binary_op(OperationType.NOT_EQUAL, other, result)
    
    def __lt__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value < other_value
        return self._record_binary_op(OperationType.LESS_THAN, other, result)
    
    def __le__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value <= other_value
        return self._record_binary_op(OperationType.LESS_EQUAL, other, result)
    
    def __gt__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value > other_value
        return self._record_binary_op(OperationType.GREATER_THAN, other, result)
    
    def __ge__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value >= other_value
        return self._record_binary_op(OperationType.GREATER_EQUAL, other, result)
    
    # ========== Bitwise Operations ==========
    
    def __and__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value & other_value
        return self._record_binary_op(OperationType.BITWISE_AND, other, result)
    
    def __rand__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value & self.value
        return self._record_binary_op(OperationType.BITWISE_AND, other, result, reverse=True)
    
    def __or__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value | other_value
        return self._record_binary_op(OperationType.BITWISE_OR, other, result)
    
    def __ror__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value | self.value
        return self._record_binary_op(OperationType.BITWISE_OR, other, result, reverse=True)
    
    def __xor__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value ^ other_value
        return self._record_binary_op(OperationType.BITWISE_XOR, other, result)
    
    def __rxor__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value ^ self.value
        return self._record_binary_op(OperationType.BITWISE_XOR, other, result, reverse=True)
    
    def __invert__(self) -> 'TracedValue':
        result = ~self.value
        return self._record_unary_op(OperationType.BITWISE_NOT, result)
    
    def __lshift__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value << other_value
        return self._record_binary_op(OperationType.LEFT_SHIFT, other, result)
    
    def __rlshift__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value << self.value
        return self._record_binary_op(OperationType.LEFT_SHIFT, other, result, reverse=True)
    
    def __rshift__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = self.value >> other_value
        return self._record_binary_op(OperationType.RIGHT_SHIFT, other, result)
    
    def __rrshift__(self, other) -> 'TracedValue':
        other_value = self._get_value(other)
        result = other_value >> self.value
        return self._record_binary_op(OperationType.RIGHT_SHIFT, other, result, reverse=True)
    
    # ========== Type Conversion ==========
    
    def __float__(self) -> float:
        return float(self.value)
    
    def __int__(self) -> int:
        return int(self.value)
    
    def __bool__(self) -> bool:
        # For boolean context, return the raw bool
        # We can't return a TracedValue here
        return bool(self.value)
    
    def __index__(self) -> int:
        return int(self.value)
    
    # ========== String Representations ==========
    
    def __repr__(self) -> str:
        if self.label:
            return f"TracedValue({self.label}={self.value})"
        return f"TracedValue({self.value})"
    
    def __str__(self) -> str:
        return str(self.value)
    
    # ========== Hash (for use in dicts/sets) ==========
    
    def __hash__(self) -> int:
        return hash((self.value, self.node_id))
