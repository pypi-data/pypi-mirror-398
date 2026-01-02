"""
Basic usage examples for explain-ok library.

This file demonstrates the main ways to use the library:
1. Using the @explain decorator
2. Using TraceContext directly
3. Using explain_call for external functions
"""

from explain_ok import explain, TraceContext, trace_value, explain_call, Explanation


# =============================================================================
# Example 1: Basic decorator usage
# =============================================================================

@explain
def simple_calculation(x, y):
    """A simple calculation to demonstrate tracing."""
    a = x + y
    b = a * 2
    return b - 1


def example_decorator():
    """Demonstrate the @explain decorator."""
    print("=" * 60)
    print("Example 1: Using @explain decorator")
    print("=" * 60)
    
    result, explanation = simple_calculation(5, 3)
    
    print(f"\nResult: {result}")
    print(f"Number of steps: {explanation.step_count}")
    print("\nMarkdown output:")
    print(explanation.to_markdown())


# =============================================================================
# Example 2: Scientific formula
# =============================================================================

@explain
def quadratic_roots(a, b, c):
    """
    Calculate the roots of a quadratic equation ax² + bx + c = 0
    using the quadratic formula.
    
    Returns only the positive root for simplicity.
    """
    discriminant = b ** 2 - 4 * a * c
    root = (-b + discriminant ** 0.5) / (2 * a)
    return root


def example_quadratic():
    """Demonstrate tracing a scientific formula."""
    print("\n" + "=" * 60)
    print("Example 2: Quadratic Formula")
    print("=" * 60)
    
    # Solve x² - 5x + 6 = 0 (roots are 2 and 3)
    result, explanation = quadratic_roots(1, -5, 6)
    
    print(f"\nSolving: x² - 5x + 6 = 0")
    print(f"Root found: {result}")
    print("\nComputation trace (text format):")
    print(explanation.to_text())


# =============================================================================
# Example 3: Using TraceContext directly
# =============================================================================

def example_context_manager():
    """Demonstrate using TraceContext directly."""
    print("\n" + "=" * 60)
    print("Example 3: Using TraceContext")
    print("=" * 60)
    
    with TraceContext() as ctx:
        # Register inputs
        length = ctx.register_input("length", 10)
        width = ctx.register_input("width", 5)
        height = ctx.register_input("height", 3)
        
        # Calculate volume
        area = length * width
        volume = area * height
        
        # Build explanation
        explanation = ctx.build_explanation(volume)
    
    print(f"\nCalculating volume of a box:")
    print(f"Length: 10, Width: 5, Height: 3")
    print(f"Volume: {explanation.output}")
    print("\nJSON output:")
    print(explanation.to_json())


# =============================================================================
# Example 4: Tracing external functions
# =============================================================================

def distance_3d(x1, y1, z1, x2, y2, z2):
    """Calculate 3D Euclidean distance (external function)."""
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    return (dx**2 + dy**2 + dz**2) ** 0.5


def example_external_function():
    """Demonstrate tracing an external function."""
    print("\n" + "=" * 60)
    print("Example 4: Tracing External Functions")
    print("=" * 60)
    
    # Trace the external function
    result, explanation = explain_call(
        distance_3d, 
        0, 0, 0,  # Point 1
        3, 4, 0   # Point 2
    )
    
    print(f"\nCalculating distance from (0,0,0) to (3,4,0)")
    print(f"Distance: {result}")
    print(f"Steps performed: {explanation.step_count}")
    print("\nInputs captured:")
    for name, value in explanation.inputs.items():
        print(f"  {name} = {value}")


# =============================================================================
# Example 5: Financial calculation
# =============================================================================

@explain
def compound_interest(principal, rate, years, compounds_per_year):
    """
    Calculate compound interest.
    
    A = P(1 + r/n)^(nt)
    
    Where:
    - P = principal
    - r = annual interest rate
    - n = compounds per year
    - t = time in years
    """
    rate_per_period = rate / compounds_per_year
    total_periods = compounds_per_year * years
    growth_factor = (1 + rate_per_period) ** total_periods
    final_amount = principal * growth_factor
    return final_amount


def example_financial():
    """Demonstrate a financial calculation."""
    print("\n" + "=" * 60)
    print("Example 5: Compound Interest Calculation")
    print("=" * 60)
    
    result, explanation = compound_interest(
        principal=10000,
        rate=0.08,
        years=5,
        compounds_per_year=12
    )
    
    print(f"\nPrincipal: $10,000")
    print(f"Annual Rate: 8%")
    print(f"Years: 5")
    print(f"Compounding: Monthly")
    print(f"\nFinal Amount: ${result:,.2f}")
    print(f"\nTotal computation steps: {explanation.step_count}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    example_decorator()
    example_quadratic()
    example_context_manager()
    example_external_function()
    example_financial()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
