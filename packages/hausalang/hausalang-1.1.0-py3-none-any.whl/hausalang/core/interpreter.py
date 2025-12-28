"""
AST Interpreter for Hausalang

This module implements an interpreter that walks the Abstract Syntax Tree (AST)
produced by the parser and executes the program.

Key Design:
- Environment class manages variable scope and function definitions
- Interpreter class walks AST nodes recursively
- No raw token or line-based execution; pure AST-driven
"""

from typing import Any, Dict, Optional

from . import parser
from .lexer import tokenize_program
from .errors import (
    ContextualError,
    ErrorKind,
    SourceLocation,
)


class ReturnValue(Exception):
    """Exception used to implement return statements.

    When a return statement is executed, we raise this exception to unwind
    the call stack back to the function call site.
    """

    def __init__(self, value: Any):
        self.value = value
        super().__init__()


class Environment:
    """Manages variable scope and function definitions.

    An environment maps variable names to values and function names to
    function definitions (AST nodes). When entering a new scope (function call),
    we create a new Environment with a parent reference.
    """

    def __init__(self, parent: Optional["Environment"] = None):
        """Initialize an environment.

        Args:
            parent: The parent environment (for scope chain). None for global scope.
        """
        self.parent = parent
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, parser.Function] = {}

    def define_variable(self, name: str, value: Any) -> None:
        """Define a variable in this environment."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any:
        """Get a variable, searching parent scopes if necessary."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable(name)
        raise NameError(f"Undefined variable: {name}")

    def define_function(self, name: str, func: parser.Function) -> None:
        """Define a function in this environment."""
        self.functions[name] = func

    def get_function(self, name: str) -> parser.Function:
        """Get a function, searching parent scopes if necessary."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        raise NameError(f"Undefined function: {name}")

    def function_exists(self, name: str) -> bool:
        """Check if a function is defined."""
        if name in self.functions:
            return True
        if self.parent:
            return self.parent.function_exists(name)
        return False


class Interpreter:
    """AST Interpreter for Hausalang.

    Walks the AST and executes each node by dispatching to specialized methods.
    """

    def __init__(self):
        """Initialize the interpreter with a global environment."""
        self.global_env = Environment()

    # ========================================================================
    # Program Execution
    # ========================================================================

    def interpret(self, program: parser.Program) -> None:
        """Execute a program (AST).

        Args:
            program: The Program node from the parser.
        """
        self.execute_program(program, self.global_env)

    def execute_program(self, program: parser.Program, env: Environment) -> None:
        """Execute all statements in a program.

        Args:
            program: The Program node.
            env: The environment for execution.
        """
        for statement in program.statements:
            self.execute_statement(statement, env)

    # ========================================================================
    # Statement Execution
    # ========================================================================

    def execute_statement(self, stmt: parser.Statement, env: Environment) -> None:
        """Execute a statement.

        Dispatches to the appropriate handler based on statement type.

        Args:
            stmt: The statement to execute.
            env: The environment for execution.
        """
        if isinstance(stmt, parser.Assignment):
            self.execute_assignment(stmt, env)

        elif isinstance(stmt, parser.Print):
            self.execute_print(stmt, env)

        elif isinstance(stmt, parser.Return):
            self.execute_return(stmt, env)

        elif isinstance(stmt, parser.If):
            self.execute_if(stmt, env)

        elif isinstance(stmt, parser.While):
            self.execute_while(stmt, env)

        elif isinstance(stmt, parser.For):
            self.execute_for(stmt, env)

        elif isinstance(stmt, parser.Function):
            self.execute_function_def(stmt, env)

        elif isinstance(stmt, parser.ExpressionStatement):
            # Expression statements (like function calls) are evaluated for
            # side effects but their return value is discarded
            self.eval_expression(stmt.expression, env)

        else:
            raise RuntimeError(f"Unknown statement type: {type(stmt)}")

    def execute_assignment(self, stmt: parser.Assignment, env: Environment) -> None:
        """Execute an assignment statement.

        Evaluates the expression and stores the result in the variable.

        Args:
            stmt: The Assignment statement.
            env: The environment for execution.
        """
        value = self.eval_expression(stmt.value, env)
        env.define_variable(stmt.name, value)

    def execute_print(self, stmt: parser.Print, env: Environment) -> None:
        """Execute a print statement.

        Evaluates the expression and prints the result to stdout.

        Args:
            stmt: The Print statement.
            env: The environment for execution.
        """
        value = self.eval_expression(stmt.expression, env)
        print(value, end="")

    def execute_return(self, stmt: parser.Return, env: Environment) -> None:
        """Execute a return statement.

        Raises a ReturnValue exception to unwind back to the function call.

        Args:
            stmt: The Return statement.
            env: The environment for execution.

        Raises:
            ReturnValue: Always (this is the mechanism for return).
        """
        value = self.eval_expression(stmt.expression, env)
        raise ReturnValue(value)

    def execute_if(self, stmt: parser.If, env: Environment) -> None:
        """Execute an if/else statement.

        Evaluates the condition, then executes either the then_body or else_body.

        Args:
            stmt: The If statement.
            env: The environment for execution.
        """
        condition = self.eval_expression(stmt.condition, env)

        if self.is_truthy(condition):
            # Execute then-body
            for then_stmt in stmt.then_body:
                self.execute_statement(then_stmt, env)
        elif stmt.else_body:
            # Execute else-body (if it exists)
            for else_stmt in stmt.else_body:
                self.execute_statement(else_stmt, env)

    def execute_while(self, stmt: parser.While, env: Environment) -> None:
        """Execute a while loop.

        Re-evaluates the condition before each iteration. Executes the body
        as long as the condition remains truthy.

        Args:
            stmt: The While statement.
            env: The environment for execution.
        """
        while self.is_truthy(self.eval_expression(stmt.condition, env)):
            # Execute loop body
            for body_stmt in stmt.body:
                self.execute_statement(body_stmt, env)

    def execute_for(self, stmt: parser.For, env: Environment) -> None:
        """Execute a for loop via AST rewriting to assignment + while loop.

        For loops are internally converted to:
            1. Assignment: var = start
            2. While loop with:
               - Condition: var < end (ascending) or var > end (descending)
               - Body: original statements + increment/decrement

        This approach reuses the proven while loop implementation.

        Args:
            stmt: The For statement.
            env: The environment for execution.

        Raises:
            ValueError: If step is 0 or has invalid type.
            TypeError: If expressions don't evaluate to numbers.
        """
        # Step 1: Evaluate all for-loop expressions to values
        start_value = self.eval_expression(stmt.start, env)
        end_value = self.eval_expression(stmt.end, env)

        # Evaluate step (default to 1)
        step_value = 1
        if stmt.step is not None:
            step_value = self.eval_expression(stmt.step, env)

        # Validate step value
        if step_value == 0:
            raise ValueError("For loop step cannot be zero")
        if not isinstance(step_value, (int, float)):
            raise TypeError(f"For loop step must be numeric, got {type(step_value)}")

        # Step 2: Initialize loop variable directly
        env.define_variable(stmt.var, start_value)

        # Step 3: Determine direction and create condition + increment
        if stmt.direction == "ascending":
            # Validate step is positive for ascending
            if step_value < 0:
                raise ValueError(
                    f"For loop: ascending (zuwa) direction requires positive step, "
                    f"got {step_value}"
                )

            # Execute loop: while var < end
            while self.is_truthy(env.get_variable(stmt.var) < end_value):
                # Execute original body
                for body_stmt in stmt.body:
                    self.execute_statement(body_stmt, env)

                # Increment: var = var + step
                current = env.get_variable(stmt.var)
                env.define_variable(stmt.var, current + step_value)

        else:  # descending
            # Validate step is positive for descending (we negate it)
            if step_value < 0:
                raise ValueError(
                    f"For loop: descending (ba) direction requires positive step, "
                    f"got {step_value}"
                )

            # Execute loop: while var > end
            while self.is_truthy(env.get_variable(stmt.var) > end_value):
                # Execute original body
                for body_stmt in stmt.body:
                    self.execute_statement(body_stmt, env)

                # Decrement: var = var - step
                current = env.get_variable(stmt.var)
                env.define_variable(stmt.var, current - step_value)

    def execute_function_def(self, stmt: parser.Function, env: Environment) -> None:
        """Execute a function definition.

        Stores the function in the environment so it can be called later.

        Args:
            stmt: The Function statement.
            env: The environment for execution.
        """
        env.define_function(stmt.name, stmt)

    # ========================================================================
    # Expression Evaluation
    # ========================================================================

    def eval_expression(self, expr: parser.Expression, env: Environment) -> Any:
        """Evaluate an expression to a value.

        Args:
            expr: The expression to evaluate.
            env: The environment for execution.

        Returns:
            The result of evaluating the expression.
        """
        if isinstance(expr, parser.Number):
            return expr.value

        elif isinstance(expr, parser.String):
            return expr.value

        elif isinstance(expr, parser.NoneValue):
            return None

        elif isinstance(expr, parser.Identifier):
            return env.get_variable(expr.name)

        elif isinstance(expr, parser.BinaryOp):
            return self.eval_binary_op(expr, env)

        elif isinstance(expr, parser.UnaryOp):
            return self.eval_unary_op(expr, env)

        elif isinstance(expr, parser.FunctionCall):
            return self.eval_function_call(expr, env)

        else:
            raise RuntimeError(f"Unknown expression type: {type(expr)}")

    def eval_binary_op(self, expr: parser.BinaryOp, env: Environment) -> Any:
        """Evaluate a binary operation.

        Args:
            expr: The BinaryOp expression.
            env: The environment for execution.

        Returns:
            The result of the operation.
        """
        left = self.eval_expression(expr.left, env)
        right = self.eval_expression(expr.right, env)

        op = expr.operator

        # Arithmetic operators
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            # Integer division if both operands are integers
            if isinstance(left, int) and isinstance(right, int):
                return left // right
            return left / right

        elif op == "%":
            return left % right

        # Comparison operators
        elif op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op == ">":
            return left > right
        elif op == "<":
            return left < right
        elif op == ">=":
            return left >= right
        elif op == "<=":
            return left <= right

        else:
            raise RuntimeError(f"Unknown operator: {op}")

    def eval_unary_op(self, expr: parser.UnaryOp, env: Environment) -> Any:
        """Evaluate a unary operation.

        Args:
            expr: The UnaryOp expression.
            env: The environment for execution.

        Returns:
            The result of the operation.
        """
        operand = self.eval_expression(expr.operand, env)

        if expr.operator == "-":
            return -operand
        elif expr.operator == "+":
            return +operand
        else:
            raise RuntimeError(f"Unknown unary operator: {expr.operator}")

    def eval_function_call(self, expr: parser.FunctionCall, env: Environment) -> Any:
        """Evaluate a function call.

        Looks up the function, evaluates the arguments, creates a new environment
        for the function, executes the function body, and returns the result.

        Args:
            expr: The FunctionCall expression.
            env: The environment for execution.

        Returns:
            The return value of the function (or None if no return statement).
        """
        # Evaluate arguments
        arg_values = [self.eval_expression(arg, env) for arg in expr.arguments]

        # Look up the function
        func = env.get_function(expr.name)

        # Check argument count
        if len(arg_values) != len(func.parameters):
            raise ValueError(
                f"Function {expr.name} expects {len(func.parameters)} arguments, "
                f"got {len(arg_values)}"
            )

        # Create a new environment for the function with current environment as parent
        func_env = Environment(parent=env)

        # Bind parameters to argument values
        for param_name, arg_value in zip(func.parameters, arg_values):
            func_env.define_variable(param_name, arg_value)

        # Execute the function body
        try:
            for stmt in func.body:
                self.execute_statement(stmt, func_env)
        except ReturnValue as ret:
            # Function returned a value
            return ret.value

        # If no return statement, return None
        return None

    # ========================================================================
    # Utilities
    # ========================================================================

    def is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy in Hausalang.

        In Hausalang:
        - False, 0, "", and None are falsy
        - Everything else is truthy

        Args:
            value: The value to test.

        Returns:
            True if the value is truthy, False otherwise.
        """
        if value is False or value is None:
            return False
        if value == 0 or value == "":
            return False
        return True


