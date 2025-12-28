"""
Test that public API imports work correctly.

This verifies that users can import core components from hausalang.core
without needing to know the internal module structure.
"""


def test_core_public_api_imports():
    """Test that all core components can be imported from hausalang.core."""
    from hausalang.core import (
        ContextualError,
        ErrorKind,
        Interpreter,
        Parser,
        SourceLocation,
        Token,
        tokenize_program,
    )

    # Verify they are the actual classes/functions
    assert callable(tokenize_program)
    assert callable(Parser)
    assert callable(Interpreter)
    assert callable(Token)
    assert issubclass(ContextualError, Exception)
    # Verify ErrorKind is an enum with error types
    assert len(list(ErrorKind)) > 0
    assert callable(SourceLocation)


def test_all_export_in_all():
    """Test that __all__ exports are all actually available."""
    from hausalang import core

    expected_exports = [
        "tokenize_program",
        "Parser",
        "Interpreter",
        "Token",
        "ContextualError",
        "ErrorKind",
        "SourceLocation",
    ]

    for export in expected_exports:
        assert hasattr(core, export), f"Export '{export}' not found in hausalang.core"
        assert export in core.__all__, f"Export '{export}' not in __all__"


def test_version_available():
    """Test that version is available from core module."""
    from hausalang.core import __version__

    assert __version__ == "1.1.0"


def test_public_api_with_simple_program():
    """Test that the public API can execute a simple program."""
    from hausalang.core import Interpreter, Parser, tokenize_program

    code = "x = 42\nrubuta x"

    tokens = tokenize_program(code)
    assert len(tokens) > 0

    parser = Parser(tokens)
    ast = parser.parse()
    assert ast is not None

    interpreter = Interpreter()
    result = interpreter.interpret(ast)
    # Result should be None (no explicit return)
    assert result is None
