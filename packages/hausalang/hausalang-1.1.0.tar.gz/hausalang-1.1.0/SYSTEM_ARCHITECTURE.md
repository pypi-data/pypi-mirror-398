"""
HAUSALANG WITH WHILE LOOPS - SYSTEM ARCHITECTURE OVERVIEW
"""

============================================================================
COMPLETE LANGUAGE PIPELINE
============================================================================

SOURCE CODE
    ↓
    │ Lexical Analysis
    ↓
TOKEN STREAM
    ↓
    │ Syntax Analysis
    ↓
ABSTRACT SYNTAX TREE (AST)
    ↓
    │ Semantic Analysis & Execution
    ↓
OUTPUT / PROGRAM STATE


============================================================================
PHASE 1: LEXICAL ANALYSIS (Lexer)
============================================================================

Module: core/lexer.py
Size: ~330 lines
Key Components:
  - Token namedtuple (type, value, line, column)
  - KEYWORDS dictionary with all language keywords
  - tokenize_program() function

Keywords Recognized:
  ✓ "aiki"        → KEYWORD_FUNCTION
  ✓ "idan"        → KEYWORD_IF
  ✓ "in ba haka ba" → KEYWORD_ELSE (3 tokens)
  ✓ "mayar"       → KEYWORD_RETURN
  ✓ "rubuta"      → KEYWORD_PRINT
  ✓ "kadai"       → KEYWORD_WHILE ← NEW

Example Tokenization:
  Input:  "kadai x < 5: rubuta x"
  Output: [
    Token(KEYWORD_WHILE, "kadai", 1, 0),
    Token(IDENTIFIER, "x", 1, 6),
    Token(OPERATOR, "<", 1, 8),
    Token(NUMBER, "5", 1, 10),
    Token(OPERATOR, ":", 1, 11),
    Token(KEYWORD_PRINT, "rubuta", 1, 14),
    Token(IDENTIFIER, "x", 1, 21)
  ]


============================================================================
PHASE 2: PARSING (Parser)
============================================================================

Module: core/parser.py
Size: ~765 lines (was 715, +50)
Key Components:
  - 13 AST node classes (frozen dataclasses)
  - Parser class with 16+ methods
  - parse() entry point function

AST Node Classes:
  Expression Nodes:
    • Number       → Numeric literals
    • String       → String literals
    • Identifier   → Variable references
    • BinaryOp    → Binary operations
    • FunctionCall → Function invocations

  Statement Nodes:
    • Assignment   → Variable assignment
    • Print        → Print statements
    • Return       → Return statements
    • If           → If/else blocks
    • While        → While loops ← NEW
    • Function     → Function definitions
    • ExpressionStatement → Expression as statement

Parser Methods:
  • parse(tokens) → Program                  Entry point
  • parse_program() → Program                Parse all statements
  • parse_statement() → Statement            Dispatch to specific parser
  • parse_expression() → Expression          Parse expressions
  • parse_comparison() → Expression          Comparison operators
  • parse_additive() → Expression            + and - operators
  • parse_multiplicative() → Expression      * and / operators
  • parse_primary() → Expression             Literals and identifiers
  • parse_assignment() → Assignment          Variable assignment
  • parse_print() → Print                    Print statement
  • parse_return() → Return                  Return statement
  • parse_if() → If                          If/else statement
  • parse_while() → While                    While loop ← NEW
  • parse_function() → Function              Function definition
  • parse_block() → List[Statement]          Parse indented block

Example Parse Tree:
  Input: "x = 0\nkadai x < 5:\n    rubuta x\n    x = x + 1"

  Program([
    Assignment(
      name="x",
      value=Number(0)
    ),
    While(
      condition=BinaryOp(
        left=Identifier("x"),
        operator="<",
        right=Number(5)
      ),
      body=[
        Print(Identifier("x")),
        Assignment(
          name="x",
          value=BinaryOp(
            left=Identifier("x"),
            operator="+",
            right=Number(1)
          )
        )
      ]
    )
  ])


============================================================================
PHASE 3: INTERPRETATION (Interpreter)
============================================================================

Module: core/interpreter.py
Size: ~407 lines (was 392, +15)
Key Components:
  - ReturnValue exception (16 lines)
  - Environment class (51 lines)
  - Interpreter class (340+ lines)

ReturnValue Exception:
  Purpose: Implement return statements via exception
  Usage: Raised by execute_return(), caught by eval_function_call()

Environment Class:
  Purpose: Manage variable scope and function definitions
  Fields:
    - parent: Optional[Environment]      Scope chain
    - variables: Dict[str, Any]          Variable bindings
    - functions: Dict[str, Function]     Function definitions
  Methods:
    - define_variable(name, value)       Create/update variable
    - get_variable(name)                 Lookup variable (with parent chain)
    - define_function(name, func)        Define function
    - get_function(name)                 Lookup function
    - function_exists(name)              Check if function exists

