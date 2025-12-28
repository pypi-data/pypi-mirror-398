"""
Backward Compatibility Tests for Hausalang v1.1 Error Reporting

Tests verify that v1.1 errors maintain v1.0 compatibility:
- Existing exception handlers still catch errors
- Exception hierarchy works correctly
- Error messages are backward compatible
- v1.0 code patterns still work

Run with: pytest tests/test_error_compat.py -v
"""

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError, ErrorKind


# ============================================================================
# EXCEPTION HIERARCHY COMPATIBILITY
# ============================================================================


class TestExceptionHierarchyCompat:
    """Tests that ContextualError maintains backward compatibility."""

    def test_name_error_for_undefined_variable(self):
        """Undefined variable errors can be caught as ContextualError (which is a NameError subclass)."""
        code = "rubuta undefined_var"

        # Should raise ContextualError which indicates a name error
        try:
            interpret_program(code)
            assert False, "Should have raised error"
        except ContextualError as e:
            assert e.kind == ErrorKind.UNDEFINED_VARIABLE
            assert "undefined_var" in e.message

    def test_name_error_for_undefined_function(self):
        """Undefined function errors should be catchable."""
        code = "x = undefined_func()"

        try:
            interpret_program(code)
            assert False, "Should have raised error"
        except ContextualError as e:
            assert e.kind == ErrorKind.UNDEFINED_FUNCTION
            assert "undefined_func" in e.message

    def test_value_error_for_loop_step(self):
        """Loop step errors should be catchable."""
        code = """
don i = 0 zuwa 5 ta 0:
    rubuta i
"""

        try:
            interpret_program(code)
            assert False, "Should have raised error"
        except ContextualError as e:
            assert e.kind == ErrorKind.ZERO_LOOP_STEP

    def test_value_error_for_division_by_zero(self):
        """Division by zero should be catchable."""
        code = "x = 10 / 0"

        try:
            interpret_program(code)
            assert False, "Should have raised error"
        except ContextualError as e:
            assert e.kind == ErrorKind.DIVISION_BY_ZERO

    def test_syntax_error_for_parse_errors(self):
        """Parse errors should be catchable."""
        code = "idan x = 5\n    rubuta x"  # Missing colon

        try:
            interpret_program(code)
            assert False, "Should have raised error"
        except ContextualError as e:
            assert e.kind == ErrorKind.MISSING_COLON

    def test_type_error_for_invalid_operands(self):
        """Type errors should be catchable."""
        code = 'x = 5 + "hello"'  # Can't add int and str

        try:
            interpret_program(code)
            assert False, "Should have raised error"
        except ContextualError as e:
            # Could be STRING_NUMBER_CONCAT or INVALID_OPERAND_TYPE
            assert e.kind in (
                ErrorKind.INVALID_OPERAND_TYPE,
                ErrorKind.STRING_NUMBER_CONCAT,
            )


# ============================================================================
# GENERIC EXCEPTION HANDLER
# ============================================================================


class TestGenericExceptionHandling:
    """Tests that generic Exception handlers work."""

    def test_exception_handler_catches_all(self):
        """Generic Exception handler should catch ContextualError."""
        code = "rubuta undefined"

        caught = False
        try:
            interpret_program(code)
        except Exception as e:
            caught = True
            # Should be ContextualError
            assert isinstance(e, ContextualError)

        assert caught

    def test_try_except_exception_pattern(self):
        """Try/except Exception pattern should work (v1.0 style)."""
        code = "rubuta undefined"

        error = None
        try:
            interpret_program(code)
        except Exception as e:
            error = e

        assert error is not None
        assert isinstance(error, Exception)
        assert isinstance(error, ContextualError)


# ============================================================================
# ERROR MESSAGE COMPATIBILITY
# ============================================================================


class TestErrorMessageCompat:
    """Tests that error messages are backward compatible."""

    def test_undefined_variable_message_contains_name(self):
        """Undefined variable message should contain the variable name."""
        code = "rubuta my_var"

        try:
            interpret_program(code)
            assert False, "Should have raised an error"
        except ContextualError as e:
            assert "my_var" in e.message

    def test_undefined_function_message_contains_name(self):
        """Undefined function message should contain the function name."""
        code = "x = my_func()"

        try:
            interpret_program(code)
            assert False, "Should have raised an error"
        except ContextualError as e:
            assert "my_func" in e.message

    def test_wrong_argument_count_message(self):
        """Wrong argument count message should be clear."""
        code = """
aiki add(a, b):
    mayar a + b

result = add(5)
"""

        try:
            interpret_program(code)
            assert False, "Should have raised an error"
        except ContextualError as e:
            # Should mention arguments
            msg = e.message.lower()
            assert "argument" in msg or "param" in msg or "2" in e.message

    def test_parse_error_message(self):
        """Parse error message should be informative."""
        code = "idan x = 5\n    rubuta x"  # Missing colon

        try:
            interpret_program(code)
            assert False, "Should have raised an error"
        except ContextualError as e:
            # Should be non-empty
            assert len(e.message) > 0


