import io
import json
import os
import sys
import traceback

# Ensure project root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError

cases = [
    {
        "id": "scope-global-local-1",
        "desc": "Function should not modify global variable unless assigned",
        "code": "x = 1\naiki f():\n    x = 2\nf()\nrubuta x",
        "expect": "1",
    },
    {
        "id": "function-return-1",
        "desc": "Function returns value via mayar",
        "code": "aiki add(a,b):\n    mayar a + b\nrubuta add(3,4)",
        "expect": "7",
    },
    {
        "id": "arg-count-error",
        "desc": "Calling function with wrong arg count should error",
        "code": "aiki f(a):\n    mayar a\nrubuta f()",
        "expect_error": "WRONG_ARGUMENT_COUNT",
    },
    {
        "id": "arithmetic-div-mod",
        "desc": "Division and modulo correctness",
        "code": "rubuta 7 / 2\nrubuta 7 % 3",
        # Interpreter uses integer division for ints: 7//2 == 3, then 7%3 == 1 -> combined output "31"
        "expect": "31",
    },
    {
        "id": "loop-for-step-zero",
        "desc": "For loop with step 0 should raise error",
        "code": "don i = 1 zuwa 5 ta 0:\n    rubuta i",
        "expect_error": "ZERO_LOOP_STEP",
    },
    {
        "id": "while-termination",
        "desc": "While loop terminates and produces expected value",
        "code": "x = 0\nkadai x < 3:\n    x = x + 1\nrubuta x",
        "expect": "3",
    },
]

results = []
for case in cases:
    out = {"id": case["id"], "desc": case["desc"]}
    try:
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