Interpreter Class:
  Purpose: Execute AST by walking nodes recursively
  Main Methods:
    - interpret(program)                 Entry point
    - execute_program(program, env)      Execute all statements
    - execute_statement(stmt, env)       Dispatch to statement handler
    - execute_assignment(stmt, env)      Variable assignment
    - execute_print(stmt, env)           Print output
    - execute_return(stmt, env)          Return from function
    - execute_if(stmt, env)              Conditional branching
    - execute_while(stmt, env)           Loop execution ← NEW
    - execute_function_def(stmt, env)    Function definition
    - eval_expression(expr, env)         Evaluate expressions
    - eval_binary_op(expr, env)          Binary operations
    - eval_function_call(expr, env)      Function invocation
    - is_truthy(value)                   Truthiness test

Statement Execution Dispatch:
  isinstance(stmt) → Handler Method
  ────────────────────────────────────
  Assignment      → execute_assignment
  Print           → execute_print
  Return          → execute_return
  If              → execute_if
  While           → execute_while ← NEW
  Function        → execute_function_def
  ExpressionStatement → eval_expression

Example Execution:
  AST: While(condition=x<5, body=[...])
  ↓
  1. Evaluate condition: x < 5
  2. Check is_truthy() result
  3. If true:
     a. Execute body statements
     b. Go to step 1
  4. If false: Exit while loop


============================================================================
COMPLETE CONTROL FLOW DISPATCH
============================================================================

When parsing encounters a statement:

parse_statement(token):
  ├─ KEYWORD_FUNCTION
  │   └─ parse_function()         → Function node
  │
  ├─ KEYWORD_IF
  │   └─ parse_if()               → If node
  │
  ├─ KEYWORD_WHILE ← NEW
  │   └─ parse_while()            → While node
  │
  ├─ KEYWORD_RETURN
  │   └─ parse_return()           → Return node
  │
  ├─ KEYWORD_PRINT
  │   └─ parse_print()            → Print node
  │
  ├─ IDENTIFIER
  │   ├─ Lookahead: "=" ?
  │   │   └─ parse_assignment()   → Assignment node
  │   │
  │   └─ No "=" ?
  │       └─ parse_expression()   → ExpressionStatement node
  │
  └─ (none match)
      └─ Error: Unexpected token

When executing an AST statement:

execute_statement(stmt):
  ├─ isinstance(Assignment)
  │   └─ execute_assignment()      Set variable
  │
  ├─ isinstance(Print)
  │   └─ execute_print()           Output value
  │
  ├─ isinstance(Return)
  │   └─ execute_return()          Raise ReturnValue
  │
  ├─ isinstance(If)
  │   └─ execute_if()              Conditional execution
  │
  ├─ isinstance(While) ← NEW
  │   └─ execute_while()           Loop execution
  │
  ├─ isinstance(Function)
  │   └─ execute_function_def()    Register function
  │
  ├─ isinstance(ExpressionStatement)
  │   └─ eval_expression()         Execute for side effects
  │
  └─ (none match)
      └─ Error: Unknown statement


============================================================================
COMPLETE WHILE LOOP EXECUTION
============================================================================

Code:
  x = 0
  kadai x < 5:
      rubuta x
      x = x + 1

Execution Timeline:

Step 1: Global initialization
  env = Environment()
  env.define_variable("x", 0)

Step 2: While loop encountered
  ast = While(condition=BinaryOp(...), body=[...])
  execute_while(ast, env)

Step 3: First iteration
  ├─ Evaluate: eval_expression(x < 5, env)
  │   ├─ eval_expression(x, env) → 0
  │   ├─ eval_expression(5, env) → 5
  │   ├─ eval_binary_op(0 < 5) → True
  │   └─ Return: True
  ├─ is_truthy(True) → True
  ├─ Execute body:
  │   ├─ Print: eval_expression(x, env) → 0; print(0)
  │   └─ Assignment: env.define_variable("x", 1)

Step 4: Second iteration
  ├─ Evaluate: x < 5 → 1 < 5 → True
  ├─ Execute body:
  │   ├─ Print: 1
  │   └─ Assignment: x = 2

Step 5-6: Iterations 3-4 (similar)

Step 7: Fifth iteration
  ├─ Evaluate: x < 5 → 4 < 5 → True
  ├─ Execute body:
  │   ├─ Print: 4
  │   └─ Assignment: x = 5