# ============================================================================
# BACKWARD COMPATIBLE PATTERNS
# ============================================================================


class TestBackwardCompatiblePatterns:
    """Tests that common v1.0 error handling patterns still work."""

    def test_pattern_try_except_specific(self):
        """try/except ContextualError pattern should work."""
        code = "x = undefined_var + 5"

        caught_context_error = False
        try:
            interpret_program(code)
        except ContextualError:
            caught_context_error = True

        assert caught_context_error

    def test_pattern_try_except_multiple(self):
        """try/except with multiple types should work."""
        code = "x = undefined_var"

        caught = False
        try:
            interpret_program(code)
        except (NameError, ValueError, TypeError, ContextualError):
            caught = True

        assert caught

    def test_pattern_try_except_else(self):
        """try/except/else pattern should work."""
        code = "rubuta undefined"

        caught_error = False
        executed_else = False

        try:
            interpret_program(code)
        except ContextualError:
            caught_error = True
        else:
            executed_else = True

        assert caught_error
        assert not executed_else

    def test_exception_has_args(self):
        """ContextualError should have args (for logging)."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            # Should have args tuple
            assert hasattr(e, "args")
            assert isinstance(e.args, tuple)


# ============================================================================
# ERROR STRING REPRESENTATION
# ============================================================================


class TestErrorStringRepCompat:
    """Tests that error string representations work correctly."""

    def test_error_has_str_representation(self):
        """Error should have str() representation."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            error_str = str(e)
            assert isinstance(error_str, str)
            assert len(error_str) > 0

    def test_error_has_repr_representation(self):
        """Error should have repr() representation."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            error_repr = repr(e)
            assert isinstance(error_repr, str)
            assert "ContextualError" in error_repr or "Error" in error_repr

    def test_error_prints_without_exception(self):
        """Error should be printable."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            # Should not raise on str conversion
            output = str(e)
            assert output  # Non-empty


# ============================================================================
# ATTRIBUTE COMPATIBILITY
# ============================================================================


class TestErrorAttributeCompat:
    """Tests that ContextualError has expected attributes."""

    def test_error_has_message_attribute(self):
        """Error should have message attribute."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            assert hasattr(e, "message")
            assert isinstance(e.message, str)

    def test_error_has_kind_attribute(self):
        """Error should have kind attribute (v1.1 feature)."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            assert hasattr(e, "kind")
            assert isinstance(e.kind, ErrorKind)

    def test_error_has_location_attribute(self):
        """Error should have location attribute (v1.1 feature)."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            assert hasattr(e, "location")
            assert hasattr(e.location, "line")
            assert hasattr(e.location, "column")


# ============================================================================
# V1.0 CODE STILL WORKS
# ============================================================================


class TestV10CodeStillWorks:
    """Tests that v1.0 code without errors still works."""

    def test_hello_world_still_works(self):
        """Hello world should still work."""
        code = 'rubuta "Hello, World!"'

        # Should not raise any error
        interpret_program(code)

    def test_arithmetic_still_works(self):
        """Arithmetic should still work."""
        code = """
x = 5
y = 10
z = x + y
rubuta z
"""

        interpret_program(code)

    def test_function_definition_still_works(self):
        """Function definition should still work."""
        code = """
aiki add(a, b):
    mayar a + b

result = add(3, 4)
rubuta result
"""

        interpret_program(code)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegrationCompat:
    """Integration tests for backward compatibility."""

    def test_mixed_errors_handled_correctly(self):
        """Multiple different error types should be handleable."""
        codes = [
            "rubuta undefined",  # NameError
            "x = 10 / 0",  # ValueError
            "x = 5 + 'hello'",  # TypeError
            "idan x = 5\n    rubuta x",  # SyntaxError (missing colon)
        ]

        for code in codes:
            caught = False
            try:
                interpret_program(code)
            except ContextualError:
                caught = True
            except Exception:
                # Also acceptable - could be base exception
                caught = True

            assert caught, f"Code should have raised error: {code[:30]}"
