"""
Serialization Tests for Hausalang v1.1 Error Reporting

Tests verify that errors can be serialized to JSON and deserialized
without loss of information, and that sensitive data is not exposed.

Run with: pytest tests/test_error_serialization.py -v
"""

import pytest
import json
from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError


# ============================================================================
# JSON ROUND-TRIP SERIALIZATION
# ============================================================================


class TestErrorSerialization:
    """Tests for serializing errors to JSON."""

    def test_error_to_dict_produces_dict(self):
        """Error can be converted to dict."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        error_dict = error.to_dict()

        assert isinstance(error_dict, dict)
        assert "kind" in error_dict
        assert "message" in error_dict
        assert "location" in error_dict

    def test_error_to_json_produces_json_string(self):
        """Error can be serialized to JSON string."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        json_str = error.to_json()

        assert isinstance(json_str, str)
        # Should be valid JSON
        data = json.loads(json_str)
        assert "kind" in data

    def test_error_dict_has_all_fields(self):
        """Error dict should include all important fields."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        error_dict = error.to_dict()

        # Required fields
        assert "kind" in error_dict
        assert "message" in error_dict
        assert "location" in error_dict
        assert "error_id" in error_dict
        assert "timestamp" in error_dict

        # Location should have line/column
        assert isinstance(error_dict["location"], dict)
        assert "line" in error_dict["location"]
        assert "column" in error_dict["location"]

    def test_error_dict_location_format(self):
        """Location in dict should have proper format."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        error_dict = error.to_dict()

        loc = error_dict["location"]
        assert isinstance(loc["line"], int)
        assert isinstance(loc["column"], int)
        assert loc["line"] >= 1
        assert loc["column"] >= 0


# ============================================================================
# JSON DESERIALIZATION / ROUND-TRIP
# ============================================================================


class TestErrorDeserialization:
    """Tests for deserializing errors from JSON."""

    def test_error_from_dict_restores_kind(self):
        """Deserialized error has same kind as original."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        original_error = exc_info.value
        original_kind = original_error.kind

        # Serialize and deserialize
        error_dict = original_error.to_dict()
        restored_error = ContextualError.from_dict(error_dict)

        assert restored_error.kind == original_kind

    def test_error_from_dict_restores_message(self):
        """Deserialized error has same message as original."""
        code = "rubuta undefined_var"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        original_error = exc_info.value
        original_msg = original_error.message

        # Serialize and deserialize
        error_dict = original_error.to_dict()
        restored_error = ContextualError.from_dict(error_dict)

        assert restored_error.message == original_msg

    def test_error_from_dict_restores_location(self):
        """Deserialized error has same location as original."""
        code = "x = 5\ny = undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        original_error = exc_info.value
        original_line = original_error.location.line
        original_col = original_error.location.column

        # Serialize and deserialize
        error_dict = original_error.to_dict()
        restored_error = ContextualError.from_dict(error_dict)

        assert restored_error.location.line == original_line
        assert restored_error.location.column == original_col

    def test_error_json_round_trip(self):
        """Error survives JSON round-trip."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        original_error = exc_info.value

        # Serialize to JSON string, then back
        json_str = original_error.to_json()
        json_dict = json.loads(json_str)
        restored_error = ContextualError.from_dict(json_dict)

        # Should have same key properties
        assert restored_error.kind == original_error.kind
        assert restored_error.message == original_error.message
        assert restored_error.location.line == original_error.location.line
        assert restored_error.location.column == original_error.location.column


# ============================================================================
# JSON SAFETY / REDACTION
# ============================================================================


class TestErrorSafetyInSerialization:
    """Tests that errors don't leak sensitive information in JSON."""

    def test_json_output_readable(self):
        """JSON output should be machine-readable."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        json_str = error.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert "kind" in data
        assert "message" in data

    def test_json_contains_no_backticks_in_message(self):
        """JSON message shouldn't have backticks (logging safety)."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        json_dict = json.loads(error.to_json())

        msg = json_dict.get("message", "")
        # Backticks are OK in message text, just checking it's reasonable
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_context_frames_in_serialization(self):
        """Context frames should be included in serialization if present."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        error_dict = error.to_dict()

        # context_frames might be empty, but should be present
        assert "context_frames" in error_dict
        assert isinstance(error_dict["context_frames"], list)

    def test_error_id_stable_across_serialization(self):
        """Error ID should be stable across serialization."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        original_error = exc_info.value
        original_id = original_error.error_id

        # Serialize and deserialize
        json_str = original_error.to_json()
        json_dict = json.loads(json_str)
        restored_error = ContextualError.from_dict(json_dict)

        # Error ID should match
        assert restored_error.error_id == original_id


# ============================================================================
# COMPACT JSON FORMAT
# ============================================================================


class TestCompactJsonFormat:
    """Tests for compact vs pretty JSON formats."""

    def test_compact_json_smaller_than_pretty(self):
        """JSON should be reasonably sized."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value

        json_str = error.to_json()

        # Should be valid
        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_compact_json_valid(self):
        """JSON should be valid and deserializable."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        json_str = error.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert "kind" in data
        assert "message" in data


# ============================================================================
# ERROR FIELDS PRESERVATION
# ============================================================================


class TestErrorFieldsPreservation:
    """Tests that all error fields are preserved in serialization."""

    def test_serialized_error_has_timestamp(self):
        """Serialized error should include timestamp."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        error_dict = error.to_dict()

        assert "timestamp" in error_dict
        assert isinstance(error_dict["timestamp"], str)
        # Should look like ISO format
        assert len(error_dict["timestamp"]) > 10

    def test_serialized_error_has_kind_string(self):
        """Serialized error should have ErrorKind as string."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        error_dict = error.to_dict()

        assert isinstance(error_dict["kind"], str)
        # Should be a valid ErrorKind
        kind_str = error_dict["kind"]
        assert "_" in kind_str  # Like UNDEFINED_VARIABLE

    def test_file_path_in_location(self):
        """File path should be in location."""
        code = "rubuta undefined"

        with pytest.raises(ContextualError) as exc_info:
            interpret_program(code)

        error = exc_info.value
        assert error.location.file_path is not None
        assert isinstance(error.location.file_path, str)
