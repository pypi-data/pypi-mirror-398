"""
Error Type System for Hausalang v1.1

This module defines the ContextualError type and supporting classes for
enhanced error reporting. All errors in the v1.1+ pipeline use this system.

Key Components:
  - ErrorKind: Formal error hierarchy (30+ kinds)
  - SourceLocation: Pinpoint error origin (file, line, column)
  - ContextFrame: Stackable diagnostic frames (5 types)
  - ContextualError: Core error type (safe to log, machine-readable, human-friendly)

Design Principles:
  - Zero modification to v1.0 core
  - Backward compatible via inheritance (SyntaxError, NameError, ValueError, etc.)
  - All errors answer: what? where? why? what_input? expected?
  - Safe to log (no PII/secrets)
  - Machine-readable first, human-friendly second
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Set, Union, Dict, Any


# ============================================================================
# ERROR KIND HIERARCHY
# ============================================================================


class ErrorKind(Enum):
    """
    Formal error taxonomy for Hausalang.

    Organized by stage:
      L1 (Lexical):  Tokenization errors
      L2 (Parse):    Syntax/grammar errors
      L3 (Runtime):  Execution errors
      Infra:         System/IO errors
      Internal:      Compiler bugs

    Each kind has a dotted value (e.g., "lexical/unknown_symbol")
    for machine-readable categorization.
    """

    # ===== APP ERRORS (User Code Mistakes) =====

    # L1: LEXICAL ERRORS (Tokenization)
    UNKNOWN_SYMBOL = "lexical/unknown_symbol"
    UNCLOSED_STRING = "lexical/unclosed_string"
    INVALID_NUMBER = "lexical/invalid_number"
    INVALID_ESCAPE = "lexical/invalid_escape"
    INVALID_INDENT = "lexical/invalid_indent"
    INDENT_LEVEL_MISMATCH = "lexical/indent_level_mismatch"

    # L2: PARSE ERRORS (Syntax/Grammar)
    UNEXPECTED_TOKEN = "parse/unexpected_token"
    EXPECTED_TOKEN = "parse/expected_token"
    MISSING_COLON = "parse/missing_colon"
    MISSING_INDENT = "parse/missing_indent"
    UNMATCHED_PAREN = "parse/unmatched_paren"
    UNEXPECTED_EOF = "parse/unexpected_eof"

    # L3a: NAME ERRORS (Variable/Function Resolution)
    UNDEFINED_VARIABLE = "runtime/name/undefined_variable"
    UNDEFINED_FUNCTION = "runtime/name/undefined_function"
    UNDEFINED_PARAMETER = "runtime/name/undefined_parameter"

    # L3b: TYPE ERRORS (Type Mismatches)
    INVALID_OPERAND_TYPE = "runtime/type/invalid_operand_type"
    STRING_NUMBER_CONCAT = "runtime/type/string_number_concat"
    NON_NUMERIC_ARITHMETIC = "runtime/type/non_numeric_arithmetic"
    NON_BOOLEAN_CONDITION = "runtime/type/non_boolean_condition"
    WRONG_ARGUMENT_TYPE = "runtime/type/wrong_argument_type"

    # L3c: ARGUMENT ERRORS (Function Arguments)
    WRONG_ARGUMENT_COUNT = "runtime/argument/wrong_argument_count"
    MISSING_REQUIRED_ARG = "runtime/argument/missing_required_arg"
    UNEXPECTED_KEYWORD_ARG = "runtime/argument/unexpected_keyword_arg"

    # L3d: VALUE ERRORS (Invalid Values)
    DIVISION_BY_ZERO = "runtime/value/division_by_zero"
    ZERO_LOOP_STEP = "runtime/value/zero_loop_step"
    NEGATIVE_LOOP_STEP = "runtime/value/negative_loop_step"
    EMPTY_REQUIRED_VALUE = "runtime/value/empty_required_value"
    OUT_OF_RANGE = "runtime/value/out_of_range"

    # L3e: ASSERTION ERRORS
    ASSERTION_FAILED = "runtime/assertion/assertion_failed"

    # L3f: EXECUTION ERRORS (Control Flow)
    INFINITE_LOOP = "runtime/execution/infinite_loop"
    STACK_OVERFLOW = "runtime/execution/stack_overflow"
    UNKNOWN_OPERATOR = "runtime/execution/unknown_operator"
    UNKNOWN_STATEMENT_TYPE = "runtime/execution/unknown_statement_type"

    # ===== INFRASTRUCTURE ERRORS (System/IO) =====
    FILE_NOT_FOUND = "infra/file_not_found"
    FILE_READ_ERROR = "infra/file_read_error"
    ENCODING_ERROR = "infra/encoding_error"
    IO_ERROR = "infra/io_error"
    PERMISSION_DENIED = "infra/permission_denied"

    # ===== INTERNAL ERRORS (Compiler Bugs) =====
    COMPILER_BUG = "internal/compiler_bug"
    INTERPRETER_BUG = "internal/interpreter_bug"
    INVALID_AST_NODE = "internal/invalid_ast_node"
    ASSERTION_FAILED_INTERNAL = "internal/assertion_failed"


# ============================================================================
# SOURCE LOCATION
# ============================================================================


@dataclass(frozen=True)
class SourceLocation:
    """
    Pinpoint error origin in source code.

    All line numbers are 1-indexed (user-facing).
    All columns are 0-indexed (matches lexer convention).

    Attributes:
        file_path: Relative path to .ha file (e.g., "program.ha")
        line: 1-indexed line number
        column: 0-indexed column number
        end_line: Optional end position (for multi-line constructs)
        end_column: Optional end column position
    """

    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __str__(self) -> str:
        """Machine format: file:line:column"""
        return f"{self.file_path}:{self.line}:{self.column}"

    def format_pretty(self) -> str:
        """Human format: 'file on line N, column M'"""
        return f"{self.file_path} on line {self.line}, column {self.column}"


# ============================================================================
# CONTEXT FRAMES (Stackable Diagnostics)
# ============================================================================


@dataclass(frozen=True)
class KvFrame:
    """
    Key-value diagnostic pair.

    Example: KvFrame(key="step_size", value="0")
    """

    key: str
    value: str

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


@dataclass(frozen=True)
class WithPathFrame:
    """
    Path-related context.

    Example: WithPathFrame(label="file", path="./program.ha")
    """

    label: str
    path: str

    def __str__(self) -> str:
        return f"{self.label}: {self.path}"


@dataclass(frozen=True)
class WithValueFrame:
    """
    Actual value that caused problem.

    Example: WithValueFrame(
        label="problematic_input",
        value="undefined_var",
        type_hint="undefined"
    )
    """

    label: str
    value: str  # Capped at 50 chars for safety
    type_hint: Optional[str] = None

    def __str__(self) -> str:
        if self.type_hint:
            return f"{self.label}: {self.value!r} (type: {self.type_hint})"
        return f"{self.label}: {self.value!r}"


@dataclass(frozen=True)
class WithExpectedFrame:
    """
    What was expected instead.

    Example: WithExpectedFrame(
        label="expected_type",
        expected="str",
        actual="int"
    )
    """

    label: str
    expected: str  # Capped at 50 chars
    actual: str  # Capped at 50 chars

    def __str__(self) -> str:
        return f"{self.label}: expected {self.expected!r}, got {self.actual!r}"


@dataclass(frozen=True)
class WithSuggestionFrame:
    """
    Actionable suggestion for recovery.

    Example: WithSuggestionFrame(
        suggestion="Use '+' for string concatenation",
        category="syntax_fix"
    )
    """

    suggestion: str
    category: str  # "syntax_fix", "config_fix", "input_fix", "debugging"

    def __str__(self) -> str:
        return f"[{self.category}] {self.suggestion}"


# Union type for context frames
ContextFrame = Union[
    KvFrame,
    WithPathFrame,
    WithValueFrame,
    WithExpectedFrame,
    WithSuggestionFrame,
]


# ============================================================================
# CONTEXTUAL ERROR (Core Error Type)
# ============================================================================


def _determine_error_base_class(kind: ErrorKind) -> type:
    """
    Determine which Python exception to inherit from based on error kind.

    This ensures backward compatibility with existing error handlers:
    - Lexical/Parse errors → inherit from SyntaxError
    - Name errors → inherit from NameError
    - Value/Type errors → inherit from ValueError/TypeError/ZeroDivisionError
    - Others → inherit from RuntimeError

    Args:
        kind: The ErrorKind to categorize

    Returns:
        Python exception class to inherit from
    """
    kind_str = kind.value

    if kind_str.startswith("lexical/") or kind_str.startswith("parse/"):
        return SyntaxError
    elif kind_str.startswith("runtime/name/"):
        return NameError
    elif kind_str == "runtime/value/division_by_zero":
        return ZeroDivisionError
    elif kind_str.startswith("runtime/value/"):
        return ValueError
    elif kind_str.startswith("runtime/type/"):
        return TypeError
    elif kind_str.startswith("infra/"):
        return OSError
    else:
        return RuntimeError


class ContextualError(Exception):
    """
    Core error type for Hausalang v1.1+.

    Guarantees:
      - Safe to log (no PII/secrets, values capped at 50 chars)
      - Machine-readable (JSON serializable, structured)
      - Human-friendly (pretty formatter available)
      - Backward compatible (inherits from stdlib exceptions)

    Every error answers five questions:
      1. What failed? (kind)
      2. Where did it fail? (location)
      3. Why did it fail? (message)
      4. What was the problematic input? (context_frames[WithValue])
      5. What was expected instead? (help + context_frames[WithExpected])

    Attributes:
        kind: ErrorKind from formal hierarchy
        message: Primary error description (human-readable, 1-200 chars)
        location: SourceLocation (file, line, column)
        source: Optional original exception (for chaining)
        context_frames: List of diagnostic frames (0 or more)
        tags: Set of categorical tags (e.g., {"recoverable", "input-error"})
        help: One-line actionable fix (≤80 chars, optional)
        timestamp: When error occurred
        error_id: UUID or deterministic hash for tracking
    """

    # Cache for dynamically-created subclasses keyed by base exception name
    _DYN_SUBCLASS_CACHE: Dict[str, type] = {}

    def __new__(cls, *args, kind: ErrorKind = None, **kwargs):
        """
        Create an instance of a dynamic subclass that also inherits from the
        appropriate builtin exception (e.g., SyntaxError, NameError).

        We create a small dynamic subclass on first use per builtin base and
        cache it to preserve identity and picklability where possible.
        """
        # On subclass usage, no dynamic dispatch necessary
        if cls is not ContextualError:
            return super().__new__(cls)

        # Determine kind either from keyword or positional args (old signature)
        actual_kind = kind
        if actual_kind is None and len(args) >= 1 and isinstance(args[0], ErrorKind):
            actual_kind = args[0]

        base_exc = (
            _determine_error_base_class(actual_kind) if actual_kind else RuntimeError
        )

        cache_key = base_exc.__name__
        Dyn = ContextualError._DYN_SUBCLASS_CACHE.get(cache_key)
        if Dyn is None:
            # Create dynamic subclass that preserves ContextualError.__init__ by
            # placing ContextualError first in the MRO, and also inherits from
            # the builtin base so isinstance(..., base_exc) is True.
            Dyn = type(f"ContextualError_{cache_key}", (ContextualError, base_exc), {})
            ContextualError._DYN_SUBCLASS_CACHE[cache_key] = Dyn

        # Allocate instance of dynamic class using Dyn.__new__ which will
        # delegate to the correct base __new__ implementation as needed.
        instance = Dyn.__new__(Dyn)
        return instance

    def __init__(
        self,
        kind: ErrorKind,
        message: str,
        location: SourceLocation,
        source: Optional[Exception] = None,
        context_frames: Optional[List[ContextFrame]] = None,
        tags: Optional[Set[str]] = None,
        help: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        error_id: Optional[str] = None,
    ):
        """
        Initialize a ContextualError.

        Args:
            kind: ErrorKind categorizing the error
            message: Primary error description
            location: SourceLocation of error origin
            source: Optional wrapped exception (for chaining)
            context_frames: Optional list of diagnostic frames
            tags: Optional set of tags for categorization
            help: Optional one-line actionable hint
            timestamp: Optional timestamp (defaults to now)
            error_id: Optional error ID (defaults to deterministic UUID)
        """
        self.kind = kind
        self.message = message
        self.location = location
        self.source = source
        self.context_frames = context_frames or []
        self.tags = tags or set()
        self.help = help
        self.timestamp = timestamp or datetime.now()

        # Generate deterministic error ID if not provided
        if error_id is None:
            # Hash of kind + location for determinism (helps deduplication)
            hash_input = (
                f"{kind.value}:{location.file_path}:{location.line}:{location.column}"
            )
            error_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_input))
        self.error_id = error_id

        # Call parent Exception.__init__ with message
        super().__init__(self.message)

        # Set the __cause__ to source exception if provided (for traceback chaining)
        if self.source:
            self.__cause__ = self.source

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Format: "ErrorKind: message @ file:line:column"
        """
        return f"{self.kind.name}: {self.message} @ {self.location}"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"ContextualError(kind={self.kind.name}, "
            f"message={self.message!r}, "
            f"location={self.location!r})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to machine-readable dictionary (JSON-safe).

        Returns:
            Dictionary with all error data

        Notes:
            - Context frames serialized with __class__.__name__ for type detection
            - All values are JSON-serializable
            - Timestamps in ISO format
            - No secrets/PII included
        """

        def serialize_frame(frame: ContextFrame) -> Dict[str, Any]:
            """Serialize a context frame to dict with type info."""
            return {
                "type": frame.__class__.__name__,
                **asdict(frame),
            }

        return {
            "kind": self.kind.value,
            "kind_name": self.kind.name,
            "message": self.message,
            "location": {
                "file_path": self.location.file_path,
                "line": self.location.line,
                "column": self.location.column,
                "end_line": self.location.end_line,
                "end_column": self.location.end_column,
            },
            "context_frames": [serialize_frame(f) for f in self.context_frames],
            "tags": list(self.tags),
            "help": self.help,
            "timestamp": self.timestamp.isoformat(),
            "error_id": self.error_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextualError":
        """
        Reconstruct ContextualError from dictionary (round-trip safety).

        Args:
            data: Dictionary from to_dict()

        Returns:
            ContextualError instance
        """
        # Reconstruct ErrorKind from value
        kind = ErrorKind(data["kind"])

        # Reconstruct SourceLocation
        loc_data = data["location"]
        location = SourceLocation(
            file_path=loc_data["file_path"],
            line=loc_data["line"],
            column=loc_data["column"],
            end_line=loc_data.get("end_line"),
            end_column=loc_data.get("end_column"),
        )

        # Reconstruct context frames
        context_frames = []
        frame_classes = {
            "KvFrame": KvFrame,
            "WithPathFrame": WithPathFrame,
            "WithValueFrame": WithValueFrame,
            "WithExpectedFrame": WithExpectedFrame,
            "WithSuggestionFrame": WithSuggestionFrame,
        }

        for frame_data in data.get("context_frames", []):
            frame_type = frame_data.pop("type")
            frame_class = frame_classes.get(frame_type)
            if frame_class:
                context_frames.append(frame_class(**frame_data))

        # Reconstruct timestamp
        timestamp = datetime.fromisoformat(data["timestamp"])

        # Create error
        return cls(
            kind=kind,
            message=data["message"],
            location=location,
            context_frames=context_frames,
            tags=set(data.get("tags", [])),
            help=data.get("help"),
            timestamp=timestamp,
            error_id=data.get("error_id"),
        )

    def to_json(self) -> str:
        """
        Serialize to JSON string (for logging, APIs, etc.).

        Returns:
            JSON-formatted string
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ContextualError":
        """
        Reconstruct from JSON string.

        Args:
            json_str: JSON string from to_json()

        Returns:
            ContextualError instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def with_context(self, frame: ContextFrame) -> "ContextualError":
        """
        Create a new ContextualError with additional context frame.

        This allows building up context without mutation:

            error = ContextualError(...)
            error = error.with_context(KvFrame("step", "0"))
            error = error.with_context(WithSuggestionFrame(...))

        Args:
            frame: ContextFrame to add

        Returns:
            New ContextualError with frame added
        """
        new_frames = self.context_frames + [frame]
        return ContextualError(
            kind=self.kind,
            message=self.message,
            location=self.location,
            source=self.source,
            context_frames=new_frames,
            tags=self.tags.copy(),
            help=self.help,
            timestamp=self.timestamp,
            error_id=self.error_id,
        )

    def with_help(self, help_text: str) -> "ContextualError":
        """
        Create a new ContextualError with help text.

        Args:
            help_text: One-line actionable hint (≤80 chars)

        Returns:
            New ContextualError with help set
        """
        return ContextualError(
            kind=self.kind,
            message=self.message,
            location=self.location,
            source=self.source,
            context_frames=self.context_frames.copy(),
            tags=self.tags.copy(),
            help=help_text,
            timestamp=self.timestamp,
            error_id=self.error_id,
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def is_lexical_error(kind: ErrorKind) -> bool:
    """Check if error is a lexical (L1) error."""
    return kind.value.startswith("lexical/")


def is_parse_error(kind: ErrorKind) -> bool:
    """Check if error is a parse (L2) error."""
    return kind.value.startswith("parse/")


def is_runtime_error(kind: ErrorKind) -> bool:
    """Check if error is a runtime (L3) error."""
    return kind.value.startswith("runtime/")


def is_infra_error(kind: ErrorKind) -> bool:
    """Check if error is an infrastructure error."""
    return kind.value.startswith("infra/")


def is_internal_error(kind: ErrorKind) -> bool:
    """Check if error is an internal (compiler bug) error."""
    return kind.value.startswith("internal/")


def redact_value(value: str, max_length: int = 50) -> str:
    """
    Redact sensitive values for safe logging.

    - Caps string length at max_length
    - Redacts known patterns (passwords, API keys, etc.)

    Args:
        value: String to redact
        max_length: Maximum length before truncation

    Returns:
        Redacted string
    """
    # Known patterns to redact
    redact_patterns = [
        "password",
        "secret",
        "token",
        "key",
        "api",
        "auth",
        "credential",
        "private",
        "sk_",
        "sk-",
        "pk_",
        "pk-",
    ]

    value_lower = value.lower()

    # Check if contains sensitive pattern
    for pattern in redact_patterns:
        if pattern in value_lower:
            return "<redacted>"

    # Cap length
    if len(value) > max_length:
        return value[:max_length] + "..."

    return value
