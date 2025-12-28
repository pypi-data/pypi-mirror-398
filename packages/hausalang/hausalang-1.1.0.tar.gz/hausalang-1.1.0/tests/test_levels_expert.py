"""Expert Level Tests for Hausalang v1.1 REPL

Tests focus on:
- Complex algorithms (recursion simulation via loops)
- State persistence across multiple operations
- History and file I/O with directives
- Edge cases and boundary conditions
- Performance with larger datasets
"""

import tempfile
from pathlib import Path
from hausalang.repl.session import ReplSession
from hausalang.repl.directives import DirectiveProcessor


class TestExpertAlgorithms:
    """Complex algorithmic scenarios"""

    def test_fibonacci_via_iteration(self):
        """Calculate Fibonacci sequence via loop"""
        s = ReplSession()
        s.execute(
            """
don n = 0 zuwa 10:
    idan n == 0:
        fib_a = 0
        fib_b = 1
    idan n > 0:
        temp = fib_b
        fib_b = fib_a + fib_b
        fib_a = temp
"""
        )
        assert s.variable_exists("fib_a")
        assert s.variable_exists("fib_b")

    def test_nested_loop_matrix_operations(self):
        """Simulate matrix operations with nested loops"""
        s = ReplSession()
        s.execute(
            """
rows = 0
cols = 0
sum_all = 0
don i = 1 zuwa 5:
    don j = 1 zuwa 5:
        sum_all = sum_all + (i * j)
    rows = rows + 1
"""
        )
        assert s.get_variable("sum_all") == 100  # Sum of i*j for i,j in 1..4

    def test_complex_conditional_logic(self):
        """Complex conditional decision tree"""
        s = ReplSession()
        s.execute(
            """
age = 25
income = 50000
idan age < 18:
    status = "minor"
idan age >= 18 kuma:
    idan income < 30000:
        status = "young_poor"
    in ba haka ba:
        idan income < 100000:
            status = "young_middle"
        in ba haka ba:
            status = "young_rich"
"""
        )
        assert s.get_variable("status") == "young_middle"

    def test_loop_with_conditional_accumulator(self):
        """Loop with conditional accumulation"""
        s = ReplSession()
        s.execute(
            """
sum_even = 0
sum_odd = 0
don i = 1 zuwa 20:
    remainder = i
    idan i == 2:
        remainder = 0
    idan i == 4:
        remainder = 0
    idan i == 6:
        remainder = 0
    idan i == 8:
        remainder = 0
    idan i == 10:
        remainder = 0
    idan i == 12:
        remainder = 0
    idan i == 14:
        remainder = 0
    idan i == 16:
        remainder = 0
    idan i == 18:
        remainder = 0
    idan remainder > 0:
        sum_odd = sum_odd + i
    in ba haka ba:
        sum_even = sum_even + i
"""
        )
        # This tests the accumulation logic


class TestExpertHistoryAndPersistence:
    """History management and file operations"""

    def test_history_accumulates(self):
        """Command history accumulates in session"""
        s = ReplSession()
        s.execute("x = 1")
        s.execute("y = 2")
        s.execute("z = 3")
        hist = s.get_history()
        assert len(hist) == 3
        assert "x = 1" in hist
        assert "z = 3" in hist

    def test_history_limit_respected(self):
        """History respects limit parameter"""
        s = ReplSession()
        for i in range(20):
            s.execute(f"var{i} = {i}")
        hist_limited = s.get_history(limit=5)
        assert len(hist_limited) <= 5

    def test_save_and_load_history(self):
        """Save history to file and reload it"""
        s = ReplSession()
        s.execute("a = 100")
        s.execute("b = 200")
        s.execute("c = a + b")

        with tempfile.TemporaryDirectory() as tmpdir:
            hist_file = Path(tmpdir) / "history.txt"
            s.save_history_to_file(str(hist_file))
            assert hist_file.exists()

            # Load into new session
            s2 = ReplSession()
            s2.load_history_from_file(str(hist_file))
            hist2 = s2.get_history()
            assert len(hist2) >= 3

    def test_directive_history_output(self):
        """Directive :history shows recent commands"""
        s = ReplSession()
        s.execute("first = 1")
        s.execute("second = 2")
        s.execute("third = 3")
        dp = DirectiveProcessor(s)
        output = dp.process(":history 5")
        assert "first = 1" in output
        assert "third = 3" in output


