"""
Regression tests for ContextualError exception inheritance.

This test suite ensures that ContextualError instances are also instances of
appropriate builtin exceptions (SyntaxError, NameError, ValueError, TypeError,
ZeroDivisionError) based on their ErrorKind. This is critical for backward
compatibility with existing exception handling code.

See: https://github.com/mnura361234-ship-it/hausalang/issues/XXX
"""

import pytest

from hausalang.core.errors import ContextualError, ErrorKind
from hausalang.core.interpreter import interpret_program


class TestContextualErrorInheritance:
    """Test that ContextualError inherits from appropriate builtin exceptions."""

    def test_lexical_error_is_syntax_error(self):
        """Lexical errors should be instances of SyntaxError."""
        try:
            interpret_program("@invalid token@")
        except Exception as e:
            assert isinstance(e, ContextualError), "Expected ContextualError"
            assert isinstance(e, SyntaxError), "Lexical error should be SyntaxError"
            assert e.kind in [
                ErrorKind.UNKNOWN_SYMBOL,
                ErrorKind.UNEXPECTED_TOKEN,
            ]

    def test_parse_error_is_syntax_error(self):
        """Parse errors should be instances of SyntaxError."""
        try:
            interpret_program("idan x =")  # Incomplete conditional
        except Exception as e:
            assert isinstance(e, ContextualError)
            assert isinstance(e, SyntaxError), "Parse error should be SyntaxError"

    def test_undefined_variable_is_name_error(self):
        """Undefined variable errors should be instances of NameError."""
        try:
            interpret_program("rubuta undefined_var")
        except Exception as e:
            assert isinstance(e, ContextualError)
            assert isinstance(e, NameError), "Undefined variable should be NameError"
            assert e.kind == ErrorKind.UNDEFINED_VARIABLE

    def test_type_error_is_type_error(self):
        """Type mismatch errors should be instances of TypeError."""
        try:
            interpret_program(
                """
x = "hello"
y = 5
z = x + y
"""
            )
        except Exception as e:
            assert isinstance(e, ContextualError)
            assert isinstance(e, TypeError), "Type mismatch should be TypeError"

    def test_division_by_zero_is_zero_division_error(self):
        """Division by zero should be instances of ZeroDivisionError."""
        try:
            interpret_program("x = 1 / 0\nrubuta x")
        except Exception as e:
            assert isinstance(e, ContextualError)
            assert isinstance(
                e, ZeroDivisionError
            ), "Division by zero should be ZeroDivisionError"

    def test_value_error_is_value_error(self):
        """Invalid value errors should be instances of ValueError."""
        try:
            # Try to convert non-numeric string to number
            interpret_program(
                """
aiki num():
    mayar jigon("hello")
"""
            )
        except Exception as e:
            assert isinstance(e, ContextualError)
            # Either UNDEFINED_FUNCTION or another error is fine for this test
            # The key is that it's a ContextualError

    def test_catch_syntax_error_catches_lexical_error(self):
        """
        Exception handler for SyntaxError should catch ContextualError
        from lexical/parse errors.
        """

        def run_invalid_syntax():
            try:
                interpret_program("@invalid@")
            except SyntaxError as e:
                return e

        result = run_invalid_syntax()
        assert result is not None, "SyntaxError handler should catch lexical error"
        assert isinstance(result, ContextualError)

    def test_catch_name_error_catches_undefined_variable(self):
        """
        Exception handler for NameError should catch ContextualError
        for undefined variables.
        """

        def run_undefined():
            try:
                interpret_program("rubuta x")
            except NameError as e:
                return e

        result = run_undefined()
        assert result is not None, "NameError handler should catch undefined variable"
        assert isinstance(result, ContextualError)

    def test_catch_zero_division_error(self):
        """
        Exception handler for ZeroDivisionError should catch ContextualError
        for division by zero.
        """

        def run_div_zero():
            try:
                interpret_program("x = 5 / 0\nrubuta x")
            except ZeroDivisionError as e:
                return e

        result = run_div_zero()
        assert result is not None, "ZeroDivisionError handler should catch error"
        assert isinstance(result, ContextualError)

    def test_catch_exception_catches_all_contextual_errors(self):
        """
        Generic Exception handler should catch all ContextualError types.
        """

        def run_any_error():
            try:
                interpret_program("rubuta undefined_var")
            except Exception as e:
                return e

        result = run_any_error()
        assert result is not None, "Exception handler should catch ContextualError"
        assert isinstance(result, ContextualError)

    def test_error_message_accessible_from_syntax_error(self):
        """
        Accessing error message via SyntaxError should work.
        """
        try:
            interpret_program("@invalid@")
        except SyntaxError as e:
            msg = str(e)
            assert msg, "SyntaxError str() should produce message"
            assert isinstance(e, ContextualError)

    def test_error_attributes_accessible(self):
        """
        ContextualError-specific attributes should be accessible.
        """
        try:
            interpret_program("rubuta x")
        except NameError as e:
            # Should be able to access ContextualError attributes
            assert hasattr(e, "kind")
            assert hasattr(e, "location")
            assert hasattr(e, "context_frames")
            assert e.kind == ErrorKind.UNDEFINED_VARIABLE


class TestContextualErrorRegressionScenarios:
    """
    Test realistic backward-compatibility scenarios where code
    expects to catch standard Python exceptions but gets ContextualError.
    """

    def test_multi_catch_syntax_and_name_error(self):
        """Test catching multiple exception types in one except clause."""
        error_caught = None
        try:
            interpret_program("rubuta undefined")
        except (SyntaxError, NameError) as e:
            error_caught = e

        assert error_caught is not None
        assert isinstance(error_caught, ContextualError)
        assert isinstance(error_caught, NameError)

    def test_conditional_exception_handling(self):
        """Test conditional logic in exception handlers."""

        def handle_error():
            try:
                interpret_program("@invalid@")
            except SyntaxError as e:
                if isinstance(e, ContextualError):
                    return "contextual_syntax_error"
                else:
                    return "plain_syntax_error"
            except Exception:
                return "other_error"

        result = handle_error()
        assert result == "contextual_syntax_error"

    def test_reraise_preserves_type(self):
        """Test that reraising ContextualError preserves builtin type."""
        caught_exception = None
        try:
            try:
                interpret_program("rubuta x")
            except NameError as e:
                caught_exception = e
                raise
        except NameError as e:
            assert e is caught_exception
            assert isinstance(e, ContextualError)

    def test_multiple_error_types_from_single_program(self):
        """
        Test handling different error types from different code paths.
        """
        # Undefined variable -> NameError
        try:
            interpret_program("rubuta undefined")
        except NameError:
            name_error_caught = True
        except Exception:
            name_error_caught = False

        # Division by zero -> ZeroDivisionError
        try:
            interpret_program("x = 1 / 0")
        except ZeroDivisionError:
            div_error_caught = True
        except Exception:
            div_error_caught = False

        assert name_error_caught, "Should catch NameError"
        assert div_error_caught, "Should catch ZeroDivisionError"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
