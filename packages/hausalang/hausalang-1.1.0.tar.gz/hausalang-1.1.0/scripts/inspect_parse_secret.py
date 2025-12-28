import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError

code = "idan 1\n    rubuta 1"

try:
    interpret_program(code)
except ContextualError as e:
    d = e.to_dict()
    print(json.dumps(d, indent=2))
    text = d.get("message", "") + json.dumps(d.get("context_frames", []))
    text_l = text.lower()
    patterns = ["password", "secret", "token", "key", "sk_", "sk-"]
    matches = [p for p in patterns if p in text_l]
    print("\nMatched secret patterns:", matches)
    sys.exit(0)
except Exception as ex:
    print("Other exception:", type(ex).__name__, ex)
    sys.exit(1)

print("No error raised")
