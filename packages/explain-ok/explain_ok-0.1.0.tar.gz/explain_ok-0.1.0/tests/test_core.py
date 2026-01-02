"""
Tests for explain-ok library core functionality.
"""

import pytest
from explain_ok import (
    explain,
    trace_value,
    explain_call,
    TraceContext,
    TracedValue,
    Explanation,
    OperationType,
)


class TestExplainDecorator:
    """Test the @explain decorator."""
    
    def test_simple_addition(self):
        """Test basic addition tracing."""
        @explain
        def add(x, y):
            return x + y
        
        result, explanation = add(5, 3)
        
        assert result == 8
        assert isinstance(explanation, Explanation)
        assert explanation.output == 8
        assert explanation.step_count >= 3  # 2 inputs + 1 add
    
    def test_multiple_operations(self):
        """Test tracing multiple operations."""
        @explain
        def compute(a, b):
            c = a + b
            d = c * 2
            return d - 1
        
        result, explanation = compute(3, 4)
        
        assert result == 13  # (3 + 4) * 2 - 1 = 13
        assert explanation.output == 13
    
    def test_inputs_recorded(self):
        """Test that inputs are properly recorded."""
        @explain
        def func(x, y, z):
            return x + y + z
        
        result, explanation = func(1, 2, 3)
        
        assert "x" in explanation.inputs
        assert "y" in explanation.inputs
        assert "z" in explanation.inputs
        assert explanation.inputs["x"] == 1
        assert explanation.inputs["y"] == 2
        assert explanation.inputs["z"] == 3
    
    def test_kwargs_support(self):
        """Test that keyword arguments are traced."""
        @explain
        def func(a, b):
            return a * b
        
        result, explanation = func(a=4, b=5)
        
        assert result == 20
        assert explanation.inputs["a"] == 4
        assert explanation.inputs["b"] == 5


class TestArithmeticOperations:
    """Test arithmetic operation tracing."""
    
    def test_addition(self):
        @explain
        def add(x, y):
            return x + y
        
        result, _ = add(10, 5)
        assert result == 15
    
    def test_subtraction(self):
        @explain
        def sub(x, y):
            return x - y
        
        result, _ = sub(10, 3)
        assert result == 7
    
    def test_multiplication(self):
        @explain
        def mul(x, y):
            return x * y
        
        result, _ = mul(4, 5)
        assert result == 20
    
    def test_division(self):
        @explain
        def div(x, y):
            return x / y
        
        result, _ = div(15, 3)
        assert result == 5.0
    
    def test_floor_division(self):
        @explain
        def floordiv(x, y):
            return x // y
        
        result, _ = floordiv(17, 5)
        assert result == 3
    
    def test_modulo(self):
        @explain
        def mod(x, y):
            return x % y
        
        result, _ = mod(17, 5)
        assert result == 2
    
    def test_power(self):
        @explain
        def power(x, y):
            return x ** y
        
        result, _ = power(2, 3)
        assert result == 8
    
    def test_negation(self):
        @explain
        def neg(x):
            return -x
        
        result, _ = neg(5)
        assert result == -5
    
    def test_reverse_operations(self):
        """Test reverse operations (e.g., 5 + traced_value)."""
        @explain
        def compute(x):
            return 10 + x  # This uses __radd__
        
        result, _ = compute(3)
        assert result == 13


class TestComparisonOperations:
    """Test comparison operation tracing."""
    
    def test_equal(self):
        @explain
        def eq(x, y):
            return x == y
        
        result, _ = eq(5, 5)
        # Result is a TracedValue with value True
        assert result == True or (hasattr(result, 'value') and result.value == True)
    
    def test_less_than(self):
        @explain
        def lt(x, y):
            return x < y
        
        result, _ = lt(3, 5)
        assert result == True or (hasattr(result, 'value') and result.value == True)
    
    def test_greater_than(self):
        @explain
        def gt(x, y):
            return x > y
        
        result, _ = gt(10, 5)
        assert result == True or (hasattr(result, 'value') and result.value == True)


