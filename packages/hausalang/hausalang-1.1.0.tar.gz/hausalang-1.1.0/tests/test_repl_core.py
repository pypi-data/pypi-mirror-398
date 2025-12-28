"""Unit tests for Phase 1 REPL core loop (ReplSession).

These tests exercise persistent state, expression evaluation, and basic error
handling without launching an interactive loop.
"""

from hausalang.repl.session import ReplSession
from hausalang.core.errors import ContextualError, ErrorKind


def test_variable_persistence():
    s = ReplSession()
    r1 = s.execute("x = 5")
    assert r1.success
    r2 = s.execute("y = x + 10")
    assert r2.success
    assert s.get_variable("y") == 15


def test_expression_evaluation_returns_value():
    s = ReplSession()
    r = s.execute("1 + 2")
    assert r.success
    assert r.output == 3


def test_function_definition_and_call():
    s = ReplSession()
    func_src = """
aiki add(a, b):
    mayar a + b
"""
    res_def = s.execute(func_src)
    assert res_def.success
    assert s.function_exists("add")

    call_res = s.execute("result = add(3, 4)")
    assert call_res.success
    assert s.get_variable("result") == 7


def test_contextual_error_returned_on_runtime_error():
    s = ReplSession()
    # undefined variable
    r = s.execute("rubuta undefined")
    assert not r.success
    assert isinstance(r.error, ContextualError)
    assert r.error.kind == ErrorKind.UNDEFINED_VARIABLE
