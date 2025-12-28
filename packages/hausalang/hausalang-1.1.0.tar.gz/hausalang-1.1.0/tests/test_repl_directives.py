"""Unit tests for REPL directives (Phase 2).

Tests use DirectiveProcessor directly with a ReplSession to avoid launching
an interactive loop.
"""

from hausalang.repl.session import ReplSession
from hausalang.repl.directives import DirectiveProcessor


def test_vars_and_funcs_directives():
    s = ReplSession()
    s.execute("x = 10")
    func_src = """
aiki add(a, b):
    mayar a + b
"""
    s.execute(func_src)

    dp = DirectiveProcessor(s)
    out_vars = dp.process(":vars")
    assert "x = 10" in out_vars

    out_funcs = dp.process(":funcs")
    assert "add()" in out_funcs


def test_clear_directive():
    s = ReplSession()
    s.execute("z = 99")
    dp = DirectiveProcessor(s)
    resp = dp.process(":clear")
    assert resp == "State cleared."
    assert not s.variable_exists("z")


def test_load_and_history_and_save(tmp_path):
    s = ReplSession()
    dp = DirectiveProcessor(s)
    # create a small file to load
    p = tmp_path / "load_test.ha"
    p.write_text("a = 42\n")

    res = dp.process(f":load {p}")
    assert "Loaded:" in res
    assert s.get_variable("a") == 42

    # history should contain the loaded source as one entry (session.load_file appends nothing,
    # but session.execute appends — ensure execute history works)
    s.execute("b = 7")
    hist = dp.process(":history 10")
    assert "b = 7" in hist

    # test save
    out_file = tmp_path / "hist_save.txt"
    save_resp = dp.process(f":save {out_file}")
    assert "History saved to" in save_resp
    assert out_file.exists()
    data = out_file.read_text()
    assert "b = 7" in data
