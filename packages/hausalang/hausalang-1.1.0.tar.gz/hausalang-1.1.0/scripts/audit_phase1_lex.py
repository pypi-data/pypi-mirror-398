import io
import json
import os
import sys
import traceback

# Ensure project root is on sys.path so `hausalang` package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError

cases = [
    {
        "id": "lex-valid-1",
        "desc": "Identifier and integer number",
        "code": "x = 123\nrubuta x",
        "expect": {"type": "print", "output": "123"},
    },
    {
        "id": "lex-valid-2",
        "desc": "String with escape sequences",
        "code": 'rubuta "hello\\nworld"',
        "expect": {"type": "print", "output": "hello\\nworld"},
    },
    {
        "id": "lex-valid-3",
        "desc": "Identifier with underscore",
        "code": "var_1 = 5\nrubuta var_1",
        "expect": {"type": "print", "output": "5"},
    },
    # Invalid cases
    {
        "id": "lex-invalid-1",
        "desc": "Unknown symbol '@'",
        "code": "x = 1\nrubuta @",
        "expect": {"type": "error", "kind": "LEXICAL"},
    },
    {
        "id": "lex-invalid-2",
        "desc": "Unterminated string",
        "code": 'rubuta "unterminated',
        "expect": {"type": "error", "kind": "LEXICAL"},
    },
    {
        "id": "lex-invalid-3",
        "desc": "Malformed number",
        "code": "rubuta 12.34.56",
        "expect": {"type": "error", "kind": "PARSE"},
    },
]

results = []
for case in cases:
    out = {"id": case["id"], "desc": case["desc"]}
    try:
        # Capture stdout produced by the interpreter
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            interpret_program(case["code"])
        finally:
            captured = sys.stdout.getvalue()
            sys.stdout = old_stdout

        out["status"] = "ok"
        out["output"] = captured
    except ContextualError as e:
        out["status"] = "error"
        try:
            out["error_kind"] = e.kind.name
        except Exception:
            out["error_kind"] = str(getattr(e, "kind", repr(e)))
        out["message"] = str(e)
    except Exception as e:
        out["status"] = "exception"
        out["message"] = str(e)
        out["traceback"] = traceback.format_exc()
    results.append(out)

print(json.dumps(results, indent=2))
