import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError

cases = [
    {"id": "ex-hello", "path": "examples/hello.ha", "expect_error": False},
    {"id": "ex-arith", "path": "examples/arithmetic.ha", "expect_error": False},
    {"id": "ex-func", "path": "examples/functions.ha", "expect_error": False},
    # v1.0 error-behavior checks
    {
        "id": "bc-unknown-symbol",
        "code": "rubuta 1 @ 2",
        "expected_builtin": SyntaxError,
    },
    {
        "id": "bc-unclosed-string",
        "code": 'rubuta "unterminated',
        "expected_builtin": SyntaxError,
    },
    {"id": "bc-undefined-var", "code": "rubuta x", "expected_builtin": NameError},
    {
        "id": "bc-undefined-func",
        "code": "rubuta unknown()",
        "expected_builtin": NameError,
    },
    {"id": "bc-type-error", "code": 'rubuta "a" + 5', "expected_builtin": TypeError},
    {"id": "bc-zerodiv", "code": "rubuta 1 / 0", "expected_builtin": ZeroDivisionError},
]

results = []


# helper to run code
def run_code(code):
    try:
        interpret_program(code)
        return {"status": "ok"}
    except ContextualError as e:
        return {
            "status": "contextual_error",
            "type": type(e).__name__,
            "is_contextual": True,
            "is_builtin_instance": isinstance(e, Exception)
            and any(
                isinstance(e, t)
                for t in (
                    SyntaxError,
                    NameError,
                    ValueError,
                    TypeError,
                    ZeroDivisionError,
                )
            ),
            "kind": getattr(e, "kind", None).name if hasattr(e, "kind") else None,
        }
    except Exception as e:
        return {
            "status": "exception",
            "type": type(e).__name__,
            "is_builtin_instance": True,
        }


for c in cases:
    entry = {"id": c["id"]}
    if "path" in c:
        p = os.path.join(ROOT, c["path"])
        try:
            with open(p, "r", encoding="utf-8") as f:
                src = f.read()
        except Exception as e:
            entry["status"] = "missing_example"
            entry["error"] = str(e)
            results.append(entry)
            continue
        out = run_code(src)
        entry.update(out)
    else:
        out = run_code(c["code"])
        entry.update(out)
        # check expected builtin inheritance
        eb = c.get("expected_builtin")
        if eb and entry.get("status") in ("contextual_error", "exception"):
            # Re-run to capture the exception object
            try:
                interpret_program(c["code"])
            except Exception as e:
                entry["raised_type"] = type(e).__name__
                entry["isinstance_of_expected_builtin"] = isinstance(e, eb)
    results.append(entry)

print(json.dumps(results, indent=2))