class TestTraceContext:
    """Test TraceContext functionality."""
    
    def test_context_manager(self):
        """Test basic context manager usage."""
        with TraceContext() as ctx:
            x = ctx.register_input("x", 5)
            y = ctx.register_input("y", 3)
            result = x + y
            explanation = ctx.build_explanation(result)
        
        assert explanation.output == 8
        assert len(ctx.operations) >= 3
    
    def test_nested_contexts(self):
        """Test that nested contexts work independently."""
        with TraceContext() as outer:
            x = outer.register_input("x", 10)
            
            with TraceContext() as inner:
                y = inner.register_input("y", 5)
                inner_result = y * 2
                inner_explanation = inner.build_explanation(inner_result)
            
            outer_result = x + 1
            outer_explanation = outer.build_explanation(outer_result)
        
        assert inner_explanation.output == 10
        assert outer_explanation.output == 11
    
    def test_is_active(self):
        """Test is_active() method."""
        assert not TraceContext.is_active()
        
        with TraceContext():
            assert TraceContext.is_active()
        
        assert not TraceContext.is_active()


class TestTraceValue:
    """Test trace_value function."""
    
    def test_within_context(self):
        """Test trace_value within a context."""
        with TraceContext() as ctx:
            x = trace_value(5, "x")
            y = trace_value(3, "y")
            result = x * y
            explanation = ctx.build_explanation(result)
        
        assert explanation.output == 15
    
    def test_outside_context(self):
        """Test trace_value outside a context still works."""
        x = trace_value(5, "x")
        y = trace_value(3, "y")
        result = x + y
        
        # Should still compute correctly
        assert result.value == 8


class TestExplanationOutput:
    """Test explanation output formats."""
    
    def test_to_dict(self):
        """Test dictionary output."""
        @explain
        def compute(x, y):
            return x + y
        
        _, explanation = compute(2, 3)
        d = explanation.to_dict()
        
        assert "inputs" in d
        assert "output" in d
        assert "steps" in d
        assert "step_count" in d
        assert d["output"] == 5
    
    def test_to_json(self):
        """Test JSON output."""
        @explain
        def compute(x, y):
            return x * y
        
        _, explanation = compute(4, 5)
        json_str = explanation.to_json()
        
        import json
        parsed = json.loads(json_str)
        assert parsed["output"] == 20
    
    def test_to_markdown(self):
        """Test Markdown output."""
        @explain
        def compute(x, y):
            return x + y
        
        _, explanation = compute(1, 2)
        md = explanation.to_markdown()
        
        assert "# Computation Explanation" in md
        assert "## Inputs" in md
        assert "## Computation Steps" in md
        assert "## Final Output" in md
    
    def test_to_text(self):
        """Test plain text output."""
        @explain
        def compute(x, y):
            return x - y
        
        _, explanation = compute(10, 4)
        text = explanation.to_text()
        
        assert "INPUTS:" in text
        assert "COMPUTATION STEPS:" in text
        assert "OUTPUT:" in text


class TestExplainCall:
    """Test explain_call function."""
    
    def test_basic_call(self):
        """Test tracing an external function."""
        def external_func(a, b):
            return a ** 2 + b ** 2
        
        result, explanation = explain_call(external_func, 3, 4)
        
        assert result == 25  # 9 + 16
        assert explanation.output == 25


class TestComplexFormulas:
    """Test complex real-world formulas."""
    
    def test_quadratic_formula_discriminant(self):
        """Test quadratic discriminant calculation."""
        @explain
        def discriminant(a, b, c):
            return b ** 2 - 4 * a * c
        
        result, explanation = discriminant(1, 5, 6)
        
        assert result == 1  # 25 - 24 = 1
        assert explanation.step_count >= 6  # inputs + operations
    
    def test_distance_formula(self):
        """Test 2D distance calculation."""
        @explain
        def distance_squared(x1, y1, x2, y2):
            dx = x2 - x1
            dy = y2 - y1
            return dx ** 2 + dy ** 2
        
        result, explanation = distance_squared(0, 0, 3, 4)
        
        assert result == 25  # 9 + 16
    
    def test_compound_interest(self):
        """Test compound interest formula."""
        @explain
        def compound_amount(principal, rate, time):
            # A = P * (1 + r)^t
            return principal * (1 + rate) ** time
        
        result, explanation = compound_amount(1000, 0.05, 2)
        
        assert abs(result - 1102.5) < 0.01  # 1000 * 1.05^2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
