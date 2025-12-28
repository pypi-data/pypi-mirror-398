"""
Error Formatting and Display for Hausalang v1.1

This module provides formatters for ContextualError instances.
Supports multiple output formats: human-readable, JSON, and compact machine.

Key Components:
  - ErrorFormatter: Main formatter class
  - pretty(): Human-readable console output (with optional colors)
  - json(): Machine-readable JSON output
  - machine(): Compact machine format

Design:
  - Colors optional and graceful (fallback if not available)
  - Multi-language prep (easy translation lookup)
  - Works with all error types (lexical, parse, runtime, infra, internal)
  - Context-aware (adapts based on error kind and audience)
"""

import json
from typing import List
from .errors import (
    ContextualError,
    ErrorKind,
    KvFrame,
    WithPathFrame,
    WithValueFrame,
    WithExpectedFrame,
    WithSuggestionFrame,
)


# ============================================================================
# Color Support (Optional, with Graceful Fallback)
# ============================================================================


class _ColorCodes:
    """ANSI color codes for terminal output (graceful fallback if not supported)."""

    # Colors
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    GRAY = "\033[90m"

    # Formatting
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text (gracefully handles non-TTY environments).

        Args:
            text: The text to colorize
            color: Color code (e.g., RED, BOLD)

        Returns:
            Colorized text (or plain text if colors not available)
        """
        # In a production environment, would check sys.stdout.isatty()
        # For now, always include colors (can be stripped by piping)
        return f"{color}{text}{cls.RESET}"


# ============================================================================
# Error Formatter
# ============================================================================


class ErrorFormatter:
    """Format ContextualError instances for different audiences.

    Supports:
      - pretty(): Human-readable console output
      - json(): Machine-readable JSON format
      - machine(): Compact single-line format

    Designed to be extensible for multi-language support (i18n).
    """

    def __init__(self, use_colors: bool = True, use_i18n: bool = False):
        """Initialize the formatter.

        Args:
            use_colors: Whether to use ANSI colors in output
            use_i18n: Whether to use i18n for messages (future feature)
        """
        self.use_colors = use_colors
        self.use_i18n = use_i18n

    # ========================================================================
    # Public Interface
    # ========================================================================

    def pretty(self, error: ContextualError) -> str:
        """Format error as human-readable multi-line output.

        Output includes:
          - Error kind and message
          - Location (file:line:column)
          - Context frames (diagnostic information)
          - Actionable help (if available)

        Example output:
            ❌ UNDEFINED_VARIABLE: Variable 'x' is not defined
               at program.ha on line 5, column 8

            Context:
              variable: x
              scope: global

            💡 Assign a value to 'x' before using it

        Args:
            error: ContextualError to format

        Returns:
            Formatted error string
        """
        lines = []

        # Header: error kind and message
        header = self._format_header(error)
        lines.append(header)

        # Location
        location = self._format_location(error)
        lines.append(location)

        # Context frames (if present)
        if error.context_frames:
            context = self._format_context_frames(error.context_frames)
            lines.append("")
            lines.append("Context:")
            lines.append(context)

        # Help (if present)
        if error.help:
            help_text = self._format_help(error.help)
            lines.append("")
            lines.append(help_text)

        # Error ID (for issue tracking)
        if error.error_id:
            error_id = self._format_error_id(error.error_id)
            lines.append("")
            lines.append(error_id)

        return "\n".join(lines)

    def json(self, error: ContextualError, pretty: bool = True) -> str:
        """Format error as JSON (machine-readable).

        Uses ContextualError.to_dict() and serializes to JSON.
        Safe for logging, APIs, and error tracking systems.

        Args:
            error: ContextualError to format
            pretty: Whether to pretty-print (True) or compact (False)

        Returns:
            JSON-formatted error string
        """
        data = error.to_dict()

        if pretty:
            return json.dumps(data, indent=2)
        else:
            return json.dumps(data, separators=(",", ":"))

    def machine(self, error: ContextualError) -> str:
        """Format error in compact machine-readable format.

        Single-line format: kind | location | message | error_id

        Useful for:
          - Log aggregation systems
          - Error tracking
          - Grep-friendly output

        Example:
            UNDEFINED_VARIABLE | program.ha:5:8 | Variable 'x' is not defined | abc-def-123

        Args:
            error: ContextualError to format

        Returns:
            Compact machine format string
        """
        parts = [
            error.kind.name,
            str(error.location),
            error.message,
            error.error_id,
        ]
        return " | ".join(parts)

    # ========================================================================
    # Helper Methods (Private)
    # ========================================================================

    def _colorize(self, text: str, color: str) -> str:
        """Apply color if enabled.

        Args:
            text: Text to colorize
            color: Color code

        Returns:
            Colorized text (or plain if colors disabled)
        """
        if self.use_colors:
            return _ColorCodes.colorize(text, color)
        return text

    def _format_header(self, error: ContextualError) -> str:
        """Format the error header (kind and message).

        Args:
            error: ContextualError

        Returns:
            Formatted header string
        """
        # Select emoji and color based on error kind
        emoji, color = self._select_visual(error.kind)

        # Format: emoji KIND: message
        kind_str = self._colorize(error.kind.name, color)
        header = f"{emoji} {kind_str}: {error.message}"

        return header

    def _format_location(self, error: ContextualError) -> str:
        """Format the location information.

        Args:
            error: ContextualError

        Returns:
            Formatted location string
        """
        location_str = error.location.format_pretty()
        return f"   at {self._colorize(location_str, _ColorCodes.GRAY)}"

    def _format_context_frames(self, frames: List) -> str:
        """Format context frames.

        Args:
            frames: List of ContextFrame objects

        Returns:
            Formatted context string (multi-line, indented)
        """
        lines = []

        for frame in frames:
            if isinstance(frame, KvFrame):
                lines.append(f"  {frame.key}: {self._format_value(frame.value)}")

            elif isinstance(frame, WithPathFrame):
                lines.append(
                    f"  {frame.label}: {self._colorize(frame.path, _ColorCodes.CYAN)}"
                )

            elif isinstance(frame, WithValueFrame):
                value_str = self._format_value(frame.value)
                if frame.type_hint:
                    lines.append(
                        f"  {frame.label}: {value_str} (type: {frame.type_hint})"
                    )
                else:
                    lines.append(f"  {frame.label}: {value_str}")

            elif isinstance(frame, WithExpectedFrame):
                expected = self._colorize(frame.expected, _ColorCodes.GREEN)
                actual = self._colorize(frame.actual, _ColorCodes.RED)
                lines.append(f"  {frame.label}: expected {expected}, got {actual}")

            elif isinstance(frame, WithSuggestionFrame):
                lines.append(f"  [{frame.category}] {frame.suggestion}")

        return "\n".join(lines)

    def _format_help(self, help_text: str) -> str:
        """Format the help/suggestion text.

        Args:
            help_text: One-line actionable hint

        Returns:
            Formatted help string
        """
        bulb = "💡"
        help_str = self._colorize(f"{bulb} {help_text}", _ColorCodes.YELLOW)
        return help_str

    def _format_error_id(self, error_id: str) -> str:
        """Format the error ID for tracking.

        Args:
            error_id: Error UUID or hash

        Returns:
            Formatted error ID string
        """
        # Short form for display (first 8 chars)
        short_id = error_id[:8]
        return f"Error ID: {self._colorize(short_id, _ColorCodes.GRAY)}"

    def _select_visual(self, kind: ErrorKind) -> tuple:
        """Select appropriate emoji and color for error kind.

        Args:
            kind: ErrorKind enum value

        Returns:
            Tuple of (emoji, color_code)
        """
        kind_str = kind.value

        # Lexical and parse errors
        if kind_str.startswith("lexical/") or kind_str.startswith("parse/"):
            return "❌", _ColorCodes.RED

        # Runtime errors
        elif kind_str.startswith("runtime/"):
            if "name" in kind_str:
                return "🔍", _ColorCodes.RED
            elif "type" in kind_str or "argument" in kind_str:
                return "⚠️", _ColorCodes.YELLOW
            elif "value" in kind_str or "execution" in kind_str:
                return "⚠️", _ColorCodes.YELLOW
            else:
                return "⚠️", _ColorCodes.YELLOW

        # Infrastructure errors
        elif kind_str.startswith("infra/"):
            return "🔧", _ColorCodes.BLUE

        # Internal errors
        elif kind_str.startswith("internal/"):
            return "🐛", _ColorCodes.RED

        # Default
        else:
            return "❓", _ColorCodes.GRAY

    def _format_value(self, value: str) -> str:
        """Format a value for display (with quote handling).

        Args:
            value: Value string

        Returns:
            Formatted value string
        """
        # Values already quoted if strings, just colorize
        if value.startswith('"') or value.startswith("'"):
            return self._colorize(value, _ColorCodes.CYAN)
        else:
            return self._colorize(f"'{value}'", _ColorCodes.CYAN)


# ============================================================================
# Convenience Functions (Module Level)
# ============================================================================


def format_pretty(error: ContextualError, use_colors: bool = True) -> str:
    """Format error as human-readable output.

    Convenience function using default formatter.

    Args:
        error: ContextualError to format
        use_colors: Whether to use colors

    Returns:
        Formatted error string
    """
    formatter = ErrorFormatter(use_colors=use_colors)
    return formatter.pretty(error)


def format_json(error: ContextualError, pretty: bool = True) -> str:
    """Format error as JSON.

    Convenience function using default formatter.

    Args:
        error: ContextualError to format
        pretty: Whether to pretty-print

    Returns:
        JSON-formatted error string
    """
    formatter = ErrorFormatter()
    return formatter.json(error, pretty=pretty)


def format_machine(error: ContextualError) -> str:
    """Format error as compact machine format.

    Convenience function using default formatter.

    Args:
        error: ContextualError to format

    Returns:
        Compact machine format string
    """
    formatter = ErrorFormatter()
    return formatter.machine(error)
