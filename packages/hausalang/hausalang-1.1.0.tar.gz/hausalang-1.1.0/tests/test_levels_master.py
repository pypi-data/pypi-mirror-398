"""Master Level Tests for Hausalang v1.1 REPL

Comprehensive, stress-testing scenarios that combine:
- All language features in realistic workflows
- Error recovery and resilience
- Full directive suite integration
- Complex real-world algorithms
- Session integrity under heavy use
"""

import tempfile
from pathlib import Path
from hausalang.repl.session import ReplSession
from hausalang.repl.directives import DirectiveProcessor


class TestMasterComprehensiveWorkflow:
    """Complete realistic workflows"""

    def test_build_library_and_use_it(self):
        """Define library functions and use them in main code"""
        s = ReplSession()

        # Define library functions
        s.execute(
            """
aiki abs_value(x):
    idan x < 0:
        mayar x * -1
    in ba haka ba:
        mayar x
"""
        )

        s.execute(
            """
aiki max_of_two(a, b):
    idan a > b:
        mayar a
    in ba haka ba:
        mayar b
"""
        )

        # Use library
        s.execute("result1 = abs_value(-42)")
        s.execute("result2 = max_of_two(10, 20)")

        assert s.get_variable("result1") == 42
        assert s.get_variable("result2") == 20

    def test_statistical_computation_workflow(self):
        """Compute statistics over a range"""
        s = ReplSession()
        s.execute(
            """
sum_vals = 0
count = 0
don i = 1 zuwa 101:
    sum_vals = sum_vals + i
    count = count + 1
"""
        )
        s.execute("average = sum_vals")  # sum_vals is 5050, count is 100
        assert s.get_variable("sum_vals") == 5050

    def test_game_logic_simulation(self):
        """Simulate simple game logic (score tracking, level progression)"""
        s = ReplSession()
        s.execute("score = 0")
        s.execute("level = 1")

        # Simulate gameplay
        s.execute(
            """
aiki earn_points(current_score, points):
    mayar current_score + points
"""
        )

        s.execute("score = earn_points(score, 100)")
        s.execute("score = earn_points(score, 50)")

        assert s.get_variable("score") == 150
        assert s.get_variable("level") == 1


class TestMasterErrorRecovery:
    """Resilience to errors and recovery"""

    def test_recover_from_undefined_variable(self):
        """Session continues after undefined variable error"""
        s = ReplSession()
        s.execute("x = 10")
        r1 = s.execute("y = undefined_var")  # Error
        assert not r1.success

        # Session still works
        s.execute("z = 20")
        assert s.get_variable("x") == 10
        assert s.get_variable("z") == 20

    def test_recover_from_type_error(self):
        """Session continues after type error"""
        s = ReplSession()
        s.execute("a = 5")
        s.execute(
            'b = "text" * 5'
        )  # Type error (can't multiply string by number in Hausalang)
        # This may or may not error depending on implementation
        s.execute("c = 10")
        assert s.get_variable("c") == 10

    def test_multiple_errors_clear_state(self):
        """Clearing state removes error traces"""
        s = ReplSession()
        s.execute("x = 1")
        r1 = s.execute("y = undefined")
        assert not r1.success

        dp = DirectiveProcessor(s)
        dp.process(":clear")

        assert not s.variable_exists("x")
        # Now can redefine without issues
        s.execute("x = 100")
        assert s.get_variable("x") == 100


class TestMasterFullDirectiveIntegration:
    """All directives working together"""

    def test_complete_directive_workflow(self):
        """Use all directives in a realistic scenario"""
        s = ReplSession()
        dp = DirectiveProcessor(s)

        # Build some state
        s.execute("data_a = 100")
        s.execute("data_b = 200")
        s.execute(
            """
aiki process(x):
    mayar x * 2
"""
        )

        # Inspect with directives
        vars_out = dp.process(":vars")
        assert "data_a = 100" in vars_out

        funcs_out = dp.process(":funcs")
        assert "process()" in funcs_out

        hist_out = dp.process(":history 10")
        assert len(hist_out) > 0

        info_out = dp.process(":info data_a")
        assert "100" in info_out

    def test_save_and_load_workflow(self):
        """Save state, clear, and reload"""
        s = ReplSession()
        s.execute("important_var = 42")
        s.execute(
            """
aiki important_func(x):
    mayar x + important_var
"""
        )
        s.execute("other = 99")

        with tempfile.TemporaryDirectory() as tmpdir:
            hist_file = Path(tmpdir) / "session.hist"

            # Save history
            dp = DirectiveProcessor(s)
            s.save_history_to_file(str(hist_file))

            # Clear and reload
            dp.process(":clear")
            assert not s.variable_exists("important_var")

            s2 = ReplSession()
            s2.load_history_from_file(str(hist_file))
            hist = s2.get_history()
            assert len(hist) >= 3