Step 8: Sixth iteration check
  ├─ Evaluate: x < 5 → 5 < 5 → False
  ├─ is_truthy(False) → False
  └─ Exit while loop

Step 9: Program ends
  Output: "01234"


============================================================================
DATA STRUCTURES IN ACTION
============================================================================

Environment Chain Example:

Global Environment:
  ┌─────────────────────────────┐
  │ variables:                  │
  │   "x": 0                    │
  │ functions:                  │
  │   (empty)                   │
  │ parent: None                │
  └─────────────────────────────┘

After function call (Function Environment):
  ┌─────────────────────────────┐
  │ variables:                  │
  │   "sum": 0                  │
  │   "i": 1                    │
  │ functions:                  │
  │   (inherited)               │
  │ parent: ↓                   │
  └─────────────────────────────┘
           ↓
  ┌─────────────────────────────┐
  │ variables:                  │
  │   "x": 0                    │
  │ functions:                  │
  │   "factorial": Function     │
  │ parent: None                │
  └─────────────────────────────┘

When accessing variable in function:
  1. Check function environment: found "sum" → return 0
  2. If not found, check parent (global): would find "x"
  3. If not in parent, search grandparent, etc.
  4. If not found anywhere, raise NameError


============================================================================
LANGUAGE FEATURE MATRIX
============================================================================

Feature             | Status | Example
──────────────────────────────────────────────────────────
Variables           | ✅     | x = 5
Assignment          | ✅     | x = x + 1
Numbers (int/float) | ✅     | 42, 3.14
Strings             | ✅     | "hello"
Arithmetic (+,-,*,/)| ✅     | x + y * 2
Comparison (==,!=)  | ✅     | x == 5
Comparison (>,<)    | ✅     | x > 10
Comparison (>=,<=)  | ✅     | x <= 100
Print statement     | ✅     | rubuta x
Function def        | ✅     | aiki name(): ...
Function call       | ✅     | name(arg)
Return statement    | ✅     | mayar x
Parameters          | ✅     | aiki f(x, y): ...
Recursion           | ✅     | fib(n-1)
If/else            | ✅     | idan x > 5: ...
While loops        | ✅     | kadai x < 5: ... ← NEW
For loops          | ⏳     | (planned)
Break/continue     | ⏳     | (planned)
Lists              | ⏳     | (planned)
Dictionaries       | ⏳     | (planned)
String methods     | ⏳     | (planned)
List comprehension | ⏳     | (planned)
Lambda functions   | ⏳     | (planned)
Classes            | ⏳     | (planned)


============================================================================
SYNTAX SUMMARY
============================================================================

LITERALS:
  Numbers:     42, 3.14, -10
  Strings:     "hello", 'world'
  Booleans:    (from comparisons, no true/false keyword yet)

VARIABLES:
  Assignment:  x = expression
  Reference:   x

OPERATORS:
  Arithmetic:  +, -, *, /
  Comparison:  ==, !=, >, <, >=, <=
  Parentheses: (expression)

STATEMENTS:
  Print:       rubuta expression
  Function:    aiki name(param1, param2): body
  Return:      mayar expression
  If/else:     idan condition: body | in ba haka ba: body
  While:       kadai condition: body ← NEW

BLOCKS:
  Indentation: Block marked by INDENT/DEDENT tokens
  Nesting:     Arbitrary nesting depth


============================================================================
TEST RESULTS SUMMARY
============================================================================

Test File: test_while_loops.py
Total Tests: 5
Pass Rate: 100%
Execution Time: < 1 second

✅ TEST 1: Simple Counting Loop
   Input: x = 0; kadai x < 5: ...
   Output: 01234
   Status: PASS

✅ TEST 2: Sum Accumulation
   Input: sum 1 to 10
   Output: 55
   Status: PASS

✅ TEST 3: Fibonacci
   Input: first 8 Fibonacci numbers
   Output: 0 1 1 2 3 5 8 13
   Status: PASS

✅ TEST 4: Nested Loops
   Input: 3x3 multiplication table
   Output: Correct matrix
   Status: PASS

✅ TEST 5: Function Loop
   Input: count_to(5) with while
   Output: 1,2,3,4,5,
   Status: PASS


============================================================================
SYSTEM READY FOR
============================================================================

✅ Production Use
✅ Loop Implementation Complete
✅ All Tests Passing
✅ Documentation Comprehensive
✅ Extensibility Proven

Next Phase: FOR LOOPS

Same 8-step approach:
  1. Add "don" keyword to lexer
  2. Create For AST node
  3. Implement parse_for()
  4. Update dispatcher
  5. Implement execute_for()
  6. Update type system
  7. Comprehensive tests
  8. Documentation


============================================================================
"""
