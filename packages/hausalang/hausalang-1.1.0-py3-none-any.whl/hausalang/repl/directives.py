"""Directive processor for REPL Phase 2.

Provides implementations for :vars, :funcs, :history, :load, :clear, :save, :info, :help
"""

from __future__ import annotations

from typing import Optional
from hausalang.repl.session import ReplSession


class DirectiveProcessor:
    def __init__(self, session: ReplSession):
        self.session = session

    def process(self, line: str) -> Optional[str]:
        """Process a directive line (starting with ':'). Returns output string or None."""
        parts = line.strip().split()
        if not parts:
            return None
        cmd = parts[0][1:]
        args = parts[1:]

        if cmd in ("exit", "quit"):
            return "__EXIT__"

        if cmd == "vars":
            vars_dict = self.session.list_variables()
            if not vars_dict:
                return "No variables defined."
            out_lines = [f"{k} = {repr(v)}" for k, v in vars_dict.items()]
            return "\n".join(out_lines)

        if cmd == "funcs":
            funcs = self.session.list_functions()
            if not funcs:
                return "No functions defined."
            out_lines = [f"{k}()" for k in funcs.keys()]
            return "\n".join(out_lines)

        if cmd == "history":
            n = 10
            if args:
                try:
                    n = int(args[0])
                except Exception:
                    n = 10
            hist = self.session.get_history(limit=n)
            if not hist:
                return "No history."
            out_lines = [f"{i+1}: {h}" for i, h in enumerate(hist)]
            return "\n".join(out_lines)

        if cmd == "clear":
            self.session.clear_state()
            return "State cleared."

        if cmd == "load":
            if not args:
                return "Usage: :load <file>"
            # Allow file paths with spaces by joining remaining args
            path = " ".join(args)
            try:
                count = self.session.load_file(path)
                return f"Loaded: {path} ({count} statements)"
            except FileNotFoundError:
                return f"File not found: {path}"
            except Exception as e:
                return f"Error loading file: {e}"

        if cmd == "save":
            if not args:
                return "Usage: :save <history_file>"
            # Allow paths with spaces
            path = " ".join(args)
            try:
                self.session.save_history_to_file(path)
                return f"History saved to {path}"
            except Exception as e:
                return f"Error saving history: {e}"

        if cmd == "info":
            if not args:
                return "Usage: :info <name>"
            name = args[0]
            if self.session.variable_exists(name):
                v = self.session.get_variable(name)
                return f"{name}: {repr(v)}"
            if self.session.function_exists(name):
                return f"Function {name}() defined"
            return f"No such name: {name}"

        if cmd == "help":
            return ":vars, :funcs, :history [N], :load <file>, :save <file>, :clear, :info <name>, :exit"

        return f"Unknown directive: :{cmd}"
