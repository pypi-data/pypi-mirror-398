from typing import List, Optional, NamedTuple

from .errors import ContextualError, ErrorKind, SourceLocation


# ============================================================================
# Token Structure
# ============================================================================


class Token(NamedTuple):
    """Represents a single token from the source code."""

    type: str  # e.g., "KEYWORD", "IDENTIFIER", "STRING", "OPERATOR", etc.
    value: str  # e.g., "idan", "x", "hello", "+", etc.
    line: int  # 1-indexed line number
    column: int  # 0-indexed column number


# ============================================================================
# Keywords for Hausalang
# ============================================================================

KEYWORDS = {
    "idan": "KEYWORD_IF",
    "in": "KEYWORD_ELSE",  # 'in ba haka ba' is 3 tokens
    "ba": "KEYWORD_ELSE",  # Note: also used for "ba" in for loops
    "haka": "KEYWORD_ELSE",
    "aiki": "KEYWORD_FUNCTION",
    "mayar": "KEYWORD_RETURN",
    "rubuta": "KEYWORD_PRINT",
    "kuma": "KEYWORD_ELIF",
    "kadai": "KEYWORD_WHILE",
    "don": "KEYWORD_FOR",  # for keyword
    "zuwa": "KEYWORD_TO",  # ascending to
    "ta": "KEYWORD_STEP",  # step
    "None": "KEYWORD_NONE",  # None literal
}


# ============================================================================
# Helper Functions (Existing)
# ============================================================================


def strip_comments(s: str) -> str:
    i = 0
    while True:
        idx = s.find("#", i)
        if idx == -1:
            return s
        before = s[:idx]
        if before.count('"') % 2 == 0:
            return s[:idx].rstrip()
        i = idx + 1


def _raise_lexer_error(kind: ErrorKind, message: str, line: int, column: int) -> None:
    """
    Raise a ContextualError for lexical errors.

    The error inherits from SyntaxError for backward compatibility.

    Args:
        kind: The ErrorKind categorizing this lexical error
        message: Human-readable error description
        line: 1-indexed line number
        column: 0-indexed column number

    Raises:
        ContextualError: Always (this is the mechanism for error handling)
    """
    location = SourceLocation(
        file_path="<input>",  # Will be resolved to actual file path in main.py
        line=line,
        column=column,
    )
    error = ContextualError(
        kind=kind,
        message=message,
        location=location,
        tags={"lexical"},
    )
    raise error


def tokenize_expr(expr: str) -> Optional[List[str]]:
    """Tokenize a simple expression into a list of string tokens.

    Returns None on tokenization error.
    """
    tokens: List[str] = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c in "+-*/()":
            tokens.append(c)
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < len(expr):
                if expr[j] == '"' and expr[j - 1] != "\\":
                    break
                j += 1
            if j >= len(expr):
                return None
            tokens.append(expr[i : j + 1])
            i = j + 1
            continue
        if c.isdigit() or (c == "." and i + 1 < len(expr) and expr[i + 1].isdigit()):
            j = i
            dot = False
            while j < len(expr) and (expr[j].isdigit() or (expr[j] == "." and not dot)):
                if expr[j] == ".":
                    dot = True
                j += 1
            tokens.append(expr[i:j])
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j] == "_"):
                j += 1
            tokens.append(expr[i:j])
            i = j
            continue
        return None
    return tokens


# ============================================================================
# Full-Program Lexer
# ============================================================================