# ============================================================================
# Public API
# ============================================================================


# ============================================================================
# Public API
# ============================================================================


def _wrap_runtime_error(
    exc: Exception,
    ast_node: Optional[parser.ASTNode] = None,
) -> ContextualError:
    """Wrap a runtime exception in ContextualError.

    Maps Python exceptions to ErrorKind and adds diagnostic context.
    Location extracted from AST node if available.

    Args:
        exc: The exception to wrap
        ast_node: Optional AST node where error occurred (for location)

    Returns:
        ContextualError with mapped kind, location, and context
    """
    # Determine location from AST node
    location = SourceLocation(
        file_path="<input>",  # Will be resolved in main.py
        line=ast_node.line if ast_node else 1,
        column=ast_node.column if ast_node else 0,
    )

    # Determine ErrorKind, context, and help from exception
    kind, context_frames, help_text = _infer_runtime_error_kind(exc)

    # Create ContextualError with preserved source exception
    error = ContextualError(
        kind=kind,
        message=str(exc),
        location=location,
        source=exc,  # Preserve for traceback chaining
        context_frames=context_frames,
        tags={"runtime"},
        help=help_text,
    )
    return error


def _infer_runtime_error_kind(exc: Exception) -> tuple:
    """Infer ErrorKind, context frames, and help text from exception.

    Maps Python exception types and messages to appropriate ErrorKind values.
    Builds context frames with diagnostic information.

    Args:
        exc: The exception to categorize

    Returns:
        Tuple of (ErrorKind, List[ContextFrame], Optional[help_text])
    """
    exc_str = str(exc).lower()
    context_frames = []
    help_text = None

    # NameError: Undefined variable or function
    if isinstance(exc, NameError):
        if "variable" in exc_str:
            kind = ErrorKind.UNDEFINED_VARIABLE
            help_text = "Assign a value before using the variable"
        else:
            kind = ErrorKind.UNDEFINED_FUNCTION
            help_text = "Define the function with 'aiki' before calling it"

    # ZeroDivisionError: Division by zero (before ValueError since it's more specific)
    elif isinstance(exc, ZeroDivisionError):
        kind = ErrorKind.DIVISION_BY_ZERO
        help_text = "Check that divisor is not zero"

    # ValueError: Various runtime value errors
    elif isinstance(exc, ValueError):
        if "step" in exc_str and "zero" in exc_str:
            kind = ErrorKind.ZERO_LOOP_STEP
            help_text = "Use a non-zero step value (e.g., 'ta 1')"
        elif "step" in exc_str and "positive" in exc_str:
            kind = ErrorKind.NEGATIVE_LOOP_STEP
            help_text = (
                "Ascending loops need positive step, descending need positive too"
            )
        elif "argument" in exc_str or "function" in exc_str:
            kind = ErrorKind.WRONG_ARGUMENT_COUNT
            help_text = "Check function definition for expected argument count"
        else:
            kind = ErrorKind.EMPTY_REQUIRED_VALUE
            help_text = None

    # TypeError: Type mismatches in operations
    elif isinstance(exc, TypeError):
        kind = ErrorKind.INVALID_OPERAND_TYPE
        help_text = "Ensure variable types match the operation (strings vs. numbers)"

    # RuntimeError: Unknown operators or statements
    elif isinstance(exc, RuntimeError):
        if "operator" in exc_str:
            kind = ErrorKind.UNKNOWN_OPERATOR
            help_text = "Check the operator syntax"
        elif "statement" in exc_str:
            kind = ErrorKind.UNKNOWN_STATEMENT_TYPE
            help_text = "Check statement syntax"
        else:
            kind = ErrorKind.INTERPRETER_BUG
            help_text = None

    # Fallback for unexpected exception types
    else:
        kind = ErrorKind.INTERPRETER_BUG
        help_text = f"Unexpected error: {type(exc).__name__}"

    return kind, context_frames, help_text