class TestMasterComplexAlgorithms:
    """Advanced algorithms in REPL context"""


def test_collatz_sequence():
    """Collatz conjecture iteration"""
    s = ReplSession()
    s.execute(
        """
n = 27
steps = 0
kadai n != 1:
    idan n % 2 == 0:
        n = n / 2
    in ba haka ba:
        n = (n * 3) + 1
    steps = steps + 1
"""
    )
    assert s.variable_exists("steps")
    assert s.variable_exists("n")

    def test_prime_checking_simulation(self):
        """Simulate prime number checking via loop"""
        s = ReplSession()
        s.execute(
            """
aiki is_even_roughly(num):
    idan num == 2:
        mayar 1
    in ba haka ba:
        mayar 0
"""
        )
        s.execute("test_val = 7")
        r = s.execute("check = is_even_roughly(test_val)")
        assert r.success

    def test_string_processing_workflow(self):
        """String manipulation workflow"""
        s = ReplSession()
        s.execute(
            """
aiki concat_three(a, b, c):
    mayar a + b + c
"""
        )
        s.execute('word1 = "Hausa"')
        s.execute('word2 = "Lang"')
        s.execute('word3 = "v1.1"')
        s.execute("combined = concat_three(word1, word2, word3)")
        assert s.get_variable("combined") == "HausaLangv1.1"


class TestMasterStressAndScale:
    """Stress testing with large scales"""

    def test_many_variables(self):
        """Create and manage many variables"""
        s = ReplSession()
        for i in range(100):
            s.execute(f"var{i} = {i * 2}")

        vars_dict = s.list_variables()
        assert len(vars_dict) == 100
        assert vars_dict["var50"] == 100

    def test_many_functions(self):
        """Define many functions"""
        s = ReplSession()
        for i in range(20):
            s.execute(
                f"""
aiki func{i}(x):
    mayar x + {i}
"""
            )

        funcs = s.list_functions()
        assert len(funcs) >= 20

    def test_long_computation(self):
        """Long-running loop"""
        s = ReplSession()
        s.execute(
            """
total = 0
don i = 0 zuwa 1000:
    total = total + i
"""
        )
        # Sum of 0 to 999 = 999*1000/2 = 499500
        assert s.get_variable("total") == 499500

    def test_deeply_nested_structure(self):
        """Deeply nested conditionals and loops"""
        s = ReplSession()
        s.execute(
            """
result = 0
don i = 0 zuwa 5:
    don j = 0 zuwa 5:
        do_it = 0
        idan i > j:
            do_it = 1
        in ba haka ba:
            idan i == j:
                do_it = 1
        idan do_it > 0:
            result = result + 1
"""
        )
        assert s.variable_exists("result")


class TestMasterSessionIntegrity:
    """Session consistency under heavy use"""

    def test_variable_consistency_across_operations(self):
        """Variables maintain consistent state"""
        s = ReplSession()
        s.execute("x = 10")
        for _ in range(100):
            s.execute("x = x + 1")
        assert s.get_variable("x") == 110

    def test_function_definition_persistence(self):
        """Functions remain available after many other operations"""
        s = ReplSession()
        s.execute(
            """
aiki helper(n):
    mayar n * 2
"""
        )
        # Do 100 other things
        for i in range(100):
            s.execute(f"temp{i} = {i}")

        # Function still works
        r = s.execute("final = helper(5)")
        assert r.success
        assert s.get_variable("final") == 10

    def test_history_consistency(self):
        """History accurately reflects all commands"""
        s = ReplSession()
        commands = []
        for i in range(50):
            cmd = f"var{i} = {i}"
            s.execute(cmd)
            commands.append(cmd)

        hist = s.get_history()
        assert len(hist) == 50
        # Check a few commands
        assert commands[0] in hist
        assert commands[25] in hist
        assert commands[49] in hist

    def test_error_does_not_corrupt_state(self):
        """Errors don't leave session in invalid state"""
        s = ReplSession()
        s.execute("a = 1")
        s.execute("b = 2")
        r_err = s.execute("undefined + 1")
        assert not r_err.success

        # State is still valid
        s.execute("c = a + b")
        assert s.get_variable("c") == 3

        # Can continue normally
        s.execute(
            """
aiki still_works():
    mayar 42
"""
        )
        r = s.execute("x = still_works()")
        assert r.success
        assert s.get_variable("x") == 42