def tokenize_program(code: str) -> List[Token]:
    """Tokenize a complete Hausalang program into tokens.

    Recognizes:
    - Keywords: idan, in ba haka ba, aiki, mayar, rubuta, kuma
    - Identifiers: variable and function names
    - Strings: quoted with double quotes
    - Numbers: integers and floats
    - Operators: =, ==, !=, >, <, >=, <=, +, -, *, /, %, :
    - Indentation: INDENT/DEDENT tokens
    - Newlines and comments (stripped)
    - Parentheses: ( )

    Args:
        code: The Hausalang source code as a string.

    Returns:
        A list of Token objects.

    Raises:
        SyntaxError: If an unknown symbol or unclosed string is encountered.
    """
    tokens: List[Token] = []
    lines = code.split("\n")

    # Track indentation levels
    indent_stack = [0]

    for line_num, raw_line in enumerate(lines, start=1):
        # Remove comments (preserving logic for quoted strings)
        line = strip_comments(raw_line)

        # Skip empty lines
        if not line.strip():
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip(" "))
        if indent % 4 != 0 and line.strip():
            _raise_lexer_error(
                ErrorKind.INVALID_INDENT,
                "Indentation must be a multiple of 4 spaces",
                line_num,
                indent,
            )

        indent_level = indent // 4

        # Emit DEDENT tokens if indentation decreased
        while len(indent_stack) > 1 and indent_level < indent_stack[-1]:
            indent_stack.pop()
            tokens.append(Token("DEDENT", "", line_num, 0))

        # Emit INDENT token if indentation increased
        if indent_level > indent_stack[-1]:
            if indent_level != indent_stack[-1] + 1:
                _raise_lexer_error(
                    ErrorKind.INDENT_LEVEL_MISMATCH,
                    "Indentation increased by more than 1 level",
                    line_num,
                    indent,
                )
            indent_stack.append(indent_level)
            tokens.append(Token("INDENT", "", line_num, indent))

        # Tokenize the content of the line
        content = line.lstrip(" ")
        col = indent

        i = 0
        while i < len(content):
            c = content[i]

            # Whitespace
            if c.isspace():
                col += 1
                i += 1
                continue

            # String literals
            if c == '"':
                j = i + 1
                while j < len(content):
                    if content[j] == '"' and content[j - 1] != "\\":
                        break
                    j += 1
                if j >= len(content):
                    _raise_lexer_error(
                        ErrorKind.UNCLOSED_STRING,
                        "String literal was not closed",
                        line_num,
                        col,
                    )
                string_value = content[i : j + 1]
                tokens.append(Token("STRING", string_value, line_num, col))
                col += len(string_value)
                i = j + 1
                continue

            # Numbers (integers and floats)
            if c.isdigit() or (
                c == "." and i + 1 < len(content) and content[i + 1].isdigit()
            ):
                j = i
                dot_count = 0
                while j < len(content):
                    if content[j].isdigit():
                        pass
                    elif content[j] == ".":
                        dot_count += 1
                        if dot_count > 1:
                            _raise_lexer_error(
                                ErrorKind.INVALID_NUMBER,
                                "Invalid number format",
                                line_num,
                                col,
                            )
                    else:
                        break
                    j += 1
                number_value = content[i:j]
                tokens.append(Token("NUMBER", number_value, line_num, col))
                col += len(number_value)
                i = j
                continue

            # Identifiers and keywords
            if c.isalpha() or c == "_":
                j = i
                while j < len(content) and (content[j].isalnum() or content[j] == "_"):
                    j += 1
                word = content[i:j]

                # Check if it's a keyword
                if word in KEYWORDS:
                    token_type = KEYWORDS[word]
                    tokens.append(Token(token_type, word, line_num, col))
                else:
                    tokens.append(Token("IDENTIFIER", word, line_num, col))

                col += len(word)
                i = j
                continue

            # Multi-character operators
            if i + 1 < len(content):
                two_char = content[i : i + 2]
                if two_char in ("==", "!=", ">=", "<="):
                    tokens.append(Token("OPERATOR", two_char, line_num, col))
                    col += 2
                    i += 2
                    continue

            # Single-character operators and punctuation
            if c in "=+-*/%:()<>,":
                tokens.append(Token("OPERATOR", c, line_num, col))
                col += 1
                i += 1
                continue

            # Unknown symbol
            _raise_lexer_error(
                ErrorKind.UNKNOWN_SYMBOL,
                f"Unknown symbol '{c}'",
                line_num,
                col,
            )

        # Emit NEWLINE at end of line
        tokens.append(Token("NEWLINE", "", line_num, col))

    # Emit final DEDENT tokens
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token("DEDENT", "", len(lines), 0))

    # Emit EOF token
    tokens.append(Token("EOF", "", len(lines) + 1, 0))

    return tokens


# ============================================================================
# Example Usage and Testing
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple variable assignment and print
    example1 = """
suna = "Fatima"
rubuta suna
"""

    print("Example 1: Variable assignment and print")
    print("Code:")
    print(example1)
    print("\nTokens:")
    try:
        tokens = tokenize_program(example1)
        for tok in tokens:
            print(f"  {tok}")
    except SyntaxError as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60 + "\n")

    # Example 2: If statement with function
    example2 = """
aiki greet(name):
    rubuta "Sannu " + name
    mayar 42

x = 10
idan x > 5:
    rubuta "x is big"
in ba haka ba:
    rubuta "x is small"
"""

    print("Example 2: Function definition and if-else")
    print("Code:")
    print(example2)
    print("\nTokens:")
    try:
        tokens = tokenize_program(example2)
        for tok in tokens:
            print(f"  {tok}")
    except SyntaxError as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60 + "\n")

    # Example 3: Error case - unknown symbol
    example3 = """rubuta 5 @ 3"""

    print("Example 3: Error - unknown symbol")
    print("Code:")
    print(example3)
    print("\nTokens:")
    try:
        tokens = tokenize_program(example3)
        for tok in tokens:
            print(f"  {tok}")
    except SyntaxError as e:
        print(f"  Error: {e}")
