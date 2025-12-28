"""REPL session management for Hausalang (Phase 1 core loop).

Minimal implementation:
- Persistent `Interpreter` instance
- `execute(source: str)` method to run one statement or multi-line block
- Expression evaluation returns value (printed by REPL normally)
- ContextualError caught and formatted using `core.formatters.format_pretty`

This file intentionally keeps Phase 1 scope small and doesn't modify v1.0 core.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

from ..core.lexer import tokenize_program
from ..core import parser
from ..core.interpreter import Interpreter
from ..core.errors import ContextualError
from ..core.formatters import format_pretty


@dataclass
class ExecutionResult:
    success: bool
    output: Optional[Any] = None
    error: Optional[ContextualError] = None
    elapsed_ms: float = 0.0


class ReplSession:
    """Persistent REPL session (Phase 1).

    - Uses a single `Interpreter()` instance (`self.interpreter`) and its
      `global_env` to persist variables and functions across commands.
    - `execute()` will parse the given source and either evaluate an
      expression (returning its value) or execute statements (assign/define/print).
    """

    def __init__(self, use_colors: Optional[bool] = None):
        self.interpreter = Interpreter()
        self.history: list[str] = []
        self.command_count = 0
        # auto-detect color support
        if use_colors is None:
            self.use_colors = sys.stdout.isatty()
        else:
            self.use_colors = bool(use_colors)

    def execute(self, source: str) -> ExecutionResult:
        """Execute a source string (single- or multi-line) in the session.

        Returns an ExecutionResult. Errors are returned in the result.error
        (not re-raised), to allow callers (including interactive loop) to
        format/display them and continue the session.
        """
        start = time.time()
        self.command_count += 1
        self.history.append(source)

        # Quick directive handling (Phase 1: only :exit recognized by caller)
        s = source.strip()
        if not s:
            return ExecutionResult(success=True, output=None, elapsed_ms=0.0)

        try:
            tokens = tokenize_program(source)
            program = parser.parse(tokens)

            # If program contains a single ExpressionStatement, evaluate and
            # return the expression value (REPL shows expression results by default).
            if len(program.statements) == 1 and isinstance(
                program.statements[0], parser.ExpressionStatement
            ):
                expr_stmt = program.statements[0]
                value = self.interpreter.eval_expression(
                    expr_stmt.expression, self.interpreter.global_env
                )
                elapsed = (time.time() - start) * 1000.0
                return ExecutionResult(success=True, output=value, elapsed_ms=elapsed)

            # Otherwise execute the program (assign/define/print). `interpret`
            # uses the persistent interpreter and its global_env.
            self.interpreter.interpret(program)
            elapsed = (time.time() - start) * 1000.0
            return ExecutionResult(success=True, output=None, elapsed_ms=elapsed)

        except ContextualError as ce:
            # Return the contextual error for the caller to format/display
            elapsed = (time.time() - start) * 1000.0
            return ExecutionResult(success=False, error=ce, elapsed_ms=elapsed)

        except Exception as e:
            # As a safety net, wrap unexpected exceptions in ContextualError-like output
            # without modifying core code.
            try:
                from ..core.interpreter import _wrap_runtime_error

                ce = _wrap_runtime_error(e, None)
            except Exception:
                # Fallback: create an internal error ContextualError with a safe kind
                ce = ContextualError(
                    kind=None,
                    message=str(e),
                    location=parser.SourceLocation("<stdin>", 1, 0),
                    source=e,
                )
            elapsed = (time.time() - start) * 1000.0
            return ExecutionResult(success=False, error=ce, elapsed_ms=elapsed)

    def format_result(self, result: ExecutionResult) -> str:
        """Format ExecutionResult for display in interactive REPL.

        Phase 1 uses `format_pretty` for ContextualError and simple str() for values.
        """
        if result.success:
            if result.output is None:
                return ""
            return repr(result.output)
        else:
            # Format the ContextualError nicely
            if result.error:
                return format_pretty(result.error, use_colors=self.use_colors)
            return "Error: (unknown)\n"

    # Helpers to inspect session state for tests and UI
    def get_variable(self, name: str) -> Any:
        return self.interpreter.global_env.get_variable(name)

    def variable_exists(self, name: str) -> bool:
        return name in self.interpreter.global_env.variables

    def list_variables(self) -> dict:
        return dict(self.interpreter.global_env.variables)

    def function_exists(self, name: str) -> bool:
        return self.interpreter.global_env.function_exists(name)

    def list_functions(self) -> dict:
        return dict(self.interpreter.global_env.functions)

    # -------------------------
    # Session management helpers
    # -------------------------
    def clear_state(self) -> None:
        """Reset the session state (new Interpreter and empty history).

        This preserves the REPL session object but clears all variables and
        functions (useful for `:clear` directive).
        """
        self.interpreter = Interpreter()
        self.history = []
        self.command_count = 0

    def load_file(self, path: str) -> int:
        """Load a .ha file and execute its contents in the current session.

        Returns the number of top-level statements executed.
        """
        # Read file and run through tokenizer/parser/interpreter
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()

        tokens = tokenize_program(src)
        program = parser.parse(tokens)
        # Execute program (appends to current environment)
        self.interpreter.interpret(program)
        return len(program.statements)

    def get_history(self, limit: int = 1000) -> list[str]:
        """Return a copy of session history (most recent last)."""
        if limit is None:
            return list(self.history)
        return list(self.history[-limit:])

    def save_history_to_file(self, file_path: str, limit: int = 1000) -> None:
        """Save in-memory history to a file (one command per line)."""
        entries = self.get_history(limit)
        with open(file_path, "w", encoding="utf-8") as f:
            for line in entries:
                f.write(line.replace("\n", "\\n") + "\n")

    def load_history_from_file(self, file_path: str) -> int:
        """Load history lines from a file into session history.

        Returns number of lines loaded.
        """
        if not file_path or not isinstance(file_path, str):
            return 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [ln.rstrip("\n").replace("\\n", "\n") for ln in f]
            self.history.extend(lines)
            return len(lines)
        except Exception:
            return 0
