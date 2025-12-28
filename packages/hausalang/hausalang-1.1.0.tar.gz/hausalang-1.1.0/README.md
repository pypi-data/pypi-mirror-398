# Hausalang: A Beginner-Friendly Programming Language

A simple, educational Hausa-inspired programming language designed for beginners to learn programming concepts in a familiar language context.

## 🚀 Try It Now

**[Open Hausalang Web Playground](https://hausalang.replit.dev)** - No installation required, code directly in your browser!

## Features

### Core Language Constructs

- **Variables & Assignment**: Store and manipulate values
  ```hausa
  suna = "Fatima"
  adadi = 42
  ```

- **Output (rubuta)**: Print values to console
  ```hausa
  rubuta "Sannu Duniya"  # print string
  rubuta suna            # print variable
  rubuta 3 + 4           # print expression result
  ```

- **Conditionals (idan / in ba haka ba)**: Control program flow with if/else
  ```hausa
  idan x > 10:
      rubuta "x is greater than 10"
  in ba haka ba:
      rubuta "x is 10 or less"
  ```

- **Elif (idan ... kuma)**: Chain conditional checks
  ```hausa
  idan x > 10 kuma:
      rubuta "greater than 10"
  idan x == 10 kuma:
      rubuta "equals 10"
  in ba haka ba:
      rubuta "less than 10"
  ```

- **Comments**: Ignore code for documentation (# outside strings)
  ```hausa
  # This is a comment
  suna = "Ali"  # inline comment
  ```

- **Arithmetic Expressions**: Evaluate mathematical operations with proper precedence
  ```hausa
  rubuta 2 + 3 * 4      # prints 14 (order of operations respected)
  rubuta (2 + 3) * 4    # prints 20
  ```

- **String Concatenation**: Combine strings with +
  ```hausa
  greet = "Sannu " + "Fatima"
  rubuta greet          # prints "Sannu Fatima"
  ```

- **String Repetition**: Repeat strings with *
  ```hausa
  rubuta "ha" * 3       # prints "hahaha"
  ```

- **Comparisons**: Test values with ==, !=, >, <, >=, <=
  ```hausa
  idan x == 5:
      rubuta "x is five"
  ```

- **Functions (aiki)**: Define reusable code blocks with parameters
  ```hausa
  aiki add(a, b):
      mayar a + b

  result = add(3, 4)
  rubuta result         # prints 7
  ```

- **Return (mayar)**: Exit a function with a value
  ```hausa
  aiki greet(name):
      rubuta "Sannu " + name

  aiki multiply(a, b):
      mayar a * b
  ```

- **Scope**: Variables defined in functions are isolated from global scope
  ```hausa
  x = 10
  aiki change_x(n):
      x = n                 # local x, doesn't affect global
      mayar x

  result = change_x(20)
  rubuta x                # still prints 10
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hausalang.git
   cd hausalang
   ```

2. Create and activate a virtual environment (optional):
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate      # On Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Run a program:
```bash
python main.py examples/hello.ha
```

### Run all example tests:
```bash
python test_all.py
```

### Run pytest tests:
```bash
pytest -q
```

### Run the web playground locally:
```bash
python web_server.py
```
Then visit: **http://localhost:8000/static/**

## Developer Setup

### Install development dependencies:
```bash
pip install -r dev-requirements.txt
```

### Set up pre-commit hooks (optional but recommended):
```bash
pre-commit install
pre-commit run --all-files  # Run checks once
```

### Format and lint code:
```bash
black .                      # Format with Black
ruff check . --fix          # Lint and auto-fix with Ruff
mypy core/                  # Type check core modules
```

### Run tests with coverage:
```bash
coverage run -m pytest
coverage report
```

### Build and run with Docker (optional):
```bash
docker-compose up
```
Then visit: **http://localhost:8000/static/**

## Deployment

### Deploy to Replit (Free, Recommended)

1. Go to [replit.com](https://replit.com)
2. Click "Create" → "Import from GitHub"
3. Paste: `https://github.com/yourusername/hausalang`
4. Click "Import"
5. Click "Run"

Your playground is now live with a shareable URL!

### Deploy to Heroku

```bash
pip install gunicorn
heroku create your-app-name
git push heroku main
```

## Example Programs

### Hello World
```hausa
rubuta "Sannu Duniya"
```

### Variables
```hausa
suna = "Nura"
rubuta "Sannu " + suna
```

### Conditionals
```hausa
x = 15
idan x > 10:
    rubuta "greater than 10"
in ba haka ba:
    rubuta "10 or less"
```

### Functions
```hausa
aiki add(a, b):
    mayar a + b

suna = "Fatima"
aiki greet(n):
    rubuta "Sannu " + n

greet(suna)
res = add(3, 4)
rubuta res
```

### Arithmetic
```hausa
rubuta 10 + 5       # 15
rubuta 10 - 3       # 7
rubuta 5 * 4        # 20
rubuta 20 / 4       # 5.0
rubuta (2 + 3) * 4  # 20
```

## Implementation Notes

### Architecture
- **core/interpreter.py**: Main execution engine with expression parsing (shunting-yard algorithm)
- **core/executor.py**: Command execution (rubuta/print)
- **core/lexer.py**: Tokenization and comment stripping helpers
- **core/perser.py**: Simple parsing utilities for function signatures and arguments
- **tests/**: Pytest test suite

### Error Handling
Errors are reported bilingually in Hausa and English for clarity:
```
kuskure: sunan variable mara kyau -> 123x (error: invalid variable name -> 123x)
```

### Expression Evaluation
The interpreter uses the shunting-yard algorithm to convert infix expressions to postfix notation for evaluation, respecting operator precedence:
- Multiplication and division: precedence 2
- Addition and subtraction: precedence 1
- Parentheses for explicit grouping

### Block Scoping
Indentation determines block membership. Variables are global unless inside a function (which creates local scope).

## File Structure
```
hausalang/
├── main.py                    # Entry point
├── core/
│   ├── __init__.py
│   ├── interpreter.py         # Main interpreter logic
│   ├── executor.py            # Command execution
│   ├── lexer.py               # Tokenization helpers
│   └── perser.py              # Parsing helpers
├── examples/                  # Example programs
│   ├── hello.ha
│   ├── variables.ha
│   ├── if.ha
│   ├── else.ha
│   ├── comparisons.ha
│   ├── arithmetic.ha
│   ├── comments.ha
│   ├── functions.ha
│   └── elif_demo.ha
├── tests/                     # Pytest test suite
│   ├── test_comments.py
│   ├── test_functions.py
│   └── test_elif.py
├── test_all.py               # Example runner
├── requirements.txt          # Dependencies
├── pytest.ini                # Pytest configuration
└── README.md                 # This file
```

## Limitations & Future Work

### Current Limitations
- No loops (for/while)
- No lists/arrays
- No dictionaries/maps
- No imports or modules
- No exception handling
- Limited string operations (no slicing, indexing)
- No multiple return values
- Single-threaded execution

### Planned Features
- Loop constructs (kaie/repeat for loops)
- List/array support (jerin)
- Dictionary support
- String operations (slicing, indexing, methods)
- Exception handling (try/except)
- Module system
- Type hints (optional)
- Performance optimizations

## Testing

Run the pytest suite:
```bash
pytest -q
```

Run individual tests:
```bash
pytest tests/test_functions.py -v
```

Run example programs:
```bash
python test_all.py
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Author

Built as an educational project to make programming more accessible in Hausa.

---

**Status**: Alpha - Core features implemented, expanding toward a complete beginner-friendly language.

idan suna == "nura":
    rubuta "Sannu nura"

idan suna == "ali":
    rubuta "Wani jiya"
```

Use `in ba haka ba` (else) for alternate paths:

```
a = 5

idan a > 10:
    rubuta "A big"

in ba haka ba:
    rubuta "A small"
```

### Comparison Operators

- `==` — equal
- `!=` — not equal
- `>` — greater than
- `<` — less than
- `>=` — greater than or equal
- `<=` — less than or equal

Examples:

```
idan a > b:
    rubuta "a is bigger"

idan x != 0:
    rubuta "x is nonzero"
```

### Variable Names

Variable names must:
- Start with a letter (a–z, A–Z) or underscore (_)
- Contain only letters, digits (0–9), and underscores

Valid: `suna`, `_name`, `age2`, `NAME`

Invalid: `1suna`, `suna-name`, `name!`

## Examples

The `examples/` folder contains sample programs:

- `examples/hello.ha` — prints a greeting
- `examples/variables.ha` — variable assignment and printing
- `examples/if.ha` — simple `idan` (if) usage
- `examples/else.ha` — demonstrates `in ba haka ba` (else)
- `examples/comparisons.ha` — numbers and various comparison operators
- `examples/badvar.ha` — shows invalid variable name error handling
- `examples/arithmetic.ha` — arithmetic expressions and precedence

## Error Messages

Errors are displayed in Hausa with English hints to help learners:

```
kuskure: sunan variable mara kyau -> 1suna (error: invalid variable name -> 1suna)
```

This dual format supports learning while building vocabulary in both languages.

## Implementation Notes

- **Interpreter**: A single-pass line-based interpreter written in Python.
- **Parsing**: Simple regex and string-based parsing; no external dependencies.
- **Indentation**: Blocks (if/else bodies) use 4-space indentation, Python-style.
- **Bilingual Errors**: All error messages include Hausa and English for accessibility.

## Project Structure

```
.
├── main.py                    # Entry point
├── core/
│   ├── __init__.py
│   ├── interpreter.py         # Main interpreter loop
│   ├── executor.py            # Command execution (rubuta, etc.)
│   ├── lexer.py               # (Placeholder for future tokenizer)
│   └── perser.py              # (Placeholder for future parser)
├── examples/
│   ├── hello.ha
│   ├── variables.ha
│   ├── if.ha
│   ├── else.ha
│   ├── comparisons.ha
│   └── badvar.ha
└── README.md
```

## Future Enhancements

- Arithmetic operations (+, -, *, /)
- String concatenation
- Loops (while, for)
- Functions and procedures
- Comments
- Nested blocks
- More built-in commands
- A proper lexer and parser (currently in `core/lexer.py` and `core/perser.py`)

## Contributing

Hausalang is an educational project. When contributing:

1. Keep the language simple and readable for beginners.
2. Prioritize clear error messages in both Hausa and English.
3. Maintain backward compatibility unless explicitly changing the design.
4. Test all new features with example `.ha` files.

## License

MIT (modify and use freely for educational purposes).
