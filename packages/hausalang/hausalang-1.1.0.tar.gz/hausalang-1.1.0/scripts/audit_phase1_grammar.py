import io
import json
import os
import sys
import traceback

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError

suites = {
    "operator_precedence": {
        "valid": [
            ("rubuta 1 + 2 * 3", "7"),
            ("rubuta (1 + 2) * 3", "9"),
            ("rubuta 10 % 3 + 2", "3"),
        ],
        "invalid": [
            ("rubuta 1 + * 2", "PARSE"),
            ("rubuta 5 / (2 *", "PARSE"),
            ("rubuta 10 % % 3", "PARSE"),
        ],
    },
    "unary_and_parentheses": {
        "valid": [
            ("rubuta -5", "-5"),
            ("rubuta +3", "3"),
            ("rubuta -(1 + 2) * 2", "-6"),
        ],
        "invalid": [
            ("rubuta -", "PARSE"),
            ("rubuta + (", "PARSE"),
            ("rubuta -", "PARSE"),
        ],
    },
    "indentation_and_blocks": {
        "valid": [
            ("aiki f():\n    mayar 1\n\nrubuta f()", "1"),
            (
                'suna = "n"\nidan suna == "n":\n    rubuta "yes"\nin ba haka ba:\n    rubuta "no"',
                "yes",
            ),
            ("x = 0\nkadai x < 2:\n    rubuta x\n    x = x + 1", "01"),
        ],
        "invalid": [
            ("aiki f():\nmayar 1", "PARSE"),
            ("idan 1\n    rubuta 1", "PARSE"),
            ("kadai x < 1\nrubuta x", "PARSE"),
        ],
    },
    "functions_and_calls": {
        "valid": [
            ("aiki add(a,b):\n    mayar a + b\n\nrubuta add(2,3)", "5"),
            ("aiki id(x):\n    mayar x\n\nvar = id(7)\nrubuta var", "7"),
            ("aiki zero():\n    mayar None\n\nrubuta zero()", "None"),
        ],
        "invalid": [
            ("aiki f(a):\n    mayar a\n\nrubuta f()", "WRONG_ARGUMENT_COUNT"),
            ("aiki 1bad():\n    mayar 0", "PARSE"),
            ("rubuta unknown_func()", "UNDEFINED_FUNCTION"),
        ],
    },
    "conditionals_and_loops": {
        "valid": [
            ("x = 1\nidan x == 1:\n    rubuta 1", "1"),
            ("x = 0\nkadai x < 3:\n    x = x + 1\nrubuta x", "3"),
            ("aiki f():\n    mayar 2\n\nidan f() == 2:\n    rubuta 9", "9"),
        ],
        "invalid": [
            ("idan :\n    rubuta 1", "PARSE"),
            ("kadai :\n    rubuta 1", "PARSE"),
            ("idan 1:\n    rubuta 1\n  rubuta 2", "PARSE"),
        ],
    },
}

results = {"suites": []}

for suite_name, suite in suites.items():
    suite_res = {"name": suite_name, "cases": []}
    for kind in ("valid", "invalid"):
        for code, expect in suite[kind]:
            case = {"code": code, "expect": expect, "kind": kind}
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    interpret_program(code)
                finally:
                    captured = sys.stdout.getvalue()
                    sys.stdout = old_stdout
                case["status"] = "ok"
                case["output"] = captured
            except ContextualError as e:
                case["status"] = "error"
                case["error_kind"] = getattr(e, "kind", None) and e.kind.name
                case["message"] = str(e)
            except Exception as e:
                case["status"] = "exception"
                case["message"] = str(e)
                case["traceback"] = traceback.format_exc()
            suite_res["cases"].append(case)
    results["suites"].append(suite_res)

print(json.dumps(results, indent=2))
