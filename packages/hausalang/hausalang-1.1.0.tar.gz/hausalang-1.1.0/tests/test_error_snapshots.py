"""
Golden Snapshot Tests for Hausalang v1.1 Error Reporting

Tests verify that error output format is consistent and readable.
Snapshots are golden outputs that should be reviewed manually.

Run with: pytest tests/test_error_snapshots.py -v
"""

import pytest
from hausalang.core.interpreter import interpret_program
from hausalang.core.lexer import tokenize_program
from hausalang.core.errors import ContextualError, ErrorKind
from hausalang.core.formatters import format_pretty


# ============================================================================
# LEXICAL ERROR SNAPSHOTS
# ============================================================================


class TestLexerErrorSnapshots:
    """Golden output tests for lexer errors."""

    def test_unknown_symbol(self):
        """Unknown symbol error format and message."""
        code = "x = 5 @ y"

        with pytest.raises(ContextualError) as exc_info:
            tokenize_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNKNOWN_SYMBOL
        assert "@" in error.message
        assert error.location.line == 1
        assert error.location.column == 6

        # Verify error can be pretty-printed
        output = format_pretty(error, use_colors=False)
        assert "UNKNOWN_SYMBOL" in output
        assert "@" in output

    def test_unclosed_string(self):
        """Unclosed string literal error."""
        code = 'x = "hello'

        with pytest.raises(ContextualError) as exc_info:
            tokenize_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNCLOSED_STRING
        assert "hello" in error.message or "string" in error.message.lower()

        output = format_pretty(error, use_colors=False)
        assert "UNCLOSED_STRING" in output

    def test_invalid_number(self):
        """Invalid number format error."""
        code = "x = 1.2.3"

        with pytest.raises(ContextualError) as exc_info:
            tokenize_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.INVALID_NUMBER

        output = format_pretty(error, use_colors=False)
        assert "INVALID_NUMBER" in output

    def test_invalid_indent(self):
        """Indentation not multiple of 4 spaces."""
        code = "x = 5\n  y = 10"  # 2 spaces instead of 4

        with pytest.raises(ContextualError) as exc_info:
            tokenize_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.INVALID_INDENT

        output = format_pretty(error, use_colors=False)
        assert "INVALID_INDENT" in output


# ============================================================================
# PARSER ERROR SNAPSHOTS
# ============================================================================


class TestParserErrorSnapshots:
    """Golden output tests for parser errors."""

    def test_missing_colon_after_if(self):
        """Missing colon after if condition."""
        code = "idan x > 5\n    rubuta x"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.MISSING_COLON

        output = format_pretty(error, use_colors=False)
        assert "MISSING_COLON" in output
        assert ":" in output  # Hint about colon

    def test_missing_colon_after_aiki(self):
        """Missing colon after function signature."""
        code = "aiki foo(x)\n    rubuta x"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.MISSING_COLON

    def test_unmatched_paren(self):
        """Unmatched parenthesis."""
        code = "aiki foo(x\n    rubuta x"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind in [ErrorKind.UNMATCHED_PAREN, ErrorKind.UNEXPECTED_EOF]

        output = format_pretty(error, use_colors=False)
        assert error.kind.name in output

    def test_unexpected_token(self):
        """Unexpected token in expression."""
        code = "x = @ y"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Could be from lexer (UNKNOWN_SYMBOL) or parser (UNEXPECTED_TOKEN)
        assert error.kind in [ErrorKind.UNKNOWN_SYMBOL, ErrorKind.UNEXPECTED_TOKEN]

    def test_missing_indent(self):
        """Missing indentation after colon."""
        code = "idan x > 5:\nrubuta x"  # No indent on line 2

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Could fail at lexer or parser depending on structure
        assert error.kind in [
            ErrorKind.MISSING_INDENT,
            ErrorKind.UNEXPECTED_TOKEN,
            ErrorKind.UNEXPECTED_EOF,
        ]


# ============================================================================
# RUNTIME ERROR SNAPSHOTS
# ============================================================================


class TestInterpreterErrorSnapshots:
    """Golden output tests for runtime errors."""

    def test_undefined_variable(self):
        """Undefined variable error."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNDEFINED_VARIABLE
        assert "undefined_var" in error.message

        output = format_pretty(error, use_colors=False)
        assert "UNDEFINED_VARIABLE" in output
        assert "undefined_var" in output

    def test_undefined_function(self):
        """Undefined function error."""
        code = "x = undefined_func(5)"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.UNDEFINED_FUNCTION
        assert "undefined_func" in error.message

        output = format_pretty(error, use_colors=False)
        assert "UNDEFINED_FUNCTION" in output

    def test_wrong_argument_count(self):
        """Function called with wrong number of arguments."""
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

        output = format_pretty(error, use_colors=False)
        assert "WRONG_ARGUMENT_COUNT" in output

    def test_division_by_zero(self):
        """Division by zero error."""
        code = "x = 10 / 0"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.DIVISION_BY_ZERO

        output = format_pretty(error, use_colors=False)
        assert "DIVISION_BY_ZERO" in output

    def test_zero_loop_step(self):
        """For loop step cannot be zero."""
        code = """
don i = 0 zuwa 10 ta 0:
    rubuta i
"""

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.kind == ErrorKind.ZERO_LOOP_STEP

        output = format_pretty(error, use_colors=False)
        assert "ZERO_LOOP_STEP" in output

    def test_string_number_concat(self):
        """String and number concatenation error."""
        code = 'x = "hello" + 5'

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        # Could be INVALID_OPERAND_TYPE or similar
        assert error.kind in [
            ErrorKind.INVALID_OPERAND_TYPE,
            ErrorKind.STRING_NUMBER_CONCAT,
        ]

        output = format_pretty(error, use_colors=False)
        assert error.kind.name in output


# ============================================================================
# ERROR OUTPUT PROPERTIES
# ============================================================================


class TestErrorOutputProperties:
    """Tests for error output consistency and required properties."""

    def test_all_errors_have_kind(self):
        """All errors must have an ErrorKind."""
        codes = [
            "x = 5 @ y",  # UNKNOWN_SYMBOL
            'x = "unclosed',  # UNCLOSED_STRING
            "rubuta undefined",  # UNDEFINED_VARIABLE
            "x = 10 / 0",  # DIVISION_BY_ZERO
        ]

        for code in codes:
            with pytest.raises(ContextualError) as exc_info:
                interpret_program(code)

            error = exc_info.value
            assert error.kind is not None
            assert isinstance(error.kind, ErrorKind)

    def test_all_errors_have_location(self):
        """All errors must have a location (file, line, column)."""
        codes = [
            "x = 5 @ y",
            'x = "unclosed',
            "rubuta undefined",
        ]

        for code in codes:
            with pytest.raises(ContextualError) as exc_info:
                interpret_program(code)

            error = exc_info.value
            assert error.location is not None
            assert error.location.line > 0
            assert error.location.column >= 0

    def test_all_errors_have_message(self):
        """All errors must have a human-readable message."""
        codes = [
            "x = 5 @ y",
            "rubuta undefined",
            "x = 10 / 0",
        ]

        for code in codes:
            with pytest.raises(ContextualError) as exc_info:
                interpret_program(code)

            error = exc_info.value
            assert error.message is not None
            assert len(error.message) > 0
            assert len(error.message) <= 500

    def test_error_pretty_format_includes_all_components(self):
        """Pretty format should include kind, location, message, help if available."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        output = format_pretty(error, use_colors=False)

        # Should contain kind name
        assert error.kind.name in output

        # Should contain message
        assert error.message in output

        # Should contain location info
        assert "line" in output.lower()
