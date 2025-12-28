"""Beginner Level Tests for Hausalang v1.1 REPL

Tests focus on:
- Basic variable assignment
- Simple arithmetic
- Print statements
- Basic error handling
"""

from hausalang.repl.session import ReplSession
from hausalang.core.errors import ContextualError, ErrorKind


class TestBeginnerVariables:
    """Basic variable operations"""

    def test_assign_number(self):
        """Assign and retrieve a number"""
        s = ReplSession()
        s.execute("x = 5")
        assert s.get_variable("x") == 5

    def test_assign_string(self):
        """Assign and retrieve a string"""
        s = ReplSession()
        s.execute('name = "Ali"')
        assert s.get_variable("name") == "Ali"

    def test_reassign_variable(self):
        """Reassign a variable to a new value"""
        s = ReplSession()
        s.execute("count = 1")
        s.execute("count = 10")
        assert s.get_variable("count") == 10


class TestBeginnerArithmetic:
    """Basic arithmetic operations"""

    def test_addition(self):
        """Test basic addition"""
        s = ReplSession()
        r = s.execute("2 + 3")
        assert r.success
        assert r.output == 5

    def test_subtraction(self):
        """Test basic subtraction"""
        s = ReplSession()
        r = s.execute("10 - 4")
        assert r.success
        assert r.output == 6

    def test_multiplication(self):
        """Test basic multiplication"""
        s = ReplSession()
        r = s.execute("3 * 4")
        assert r.success
        assert r.output == 12

    def test_division(self):
        """Test basic division (integer division for ints)"""
        s = ReplSession()
        r = s.execute("10 / 2")
        assert r.success
        assert r.output == 5


class TestBeginnerComparisons:
    """Basic comparison operations"""

    def test_equal_numbers(self):
        """Test equality comparison"""
        s = ReplSession()
        r = s.execute("5 == 5")
        assert r.success
        assert r.output is True

    def test_not_equal_numbers(self):
        """Test inequality"""
        s = ReplSession()
        r = s.execute("5 != 3")
        assert r.success
        assert r.output is True

    def test_greater_than(self):
        """Test greater-than comparison"""
        s = ReplSession()
        r = s.execute("10 > 5")
        assert r.success
        assert r.output is True


class TestBeginnerErrors:
    """Basic error detection"""

    def test_undefined_variable_error(self):
        """Undefined variable raises ContextualError"""
        s = ReplSession()
        r = s.execute("x + 1")
        assert not r.success
        assert isinstance(r.error, ContextualError)
        assert r.error.kind == ErrorKind.UNDEFINED_VARIABLE

    def test_undefined_function_error(self):
        """Undefined function raises ContextualError"""
        s = ReplSession()
        r = s.execute("greet()")
        assert not r.success
        assert isinstance(r.error, ContextualError)
        assert r.error.kind == ErrorKind.UNDEFINED_FUNCTION

    def test_zero_division_error(self):
        """Division by zero raises ContextualError"""
        s = ReplSession()
        r = s.execute("5 / 0")
        assert not r.success
        assert isinstance(r.error, ContextualError)
        assert r.error.kind == ErrorKind.DIVISION_BY_ZERO
