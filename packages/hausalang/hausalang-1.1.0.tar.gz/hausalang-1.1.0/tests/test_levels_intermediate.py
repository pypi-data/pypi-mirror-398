"""Intermediate Level Tests for Hausalang v1.1 REPL

Tests focus on:
- Function definition and calling
- Conditional statements (if/else)
- Simple loops (while)
- Variable scope
"""

from hausalang.repl.session import ReplSession
from hausalang.core.errors import ErrorKind


class TestIntermediateFunctions:
    """Function definition and calls"""

    def test_define_function(self):
        """Define a function"""
        s = ReplSession()
        code = """
aiki add(a, b):
    mayar a + b
"""
        r = s.execute(code)
        assert r.success
        assert s.function_exists("add")

    def test_call_function(self):
        """Call a defined function"""
        s = ReplSession()
        s.execute(
            """
aiki multiply(x, y):
    mayar x * y
"""
        )
        r = s.execute("result = multiply(3, 4)")
        assert r.success
        assert s.get_variable("result") == 12

    def test_function_with_multiple_args(self):
        """Function with 3+ arguments"""
        s = ReplSession()
        s.execute(
            """
aiki sum_three(a, b, c):
    mayar a + b + c
"""
        )
        r = s.execute("x = sum_three(1, 2, 3)")
        assert r.success
        assert s.get_variable("x") == 6

    def test_function_returns_string(self):
        """Function can return strings"""
        s = ReplSession()
        s.execute(
            """
aiki greet(name):
    mayar "Hello " + name
"""
        )
        r = s.execute('msg = greet("World")')
        assert r.success
        assert s.get_variable("msg") == "Hello World"

    def test_wrong_argument_count_error(self):
        """Wrong number of arguments raises error"""
        s = ReplSession()
        s.execute(
            """
aiki add(a, b):
    mayar a + b
"""
        )
        r = s.execute("result = add(5)")
        assert not r.success
        assert r.error.kind == ErrorKind.WRONG_ARGUMENT_COUNT


class TestIntermediateConditionals:
    """If/else statements"""

    def test_if_true(self):
        """If with true condition executes then-body"""
        s = ReplSession()
        s.execute("x = 10")
        s.execute(
            """
idan x > 5:
    result = "big"
"""
        )
        assert s.get_variable("result") == "big"

    def test_if_false(self):
        """If with false condition skips then-body"""
        s = ReplSession()
        s.execute("x = 3")
        s.execute("result = None")
        s.execute(
            """
idan x > 5:
    result = "big"
"""
        )
        assert s.get_variable("result") is None

    def test_if_else(self):
        """If/else statement"""
        s = ReplSession()
        s.execute("x = 2")
        s.execute(
            """
idan x > 5:
    result = "big"
in ba haka ba:
    result = "small"
"""
        )
        assert s.get_variable("result") == "small"

    def test_elif_chain(self):
        """Multiple elif clauses"""
        s = ReplSession()
        s.execute("score = 75")
        s.execute(
            """
idan score >= 90:
    grade = "A"
idan score >= 80 kuma:
    grade = "B"
idan score >= 70 kuma:
    grade = "C"
in ba haka ba:
    grade = "F"
"""
        )
        assert s.get_variable("grade") == "C"


class TestIntermediateLoops:
    """While loops"""

    def test_while_loop(self):
        """Basic while loop"""
        s = ReplSession()
        s.execute(
            """
count = 0
total = 0
kadai count < 5:
    total = total + count
    count = count + 1
"""
        )
        assert s.get_variable("count") == 5
        assert s.get_variable("total") == 10  # 0+1+2+3+4

    def test_while_with_break_condition(self):
        """While loop with early termination condition"""
        s = ReplSession()
        s.execute(
            """
x = 0
found = 0
kadai x < 100:
    idan x == 50:
        found = x
    x = x + 10
"""
        )
        assert s.get_variable("found") == 50

    def test_nested_loop_structure(self):
        """Nested control structures"""
        s = ReplSession()
        s.execute(
            """
outer = 0
inner_sum = 0
kadai outer < 3:
    inner = 0
    kadai inner < 2:
        inner_sum = inner_sum + 1
        inner = inner + 1
    outer = outer + 1
"""
        )
        assert s.get_variable("inner_sum") == 6  # 3*2


class TestIntermediateScope:
    """Variable scope within functions"""

    def test_function_parameter_scope(self):
        """Function parameters are local to function"""
        s = ReplSession()
        s.execute(
            """
aiki modify(x):
    x = 999
    mayar x
"""
        )
        s.execute("value = 10")
        s.execute("result = modify(value)")
        assert s.get_variable("value") == 10  # unchanged
        assert s.get_variable("result") == 999

    def test_function_uses_global_variable(self):
        """Function can read (but not modify assignment-wise) global variables"""
        s = ReplSession()
        s.execute("global_x = 50")
        s.execute(
            """
aiki use_global():
    mayar global_x * 2
"""
        )
        r = s.execute("result = use_global()")
        assert r.success
        assert s.get_variable("result") == 100
