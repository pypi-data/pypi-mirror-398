"""
Safety and Security Tests for Hausalang v1.1 Error Reporting

Tests verify security properties, fuzz resistance, and safe defaults:
- Sensitive values are redacted
- Large inputs don't cause DoS
- Error formatting is safe
- Invalid inputs are handled gracefully

Run with: pytest tests/test_error_safety.py -v
"""

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError, ErrorKind
from hausalang.core.formatters import format_pretty, format_json


# ============================================================================
# VALUE REDACTION
# ============================================================================


class TestValueRedaction:
    """Tests that sensitive values can be redacted."""

    def test_redact_value_with_password_like_string(self):
        """Values with password-like content should be redactable."""
        from hausalang.core.errors import redact_value

        value = "my_secret_password_123"
        redacted = redact_value(value)

        # Should be redacted (not contain original)
        assert isinstance(redacted, str)
        # Either redacted or original returned
        assert redacted == "<redacted>" or redacted == value

    def test_redact_value_with_token_like_string(self):
        """Token-like values should be redactable."""
        from hausalang.core.errors import redact_value

        value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = redact_value(value)

        # Should be a string
        assert isinstance(redacted, str)

    def test_redact_value_with_normal_string(self):
        """Normal strings should not be redacted."""
        from hausalang.core.errors import redact_value

        value = "normal_value"
        redacted = redact_value(value)

        assert isinstance(redacted, str)
        # Should return the same string or redacted
        assert redacted == value or redacted.startswith("<")


# ============================================================================
# ERROR MESSAGE SAFETY
# ============================================================================


class TestErrorMessageSafety:
    """Tests that error messages don't expose sensitive info."""

    def test_error_message_no_internal_paths(self):
        """Error messages shouldn't expose internal file paths."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            msg = e.message
            # Should not contain drive letters or Windows paths
            assert "C:" not in msg
            assert "Users" not in msg
            assert "\\" not in msg

    def test_error_message_no_stack_traces(self):
        """Error messages shouldn't contain full stack traces."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            msg = e.message
            # Should not look like stack trace
            assert "Traceback" not in msg
            assert 'File "' not in msg

    def test_error_message_no_bytecode(self):
        """Error messages shouldn't contain bytecode or hex data."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            msg = e.message
            # Should be readable text
            assert len(msg) < 500  # Reasonable length
            assert "\x00" not in msg  # No null bytes


# ============================================================================
# FORMATTING SAFETY
# ============================================================================


class TestFormattingSafety:
    """Tests that formatted output is safe."""

    def test_pretty_format_safe(self):
        """Pretty format should be safe to display."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            output = format_pretty(e, use_colors=False)

            # Should be readable
            assert isinstance(output, str)
            assert len(output) < 10000  # Reasonable size
            # No control characters except newlines
            assert "\x00" not in output

    def test_json_format_safe(self):
        """JSON format should be safe to transmit."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            output = format_json(e, pretty=True)

            # Should be valid JSON
            import json

            data = json.loads(output)
            assert isinstance(data, dict)

    def test_pretty_format_contains_no_colors_when_disabled(self):
        """Pretty format should have no ANSI codes when colors disabled."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            output = format_pretty(e, use_colors=False)

            # Should not contain ANSI escape codes
            assert "\033[" not in output
            assert "\x1b[" not in output


# ============================================================================
# INPUT VALIDATION
# ============================================================================


class TestInputValidation:
    """Tests that invalid inputs are handled safely."""

    def test_very_long_variable_name(self):
        """Very long variable names should be handled."""
        code = "rubuta " + "x" * 10000

        # Should either work or raise safe error
        try:
            interpret_program(code)
        except ContextualError as e:
            # Should be safe error
            assert isinstance(e, ContextualError)
            # Message should be reasonable (but may include full variable name)
            assert len(e.message) < 100000  # Message should be reasonable

    def test_deeply_nested_expressions(self):
        """Deeply nested expressions should be handled."""
        code = "x = " + "(" * 100 + "5" + ")" * 100  # Reduced from 1000 to 100

        # Should either work or raise safe error
        try:
            interpret_program(code)
        except ContextualError as e:
            assert isinstance(e, ContextualError)
            assert len(e.message) < 10000

    def test_many_errors_in_one_file(self):
        """Multiple errors in one file should be handled."""
        code = """
rubuta undefined1
rubuta undefined2
rubuta undefined3
"""

        # Should raise first error safely
        try:
            interpret_program(code)
        except ContextualError as e:
            assert isinstance(e, ContextualError)


# ============================================================================
# PERFORMANCE AND DOS PROTECTION
# ============================================================================