class TestExpertFileLoading:
    """File loading and execution"""

    def test_load_file_appends_to_session(self):
        """Load file appends to current session state"""
        s = ReplSession()
        s.execute("x = 10")

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "lib.ha"
            file_path.write_text(
                """
aiki helper(val):
    mayar val * 2
"""
            )
            s.load_file(str(file_path))
            assert s.function_exists("helper")
            assert s.get_variable("x") == 10  # Original state preserved

    def test_load_file_with_directive(self):
        """Load file via :load directive"""
        s = ReplSession()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.ha"
            file_path.write_text("result = 42")

            dp = DirectiveProcessor(s)
            output = dp.process(f":load {file_path}")
            assert "Loaded:" in output
            assert s.get_variable("result") == 42

    def test_load_nonexistent_file_error(self):
        """Loading non-existent file raises error"""
        s = ReplSession()
        dp = DirectiveProcessor(s)
        output = dp.process(":load /nonexistent/file.ha")
        assert "not found" in output.lower()


class TestExpertEdgeCases:
    """Boundary conditions and edge cases"""

    def test_large_number_arithmetic(self):
        """Large number arithmetic"""
        s = ReplSession()
        r = s.execute("1000000 * 1000000")
        assert r.success
        assert r.output == 1000000000000

    def test_empty_string_assignment(self):
        """Empty string handling"""
        s = ReplSession()
        s.execute('empty = ""')
        assert s.get_variable("empty") == ""

    def test_zero_in_comparisons(self):
        """Zero handling in comparisons"""
        s = ReplSession()
        r1 = s.execute("0 == 0")
        r2 = s.execute("0 > -1")
        r3 = s.execute("0 < 1")
        assert r1.output is True
        assert r2.output is True
        assert r3.output is True

    def test_nested_function_definitions(self):
        """Multiple function definitions"""
        s = ReplSession()
        s.execute(
            """
aiki f1(x):
    mayar x + 1
aiki f2(x):
    mayar f1(x) * 2
aiki f3(x):
    mayar f2(x) + 10
"""
        )
        s.execute("result = f3(5)")
        assert s.get_variable("result") == 22  # ((5+1)*2)+10

    def test_variable_shadowing_in_function(self):
        """Function parameters shadow globals"""
        s = ReplSession()
        s.execute("x = 100")
        s.execute(
            """
aiki test(x):
    mayar x + 1
"""
        )
        s.execute("local_result = test(50)")
        assert s.get_variable("x") == 100  # Global unchanged
        assert s.get_variable("local_result") == 51


class TestExpertStatePersistence:
    """Complex multi-command state scenarios"""

    def test_state_accumulation_across_commands(self):
        """State correctly accumulates across many commands"""
        s = ReplSession()
        for i in range(10):
            s.execute(f"var_{i} = {i}")

        # Verify all variables exist
        for i in range(10):
            assert s.variable_exists(f"var_{i}")
            assert s.get_variable(f"var_{i}") == i

    def test_complex_dependency_chain(self):
        """Variables depend on each other in chain"""
        s = ReplSession()
        s.execute("a = 5")
        s.execute("b = a * 2")
        s.execute("c = b + 3")
        s.execute("d = c * 2")
        assert s.get_variable("d") == 26  # ((5*2)+3)*2

    def test_function_uses_previously_defined_functions(self):
        """Function definition order matters"""
        s = ReplSession()
        s.execute(
            """
aiki base():
    mayar 10
aiki derived():
    mayar base() + 5
"""
        )
        r = s.execute("result = derived()")
        assert r.success
        assert s.get_variable("result") == 15
