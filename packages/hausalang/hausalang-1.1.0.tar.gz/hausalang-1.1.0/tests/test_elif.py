import io
import sys
from hausalang.core.interpreter import run


def test_elif_output():
    with open("examples/elif_demo.ha", "r", encoding="utf-8") as f:
        code = f.read()

    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        run(code)
    finally:
        sys.stdout = old

    out = buf.getvalue()
    assert "eq10" in out