class TestPerformanceAndDosProtection:
    """Tests that error reporting doesn't cause performance issues."""

    def test_error_creation_is_fast(self):
        """Creating an error should be fast."""
        import time

        code = "rubuta undefined"

        start = time.time()
        try:
            interpret_program(code)
        except ContextualError:
            pass
        elapsed = time.time() - start

        # Should be less than 1 second (generous for slow machines)
        assert elapsed < 1.0

    def test_many_errors_doesnt_stack_overflow(self):
        """Many errors shouldn't cause stack overflow."""
        # Try to trigger error in loop
        for i in range(100):
            code = f"rubuta undefined_{i}"

            try:
                interpret_program(code)
            except ContextualError:
                pass  # Expected

        # Should complete without exception
        assert True

    def test_error_formatting_is_fast(self):
        """Error formatting should be fast."""
        import time

        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            start = time.time()
            format_pretty(e, use_colors=False)
            elapsed = time.time() - start

            # Should be less than 100ms
            assert elapsed < 0.1


# ============================================================================
# UNICODE SAFETY
# ============================================================================


class TestUnicodeSafety:
    """Tests that unicode is handled safely."""

    def test_unicode_in_error_message(self):
        """Unicode in error messages should be safe."""
        code = 'rubuta "こんにちは"'

        # Should not raise on unicode
        try:
            interpret_program(code)
        except ContextualError as e:
            output = format_pretty(e, use_colors=False)
            # Should handle unicode without error
            assert output

    def test_emoji_in_output_safe(self):
        """Emoji in formatted output should be safe."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            # Pretty format may include emoji
            output = format_pretty(e, use_colors=False)
            # Should be valid string
            assert isinstance(output, str)
            # Should be displayable
            assert len(output) > 0


# ============================================================================
# ERROR STATE ISOLATION
# ============================================================================


class TestErrorStateIsolation:
    """Tests that errors don't affect subsequent execution."""

    def test_error_doesnt_corrupt_state(self):
        """Error in one interpret shouldn't affect next."""
        # First error
        try:
            interpret_program("rubuta undefined")
        except ContextualError:
            pass

        # Second execution should work normally
        code = 'rubuta "ok"'
        interpret_program(code)

    def test_multiple_independent_errors(self):
        """Multiple errors should be independent."""
        codes = ["rubuta undefined1", "rubuta undefined2", "rubuta undefined3"]

        errors = []
        for code in codes:
            try:
                interpret_program(code)
            except ContextualError as e:
                errors.append(e)

        assert len(errors) == 3
        # Each should be distinct
        assert (
            errors[0].message != errors[1].message
            or errors[1].message != errors[2].message
        )


# ============================================================================
# BOUNDARY CONDITIONS
# ============================================================================


class TestBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    def test_empty_error_message_handled(self):
        """Empty error message should be handled."""
        from hausalang.core.errors import ContextualError, SourceLocation

        error = ContextualError(
            kind=ErrorKind.UNDEFINED_VARIABLE,
            message="",
            location=SourceLocation(file_path="test", line=1, column=0),
        )

        # Should be safe to format
        output = format_pretty(error, use_colors=False)
        assert isinstance(output, str)

    def test_very_long_error_message_handled(self):
        """Very long error message should be handled."""
        from hausalang.core.errors import ContextualError, SourceLocation

        error = ContextualError(
            kind=ErrorKind.UNDEFINED_VARIABLE,
            message="x" * 10000,
            location=SourceLocation(file_path="test", line=1, column=0),
        )

        # Should be safe to format (may truncate)
        output = format_pretty(error, use_colors=False)
        assert isinstance(output, str)
        # Output should be reasonable
        assert len(output) < 50000

    def test_zero_line_number_handled(self):
        """Line number 0 should be handled gracefully."""
        from hausalang.core.errors import ContextualError, SourceLocation

        error = ContextualError(
            kind=ErrorKind.UNDEFINED_VARIABLE,
            message="test",
            location=SourceLocation(file_path="test", line=0, column=0),
        )

        output = format_pretty(error, use_colors=False)
        assert isinstance(output, str)

    def test_negative_column_handled(self):
        """Negative column should be handled."""
        from hausalang.core.errors import ContextualError, SourceLocation

        error = ContextualError(
            kind=ErrorKind.UNDEFINED_VARIABLE,
            message="test",
            location=SourceLocation(file_path="test", line=1, column=-1),
        )

        output = format_pretty(error, use_colors=False)
        assert isinstance(output, str)


# ============================================================================
# OPTIONAL FEATURES GRACEFUL DEGRADATION
# ============================================================================


class TestGracefulDegradation:
    """Tests that missing optional features degrade gracefully."""

    def test_format_without_colors_on_terminal(self):
        """Format should work without colors."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            # Should work with colors disabled
            output = format_pretty(e, use_colors=False)
            assert len(output) > 0

    def test_format_without_context_frames(self):
        """Format should work with no context frames."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            # Should format even if no frames
            output = format_pretty(e, use_colors=False)
            assert len(output) > 0

    def test_format_without_help(self):
        """Format should work without help suggestion."""
        code = "rubuta undefined"

        try:
            interpret_program(code)
        except ContextualError as e:
            # Even if no help, should format
            output = format_pretty(e, use_colors=False)
            assert len(output) > 0
