import io
import sys
from hausalang.core.interpreter import run


def test_comments_output():
    with open("examples/comments.ha", "r", encoding="utf-8") as f:
        code = f.read()

    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        run(code)
    finally:
        sys.stdout = old

    out = buf.getvalue()
    assert "nura" in out
    assert "3" in out
