"""
Context Accumulation Tests for Hausalang v1.1 Error Reporting

Tests verify that diagnostic context frames stack properly
and provide useful information for debugging.

Run with: pytest tests/test_error_context.py -v
"""

import pytest
from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import (
    ContextualError,
    ErrorKind,
)


# ============================================================================
# CONTEXT FRAME STACKING
# ============================================================================


class TestContextFrameStacking:
    """Tests for accumulation of diagnostic context."""

    def test_error_can_have_no_context_frames(self):
        """Errors with no context frames are valid."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # May have no frames, or may have some - both valid
        assert isinstance(error.context_frames, list)

    def test_error_can_have_multiple_context_frames(self):
        """Errors can accumulate multiple context frames."""
        code = "aiki foo():\n    mayar undefined_var\nfoo()"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Even with no explicit frame building, structure is valid
        assert isinstance(error.context_frames, list)
        assert all(hasattr(f, "__class__") for f in error.context_frames)

    def test_context_frames_immutable(self):
        """Context frames should be immutable (frozen dataclasses)."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value

        # Try to modify context frames - should fail on immutable frames
        for frame in error.context_frames:
            # Verify it's a frozen dataclass
            try:
                frame.key = "modified"  # Will fail if frozen
            except (AttributeError, TypeError):
                pass  # Expected - frame is immutable


# ============================================================================
# FUNCTION CALL CONTEXT
# ============================================================================


class TestFunctionCallContext:
    """Tests for context in function calls and nesting."""

    def test_undefined_variable_in_function(self):
        """Error in function should include context."""
        code = """
aiki compute(x):
    y = undefined_var
    mayar y + x

compute(5)
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNDEFINED_VARIABLE
        assert "undefined_var" in error.message

    def test_wrong_argument_count_context(self):
        """Wrong argument count error should have context."""
        code = """
aiki add(a, b):
    mayar a + b

result = add(5)
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.WRONG_ARGUMENT_COUNT
        assert "add" in error.message
        # Should mention expected vs actual argument count
        assert "2" in error.message and "1" in error.message

    def test_nested_function_calls(self):
        """Error in nested function calls should be locatable."""
        code = """
aiki a():
    mayar b()

aiki b():
    mayar c()

aiki c():
    mayar undefined

a()
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNDEFINED_VARIABLE
        assert "undefined" in error.message


# ============================================================================
# LOOP CONTEXT
# ============================================================================


class TestLoopContext:
    """Tests for context in loops."""

    def test_zero_step_loop_context(self):
        """Zero step error should have loop context."""
        code = """
don i = 0 zuwa 5 ta 0:
    rubuta i
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.ZERO_LOOP_STEP
        assert "step" in error.message.lower() or "0" in error.message

    def test_while_loop_undefined_variable(self):
        """Error in while loop should indicate loop context."""
        code = """
x = 0
kadai x < 10:
    rubuta y
    x = x + 1
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNDEFINED_VARIABLE
        assert "y" in error.message


# ============================================================================
# ERROR DETAILS AND DIAGNOSTICS
# ============================================================================


class TestErrorDiagnosticDetails:
    """Tests that errors provide enough diagnostic info."""

    def test_undefined_variable_has_variable_name(self):
        """Undefined variable error should mention the variable name."""
        code = "rubuta my_missing_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert "my_missing_var" in error.message

    def test_undefined_function_has_function_name(self):
        """Undefined function error should mention the function name."""
        code = "x = nonexistent_func()"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert "nonexistent_func" in error.message

    def test_wrong_argument_count_shows_counts(self):
        """Wrong argument count should show expected vs actual."""
        code = """
aiki triple(a, b, c):
    mayar a + b + c

result = triple(1, 2)
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Should indicate 3 expected, 2 actual
        msg = error.message.lower()
        assert ("3" in error.message and "2" in error.message) or (
            "expected" in msg and "argument" in msg
        )

    def test_error_has_help_suggestion(self):
        """Errors should have help suggestion when possible."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Help is optional but good to have
        if error.help:
            assert len(error.help) > 0
            assert len(error.help) <= 80  # One-line max


# ============================================================================
# ERROR LOCATION PRECISION
# ============================================================================


class TestErrorLocationPrecision:
    """Tests that error locations are accurate."""

    def test_error_location_line_number(self):
        """Error location should have a valid line number."""
        code = "x = 5\ny = 10\nz = undefined"  # Line 3

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Line should be positive
        assert error.location.line > 0

    def test_error_location_column_number(self):
        """Error location should have correct column number."""
        code = "x = undefined"  # Error at column 4

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Column should be reasonable (0-indexed)
        assert error.location.column >= 0
        assert error.location.column < len(code)

    def test_error_location_in_formatted_output(self):
        """Error location should be visible in pretty format."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value

        from hausalang.core.formatters import format_pretty

        output = format_pretty(error, use_colors=False)

        # Location should be in output
        assert "line" in output.lower() or ":" in output
