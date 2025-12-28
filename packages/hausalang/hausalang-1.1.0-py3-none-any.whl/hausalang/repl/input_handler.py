"""Minimal input handler for REPL Phase 1.

This module provides a thin abstraction over `input()` and optional `readline`
history load/save. For Phase 1 we keep this simple and non-interactive-safe for
unit tests (no blocking calls during tests).
"""

from __future__ import annotations

import os

try:
    import readline  # type: ignore
except Exception:
    readline = None


HISTORY_FILE = os.path.expanduser("~/.hausalang_history")


def load_history(max_entries: int = 1000) -> None:
    if not readline:
        return
    try:
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
    except Exception:
        pass


def save_history(max_entries: int = 1000) -> None:
    if not readline:
        return
    try:
        readline.set_history_length(max_entries)
        readline.write_history_file(HISTORY_FILE)
    except Exception:
        pass


def read_prompt(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        # Treat EOF as :exit
        return ":exit"
