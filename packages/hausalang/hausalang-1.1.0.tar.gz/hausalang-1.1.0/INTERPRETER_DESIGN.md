"""
AST Interpreter Implementation for Hausalang
============================================

This document explains the design and implementation of the Hausalang AST interpreter.

## Overview

The interpreter is built on three core components:

1. **ReturnValue Exception**: Controls function return flow
2. **Environment Class**: Manages scope and bindings
3. **Interpreter Class**: Walks the AST and executes nodes

## Component Architecture

### 1. ReturnValue Exception

Purpose: Implements function returns using Python exceptions
Location: core/interpreter.py, lines 16-24

When a `mayar` (return) statement executes:
1. The Return statement handler calls `execute_return()`
2. `execute_return()` evaluates the expression and raises `ReturnValue(value)`
3. The exception propagates up the call stack to the function call site
4. `eval_function_call()` catches it and returns the value

Benefits:
- Simple, correct unwinding through nested call stacks
- No need for manual "return flag" tracking
- Leverages Python's exception mechanism naturally

Example:
    aiki add(a, b):
        mayar a + b    # Raises ReturnValue(a + b)

    result = add(5, 3)  # Returns 8, caught by eval_function_call()

### 2. Environment Class

Purpose: Manages variable and function scopes
Location: core/interpreter.py, lines 27-77

Structure:
    class Environment:
        parent: Optional[Environment]        # Parent scope (for lookup chain)
        variables: Dict[str, Any]          # Local variables
        functions: Dict[str, Function]     # Local function definitions

Key Methods:

    define_variable(name, value)
        - Store a variable in this environment
        - Local definition (does not affect parent)

    get_variable(name)
        - Retrieve a variable by name
        - Searches: local → parent → parent.parent → ...
        - Raises NameError if not found

    define_function(name, func)
        - Store a function definition (as an AST node)

    get_function(name)
        - Retrieve a function by name
        - Searches scope chain like get_variable()

Scope Chain Example:

    Global Environment (functions: add, multiply)
         │
         └─ Function Environment for add() (parameters: a, b)
              │
              └─ (if add calls another function)

Variable Lookup:
    1. Check local environment
    2. If not found, check parent environment
    3. Repeat up the chain to global scope
    4. If not found anywhere, raise NameError

### 3. Interpreter Class

Purpose: Walk the AST and execute nodes
Location: core/interpreter.py, lines 80-350

**Execution Flow:**

    interpret_program(source_code)              [Public API]
         │
         └─> tokenize_program()                 [Lexer]
              │
              └─> parser.parse()                [Parser]
                   │
                   └─> Interpreter.interpret()
                        │
                        └─> execute_program()
                             │
                             └─> execute_statement() × N
                                  │
                                  ├─> Assignment → eval_expression()
                                  ├─> Print → eval_expression() + print()
                                  ├─> Return → execute_return() [raises]
                                  ├─> If → eval_expression() + execute_statement()
                                  ├─> Function → define in environment
                                  └─> ExpressionStatement → eval_expression()

**Statement Execution Methods:**

Method: execute_assignment(stmt, env)
    1. Evaluate the expression (right side)
    2. Store result in variable (left side)
    Example: x = 5 + 3
        1. eval_expression(5 + 3) → 8
        2. env.define_variable("x", 8)

Method: execute_print(stmt, env)
    1. Evaluate the expression
    2. Print to stdout (no newline)
    Example: rubuta x + 1
        1. eval_expression(x + 1) → (depends on x)
        2. print(result, end='')

Method: execute_return(stmt, env)
    1. Evaluate the expression
    2. Raise ReturnValue(value) to unwind stack
    Example: mayar a + b
        1. eval_expression(a + b)
        2. raise ReturnValue(result)

Method: execute_if(stmt, env)
    1. Evaluate condition expression
    2. If truthy: execute then_body statements
    3. Else if else_body exists: execute else_body statements
    Example: idan x > 5: ... in ba haka ba: ...
        1. eval_expression(x > 5)
        2. If True, execute then_body; else execute else_body

Method: execute_function_def(stmt, env)
    1. Store the Function node in the environment
    2. (Does NOT execute the body, just registers it)
    Example: aiki add(a, b): mayar a + b
        1. env.define_function("add", Function(...))

**Expression Evaluation Methods:**

Method: eval_expression(expr, env)
    Dispatches to the appropriate handler:
    - Number → return expr.value
    - String → return expr.value
    - Identifier → return env.get_variable(expr.name)
    - BinaryOp → eval_binary_op()
    - FunctionCall → eval_function_call()

Method: eval_binary_op(expr, env)
    1. Evaluate left expression
    2. Evaluate right expression
    3. Apply operator:
        - Arithmetic: +, -, *, / (int division for //)
        - Comparison: ==, !=, >, <, >=, <=
    Example: x + y
        1. left = eval_expression(x) → value of x
        2. right = eval_expression(y) → value of y
        3. return left + right

Method: eval_function_call(expr, env)
    1. Evaluate all arguments
    2. Look up function definition
    3. Check argument count matches parameters
    4. Create new Environment with current env as parent
    5. Bind parameters to argument values
    6. Execute function body statements
    7. Catch ReturnValue exception to get return value
    8. Return the value (or None if no return statement)

    Example: add(5, 3)
        1. arg_values = [5, 3]
        2. func = env.get_function("add")
        3. func_env = Environment(parent=env)
        4. func_env.define_variable("a", 5)
           func_env.define_variable("b", 3)
        5. Execute function body with func_env
        6. When "mayar a + b" is hit:
           - Raises ReturnValue(8)
           - Caught by eval_function_call()
           - Returns 8

Method: is_truthy(value)
    Determines conditional truthiness:
    - False, None → falsy
    - 0, "" → falsy
    - Everything else → truthy

## Execution Example: Function Call

Code:
    aiki add(a, b):
        mayar a + b

    result = add(5, 3)
    rubuta result

Step-by-step:

1. **Parse to AST:**
   Program([
       Function(name="add", parameters=["a", "b"], body=[...]),
       Assignment(name="result", value=FunctionCall(name="add", arguments=[5, 3])),
       Print(expression=Identifier(name="result"))
   ])

2. **Execute Function Definition:**
   - Call execute_statement(Function(...), global_env)
   - Calls execute_function_def()
   - global_env.define_function("add", Function(...))
   - Function is now registered (body not executed yet)

3. **Execute Assignment:**
   - Call execute_statement(Assignment(...), global_env)
   - Calls execute_assignment()
   - Calls eval_expression(FunctionCall(...), global_env)
   - Calls eval_function_call(FunctionCall(...), global_env)

   Inside eval_function_call():
   a. arg_values = [eval_expression(5, global_env), eval_expression(3, global_env)]
                  = [5, 3]

   b. func = global_env.get_function("add")
                      → Function(name="add", parameters=["a", "b"], body=[Return(...)])

   c. Check: len([5, 3]) == len(["a", "b"]) ✓

   d. func_env = Environment(parent=global_env)
                 {variables: {}, functions: {}}

   e. func_env.define_variable("a", 5)
      func_env.define_variable("b", 3)
      → func_env = {variables: {"a": 5, "b": 3}, functions: {}}

   f. Execute func.body = [Return(BinaryOp("+", Identifier("a"), Identifier("b")))]
      - execute_statement(Return(...), func_env)
      - execute_return(Return(...), func_env)
      - value = eval_expression(BinaryOp(...), func_env)
        - left = eval_expression(Identifier("a"), func_env)
                → func_env.get_variable("a") → 5
        - right = eval_expression(Identifier("b"), func_env)
                 → func_env.get_variable("b") → 3
        - return 5 + 3 → 8
      - raise ReturnValue(8)

   g. Catch ReturnValue(8) in eval_function_call()
      return 8

   h. Back in execute_assignment():
      global_env.define_variable("result", 8)

4. **Execute Print:**
   - Call execute_statement(Print(...), global_env)
   - Calls execute_print()
   - value = eval_expression(Identifier("result"), global_env)
           → global_env.get_variable("result") → 8
   - print(8, end='')
   - Output: "8"

## Key Design Decisions

1. **Exception-based Returns**
   Why: Simplifies unwinding, matches Python semantics
   Alternative: Boolean flag + explicit checking

2. **Scope Chain via Parent References**
   Why: Efficient lookup, supports closures naturally
   Alternative: Flat scope dictionary

3. **AST-driven, Not Token-driven**
   Why: Clean separation of parsing and execution, easier to extend
   Alternative: Interpret tokens directly

4. **Immutable AST Nodes (frozen dataclasses)**
   Why: Thread-safe, clear semantics, prevents accidental mutations
   Alternative: Mutable AST nodes

5. **Explicit Type Checking with isinstance()**
   Why: Clear dispatch, easy to add new statement types
   Alternative: Visitor pattern or eval()

## Extending the Interpreter

To add a new statement type:

1. Add AST node to core/parser.py
2. Update Statement type union to include new node
3. Add execute_XXX() method to Interpreter class
4. Update execute_statement() dispatch

To add a new expression type:

1. Add AST node to core/parser.py
2. Update Expression type union to include new node
3. Add evaluation case in eval_expression()
4. Implement logic

Example: Adding While Loops

    # In parser.py:
    @dataclass(frozen=True)
    class While(ASTNode):
        condition: 'Expression'
        body: List['Statement']

    # In interpreter.py execute_statement():
    elif isinstance(stmt, parser.While):
        self.execute_while(stmt, env)

    # New method:
    def execute_while(self, stmt: parser.While, env: Environment) -> None:
        while self.is_truthy(self.eval_expression(stmt.condition, env)):
            for body_stmt in stmt.body:
                self.execute_statement(body_stmt, env)

## Testing Strategy

Current test coverage: 5 comprehensive examples
- Simple assignment and arithmetic
- Function definition and call
- If/else conditionals
- String concatenation
- Complex nested program with multiple functions

All tests pass with correct output.

## Performance Characteristics

Time Complexity:
- Variable lookup: O(depth of scope chain) → typically O(1) or O(n) for deep nesting
- Function call: O(execution time of function body)
- Binary operations: O(1)

Space Complexity:
- Each function call: O(parameters + local variables)
- Global scope: O(total variables + total functions)

## Error Handling

Current error types:
- SyntaxError: Parser error (caught and reported)
- NameError: Undefined variable or function
- ValueError: Wrong argument count to function
- RuntimeError: Unknown operator or node type
- TypeError: Invalid operation (caught by Python)

All errors include descriptive messages with context.
"""
