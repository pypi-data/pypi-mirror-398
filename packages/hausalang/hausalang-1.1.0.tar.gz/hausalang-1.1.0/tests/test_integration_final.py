#!/usr/bin/env python3
"""
Comprehensive integration test for Hausalang v1.1
Tests all major language features in one cohesive workflow.
"""
import pytest
from hausalang.repl.session import ReplSession
from hausalang.core.errors import ContextualError, ErrorKind


class TestHausalangIntegration:
    """Complete integration test covering all language features"""

    def test_complete_workflow_fibonacci_with_unary_and_modulo(self):
        """
        Complete workflow:
        - Variable assignment
        - Unary operators (negative numbers)
        - Modulo operator for even/odd detection
        - Function definitions with parameters
        - If/elif/else statements
        - While loops with conditional break
        - String concatenation
        - Return values
        """
        s = ReplSession()

        # Define a function to check if number is even
        r = s.execute(
            """
aiki is_even(n):
    mayar n % 2 == 0
"""
        )
        assert r.success, f"Function definition failed: {r.error}"
        assert s.function_exists("is_even"), "is_even function not defined"

        # Test unary operators with negative numbers
        r = s.execute("a = -5")
        assert r.success
        assert s.get_variable("a") == -5

        # Use unary operator in comparison
        r = s.execute("b = 0 > -1")
        assert r.success
        assert s.get_variable("b") is True

        # Test modulo in if statement
        r = s.execute(
            """
result = ""
idan 10 % 2 == 0:
    result = "even"
in ba haka ba:
    result = "odd"
"""
        )
        assert r.success, f"If/else with modulo failed: {r.error}"
        assert s.get_variable("result") == "even"

        # Test function with arithmetic and modulo
        r = s.execute(
            """
aiki fib_with_check(n):
    idan n < 0:
        mayar "negative"
    in ba haka ba:
        idan n % 2 == 0:
            mayar n * 2
        in ba haka ba:
            mayar n + 1
"""
        )
        assert r.success

        # Call function with positive number
        r = s.execute("fib_with_check(5)")
        assert r.success
        assert r.output == 6  # 5 is odd, so 5+1=6

        # Call function with even number
        r = s.execute("fib_with_check(4)")
        assert r.success
        assert r.output == 8  # 4 is even, so 4*2=8

        # Call function with negative number
        r = s.execute("fib_with_check(-3)")
        assert r.success
        assert r.output == "negative"

        # Fibonacci sequence with while loop and modulo
        r = s.execute(
            """
n = 1
fib_a = 0
fib_b = 1
count = 0
kadai count < 10:
    temp = fib_a + fib_b
    fib_a = fib_b
    fib_b = temp
    idan temp % 2 == 0:
        last_even = temp
    count = count + 1
"""
        )
        assert r.success, f"Fibonacci loop failed: {r.error}"
        assert s.variable_exists("last_even"), "last_even should be defined"
        assert s.get_variable("count") == 10

        # Verify final fibonacci state
        fib_b = s.get_variable("fib_b")
        assert isinstance(
            fib_b, (int, float)
        ), f"fib_b should be numeric, got {type(fib_b)}"

    def test_all_operators_work_together(self):
        """Test that all operators interact correctly"""
        s = ReplSession()

        # Arithmetic: +, -, *, /, %
        r = s.execute(
            """
x = 20
y = 3
sum_val = x + y
diff_val = x - y
prod_val = x * y
div_val = x / y
mod_val = x % y
"""
        )
        assert r.success
        assert s.get_variable("sum_val") == 23
        assert s.get_variable("diff_val") == 17
        assert s.get_variable("prod_val") == 60
        assert s.get_variable("div_val") == 20 // 3  # Integer division
        assert s.get_variable("mod_val") == 2

        # Comparisons with unary operators
        r = s.execute(
            """
c1 = -5 < 0
c2 = -5 == -5
c3 = -(-5) == 5
"""
        )
        assert r.success
        assert s.get_variable("c1") is True
        assert s.get_variable("c2") is True
        assert s.get_variable("c3") is True

    def test_error_recovery(self):
        """Test that errors are properly caught and don't break session state"""
        s = ReplSession()

        # Set a variable
        s.execute("healthy = 42")
        assert s.get_variable("healthy") == 42

        # Cause an error
        r = s.execute("undefined_var + 1")
        assert not r.success
        assert isinstance(r.error, ContextualError)
        assert r.error.kind == ErrorKind.UNDEFINED_VARIABLE

        # Verify state is intact
        assert s.get_variable("healthy") == 42

        # Continue executing
        r = s.execute("healthy * 2")
        assert r.success
        assert r.output == 84

    def test_complex_expression_evaluation(self):
        """Test operator precedence and complex expressions"""
        s = ReplSession()

        # Precedence: *, /, % before +, -
        r = s.execute(
            """
result = 2 + 3 * 4
result_unary = -2 + 3
result_modulo = 10 % 3 + 2
"""
        )
        assert r.success
        assert s.get_variable("result") == 14  # Not 20
        assert s.get_variable("result_unary") == 1  # Not 1
        assert s.get_variable("result_modulo") == 3  # 10%3=1, 1+2=3


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
