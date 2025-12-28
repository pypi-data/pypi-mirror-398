# Hausalang v1.1 Release Notes

**Release Date:** December 25, 2025
**Status:** Production Ready ✅

## Overview

Hausalang v1.1 introduces a production-grade error reporting system (`ContextualError`), adds missing language operators (modulo `%`, unary `+/-`), restructures the package for proper Python distribution, and maintains full backward compatibility with v1.0 programs.

**All 180 pytest tests passing. Audit phases 1–5 complete (lexical, grammar, error system, backward-compatibility, stability & safety).**

---

## Major Changes

### 1. Enhanced Error Reporting (v1.1 ErrorKind System)

**New:** `ContextualError` — a structured, machine-readable, human-friendly error type.

**Features:**
- **Formal ErrorKind hierarchy:** 30+ error kinds organized by stage (lexical, parse, runtime/name/type/value, infrastructure, internal).
- **Precise location tracking:** `SourceLocation` with file path, line, column.
- **Diagnostic frames:** Stackable context (KvFrame, WithValueFrame, WithExpectedFrame, WithSuggestionFrame).
- **Safe logging:** Values capped at 50 chars; secrets redacted (only strict prefixes: `sk_`, `pk_`, `ak_` and long-form keys detected).
- **JSON-serializable:** `to_dict()`, `to_json()`, `from_json()` for APIs and logging.
- **Deterministic error IDs:** Hash of `kind + location` for deduplication.
- **Backward compatible:** All `ContextualError` instances are also instances of appropriate builtin exceptions (e.g., `isinstance(e, SyntaxError)` is True for lexical/parse errors).

**Example:**
```python
try:
    interpret_program("rubuta x")
except NameError as e:  # Also a ContextualError!
    print(e.kind)           # ErrorKind.UNDEFINED_VARIABLE
    print(e.location)       # <input>:1:0
    print(e.to_json())      # Full structured data
```

### 2. Language Operators

**Added:**
- **Modulo operator (`%`):** Arithmetic modulo (e.g., `7 % 3 == 1`).
- **Unary operators (`+`, `-`):** Unary plus and minus (e.g., `-x`, `+3`).

**Implementation:**
- Lexer recognizes `%` operator.
- Parser correctly precedences `%` with `*` and `/`.
- Interpreter evaluates unary and modulo operations.

### 3. Package Restructure

**Before:** Flat namespace package (ambiguous imports, no proper distribution).
**After:** Proper Python package structure:
```
hausalang/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── lexer.py
│   ├── parser.py
│   ├── interpreter.py
│   ├── errors.py
│   ├── formatters.py
│   └── executor.py
├── repl/
│   ├── __init__.py
│   ├── session.py
│   ├── directives.py
│   └── input_handler.py
```

**Benefits:**
- Installable with `pip install -e .` (editable).
- Clear namespace hierarchy.
- Supports modern Python packaging tools.

### 4. Bug Fixes & Improvements

- **Backward-compatibility fix:** Dynamic exception subclassing ensures `ContextualError` inherits from stdlib exceptions (SyntaxError, NameError, TypeError, ValueError, ZeroDivisionError) based on error kind. Existing code using `except SyntaxError:` now correctly catches Hausalang lexical/parse errors.
- **All relative imports:** Internal package imports use relative paths (`from . import ...`), no absolute imports.
- **Code formatting:** Black, ruff, and pre-commit hooks enforced across codebase.

---

## Testing & Validation

**Test Suite:** 180 pytest tests, all passing.

**Audit Results:**
| Phase | Category | Result | Notes |
|-------|----------|--------|-------|
| 1 | Lexical & Grammar | ✅ Pass | Identifiers, keywords, strings, operators, indentation, functions, conditionals, loops all correct |
| 2 | Error System | ✅ Pass (fixed) | ErrorKind, SourceLocation, context_frames, help, JSON-serialization verified |
| 3 | Backward Compatibility | ✅ Pass (fixed) | v1.0 programs run unchanged; exception inheritance restored |
| 4 | Stability & Safety | ✅ Pass | JSON round-trip, deterministic IDs, no path leaks, no false-positive redaction |
| 5 | Release Readiness | ✅ Pass | Production-ready; recommended next steps documented |

---

## Breaking Changes

**None for v1.0 user code.** All v1.0 programs continue to execute.

**Developer-facing:** If you relied on specific exception types, note that:
- All errors are now `ContextualError` instances (but also inherit from stdlib exceptions).
- Error messages and types may differ slightly due to enhanced categorization.
- Use `e.kind` (ErrorKind enum) or `e.kind.value` (string like "lexical/unknown_symbol") for precise error type detection instead of exception class.

---

## Installation & Usage

**Install:**
```bash
pip install -e .
```

**Usage (CLI/REPL):**
```bash
python -m hausalang.repl
```

**Programmatic:**
```python
from hausalang.core.interpreter import interpret_program

try:
    interpret_program("""
aiki add(a, b):
    mayar a + b

rubuta add(3, 4)
""")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'to_json'):
        print(f"Structured: {e.to_json()}")
```

---

## Migration Guide (v1.0 → v1.1)

**For end-users:**
- No changes needed. All v1.0 programs run unchanged.
- New features: modulo (`%`) and unary operators (`+`, `-`) now available.

**For developers using the interpreter:**
- Update imports: `from hausalang.core import interpret_program` (was `from core import ...`).
- Exception handling: `except SyntaxError` and `except NameError` still work (ContextualError inherits from them).
- Enhanced error handling: Use `e.kind` for structured error types, `e.to_json()` for logging, `e.location` for source tracking.

**Example (error handling):**
```python
from hausalang.core.interpreter import interpret_program
from hausalang.core.errors import ContextualError, ErrorKind

try:
    interpret_program(code)
except ContextualError as e:
    if e.kind == ErrorKind.UNDEFINED_VARIABLE:
        print(f"Variable undefined at {e.location}")
    elif isinstance(e, SyntaxError):
        print(f"Syntax error: {e.message}")
```

---

## Known Limitations & Future Work

**v1.1 Scope:**
- No infinite-loop detection (INFINITE_LOOP kind defined but not implemented).
- No resource limits (stack depth, memory usage).
- No type annotations in the language itself.
- No module/import system.

**Recommended for v1.2:**
- Implement infinite-loop detection and resource limits.
- Add deterministic short error IDs (hash prefix) and canonical schema.
- Extend language with basic type annotations or assertions.
- Add optional import system for code reuse.

---

## Contributors & Thanks

**Core Team:**
- Hausalang development team.

**QA & Validation:**
- Comprehensive audit suite (5 phases, 180+ tests, custom audit scripts).
- Pre-commit hooks (Black, ruff, end-of-file fixer, trailing-whitespace).

---

## Support & Feedback

- **Issues:** Report via GitHub Issues.
- **Discussions:** Community feedback welcome.
- **Documentation:** See [INTERPRETER_DESIGN.md](INTERPRETER_DESIGN.md), [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md).

---

## License

Hausalang is [Licensed](LICENSE) under [your license here].

---

**Enjoy Hausalang v1.1! 🎉**