def interpret_program(source_code: str) -> None:
    """Parse and interpret a Hausalang program.

    This is the main entry point: takes source code, lexes it, parses it to
    produce an AST, then interprets the AST.

    All errors (lexical, parse, runtime) are wrapped in ContextualError for
    enhanced error reporting. ContextualError inherits from stdlib exceptions
    for backward compatibility.

    Args:
        source_code: The Hausalang source code as a string.

    Raises:
        ContextualError: If the code has any error (inherits from SyntaxError,
                        NameError, ValueError, etc. depending on error type)
    """
    try:
        # Lex the source code
        tokens = tokenize_program(source_code)

        # Parse tokens to produce AST
        program = parser.parse(tokens)

        # Interpret the AST
        interpreter = Interpreter()
        interpreter.interpret(program)

    except ContextualError:
        # Already wrapped by lexer or parser - re-raise as-is
        raise

    except (NameError, ValueError, TypeError, RuntimeError, ZeroDivisionError) as e:
        # Wrap runtime errors in ContextualError
        wrapped = _wrap_runtime_error(e, ast_node=None)
        raise wrapped from e

    except Exception as e:
        # Unexpected error type - wrap in internal error
        wrapped = ContextualError(
            kind=ErrorKind.INTERPRETER_BUG,
            message=f"Unexpected error in interpreter: {str(e)}",
            location=SourceLocation("<input>", 1, 0),
            source=e,
            tags={"internal", "interpreter"},
        )
        raise wrapped from e


# Backwards compatibility: older tests expect `run` to be available.
# Provide an alias so external code importing `run` continues to work.
run = interpret_program
