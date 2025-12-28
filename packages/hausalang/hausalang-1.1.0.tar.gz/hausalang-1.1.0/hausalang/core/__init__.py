"""
Hausalang core language implementation.

Public API for lexer, parser, interpreter, and error system.
"""

from hausalang.core.errors import ContextualError, ErrorKind, SourceLocation
from hausalang.core.interpreter import Interpreter
from hausalang.core.lexer import Token, tokenize_program
from hausalang.core.parser import Parser

__all__ = [
    "tokenize_program",
    "Parser",
    "Interpreter",
    "Token",
    "ContextualError",
    "ErrorKind",
    "SourceLocation",
]

__version__ = "1.1.0"
