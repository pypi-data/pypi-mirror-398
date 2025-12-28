import json
import os
import re
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import (
    ContextualError,
    ErrorKind,
    SourceLocation,
)

cases = [
    {"id": "lex-unknown-symbol", "code": "rubuta 1 @ 2"},
    {"id": "parse-missing-colon", "code": "idan 1\n    rubuta 1"},
    {"id": "runtime-undef-var", "code": "rubuta x"},
    {"id": "runtime-type", "code": 'rubuta "a" + 5'},
    {"id": "runtime-div-zero", "code": "rubuta 1 / 0"},
]

results = []

# Helpers
DRIVE_RE = re.compile(r"^[A-Za-z]:\\")
# Stricter secret detection: only redact common secret prefixes or long-looking keys
SECRET_PREFIXES = ["sk_", "sk-", "pk_", "pk-", "ak_", "ak-"]
# Regex patterns for long-looking keys (hex or base64-like, length >= 30)
import re

SECRET_REGEXES = [
    re.compile(r"[A-Fa-f0-9]{30,}"),
    re.compile(r"[A-Za-z0-9-_]{30,}"),
]

for c in cases:
    r = {"id": c["id"]}
    try:
        interpret_program(c["code"])
        r["status"] = "no_error"
    except ContextualError as e:
        r["status"] = "contextual_error"
        d = e.to_dict()
        r["kind"] = d.get("kind")
        r["error_id"] = d.get("error_id")
        # JSON serializable?
        try:
            s = json.dumps(d)
            r["json_serializable"] = True
        except Exception as ex:
            r["json_serializable"] = False
            r["json_error"] = str(ex)
        # No absolute file paths in any string fields
        all_values = json.dumps(d)
        r["contains_windows_drives"] = bool(DRIVE_RE.search(all_values))
        r["contains_leading_slash_paths"] = any(
            (v.startswith("/") for v in [d.get("location", {}).get("file_path", "")])
        )
        # No secrets in message or context_frames using stricter checks
        combined = (
            d.get("message", "") + json.dumps(d.get("context_frames", []))
        ).lower()
        has_prefix = any(p in combined for p in SECRET_PREFIXES)
        has_regex = any(rx.search(combined) for rx in SECRET_REGEXES)
        r["contains_secrets"] = bool(has_prefix or has_regex)
        # Timestamp present but not leaked as path
        r["timestamp_present"] = "timestamp" in d
        # Round-trip
        try:
            j = e.to_json()
            e2 = ContextualError.from_json(j)
            r["roundtrip_kind_eq"] = e2.kind == e.kind
            r["roundtrip_error_id_eq"] = e2.error_id == e.error_id
        except Exception as ex:
            r["roundtrip_ok"] = False
            r["roundtrip_error"] = str(ex)
    except Exception as ex:
        r["status"] = "other_exception"
        r["type"] = type(ex).__name__
        r["traceback"] = traceback.format_exc()
    results.append(r)

# Deterministic error id test: create two errors with same kind+location
loc = SourceLocation(file_path="test.ha", line=1, column=0)
e1 = ContextualError(kind=ErrorKind.UNDEFINED_VARIABLE, message="x", location=loc)
e2 = ContextualError(kind=ErrorKind.UNDEFINED_VARIABLE, message="x2", location=loc)
det = {
    "deterministic_ids_equal": e1.error_id == e2.error_id,
    "id1": e1.error_id,
    "id2": e2.error_id,
}

output = {"cases": results, "deterministic": det}
print(json.dumps(output, indent=2))
