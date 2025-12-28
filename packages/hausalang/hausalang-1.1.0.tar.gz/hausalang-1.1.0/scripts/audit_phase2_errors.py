import json
import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError, ErrorKind, SourceLocation

cases = [
    {
        "id": "lex-unknown-symbol",
        "code": "rubuta 1 @ 2",
        "expected_kind": ErrorKind.UNKNOWN_SYMBOL,
        "expected_base": SyntaxError,
    },
    {
        "id": "lex-unclosed-string",
        "code": 'rubuta "unterminated',
        "expected_kind": ErrorKind.UNCLOSED_STRING,
        "expected_base": SyntaxError,
    },
    {
        "id": "parse-missing-colon",
        "code": "idan 1\n    rubuta 1",  # missing ':' after 'idan 1'
        "expected_kind": ErrorKind.MISSING_COLON,
        "expected_base": SyntaxError,
    },
    {
        "id": "runtime-undefined-variable",
        "code": "rubuta x",
        "expected_kind": ErrorKind.UNDEFINED_VARIABLE,
        "expected_base": NameError,
    },
    {
        "id": "runtime-undefined-function",
        "code": "rubuta unknown()",
        "expected_kind": ErrorKind.UNDEFINED_FUNCTION,
        "expected_base": NameError,
    },
    {
        "id": "runtime-type-error",
        "code": 'rubuta "a" + 5',
        "expected_kind": ErrorKind.INVALID_OPERAND_TYPE,
        "expected_base": TypeError,
    },
    {
        "id": "runtime-division-by-zero",
        "code": "rubuta 1 / 0",
        "expected_kind": ErrorKind.DIVISION_BY_ZERO,
        "expected_base": ValueError,  # ErrorKind maps to ValueError per errors module
    },
]

results = []
for c in cases:
    r = {"id": c["id"], "code": c["code"]}
    try:
        interpret_program(c["code"])
        r["status"] = "no_error"
    except ContextualError as e:
        r["status"] = "contextual_error"
        r["kind"] = e.kind.name if hasattr(e, "kind") else None
        r["kind_value"] = e.kind.value if hasattr(e, "kind") else None
        r["message"] = e.message if hasattr(e, "message") else str(e)
        # SourceLocation
        loc = getattr(e, "location", None)
        if isinstance(loc, SourceLocation):
            r["location"] = {
                "file_path": loc.file_path,
                "line": loc.line,
                "column": loc.column,
            }
        else:
            r["location"] = None
        # Context frames
        r["context_frames_count"] = len(getattr(e, "context_frames", []))
        r["has_help"] = bool(getattr(e, "help", None))
        # Catchability check
        r["isinstance_as_expected_base"] = (
            isinstance(e, c["expected_base"]) if c.get("expected_base") else False
        )
    except Exception as exc:
        r["status"] = "other_exception"
        r["exc_type"] = type(exc).__name__
        r["traceback"] = traceback.format_exc()
    results.append(r)

print(json.dumps(results, indent=2))
