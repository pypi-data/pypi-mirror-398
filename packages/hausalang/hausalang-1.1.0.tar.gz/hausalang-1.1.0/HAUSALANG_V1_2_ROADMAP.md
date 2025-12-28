# Hausalang v1.2 Roadmap

**Status:** Planning
**Release Target:** Q2 2026
**Phase:** Design & Architecture

---

## Overview

Hausalang v1.2 focuses on production-grade reliability and advanced language features. Building on v1.1's solid error system and v1.0's core interpreter, v1.2 introduces infinite-loop detection, resource limits, type annotations, and a structured error versioning system.

**Key Themes:**
- **Safety:** Infinite-loop detection, resource limits, timeout handling
- **Discoverability:** Error schema versioning, error registry API
- **Extensibility:** Type annotations, import system foundation

---

## Major Features

### 1. Infinite-Loop Detection

**Problem:** v1.1 has an `INFINITE_LOOP` ErrorKind defined but unimplemented. Long-running or infinite loops crash without clear diagnosis.

**Solution:**
- **Instruction counter:** Track executed statements/expressions per loop iteration
- **Heuristic detection:** Flag when loop iteration count exceeds threshold (e.g., 100k iterations)
- **Two-stage approach:**
  - Stage 1 (v1.2.0): Simple iteration counter, hard threshold
  - Stage 2 (v1.2.1+): Pattern-based detection (e.g., inner loop increment rate)

**Design:**
```python
class Interpreter:
    def __init__(self):
        self.loop_iteration_count = 0
        self.loop_iteration_limit = 100_000  # configurable per execution

    def execute_while_loop(self, stmt, env):
        self.loop_iteration_count = 0
        while self.eval_condition(stmt.condition, env):
            self.loop_iteration_count += 1
            if self.loop_iteration_count > self.loop_iteration_limit:
                raise ContextualError(
                    kind=ErrorKind.INFINITE_LOOP,
                    message=f"Loop exceeded {self.loop_iteration_limit} iterations",
                    location=stmt.location
                )
            self.execute_statement(stmt.body, env)
```

**Testing:**
- Unit tests for iteration counter (typical loops, nested loops, early exit)
- Regression tests to ensure legitimate loops still work
- Stress test with known infinite loop patterns

**Configuration:**
- `Interpreter(max_loop_iterations=1_000_000)` for customization
- Optional: Environment variable `HAUSALANG_MAX_LOOP_ITER`

---

### 2. Resource Limits

**Problem:** Unbounded recursion, deep nesting, or large data structures can exhaust memory or stack.

**Solution:**
- **Stack depth limit:** Prevent stack overflow via recursion (default: 1000)
- **Memory budget:** Optional tracking of heap allocations (v1.2.1+)
- **Execution timeout:** Optional wall-clock time limit per program

**Design:**

```python
class Interpreter:
    def __init__(self, max_call_depth=1000, max_memory_mb=None, timeout_sec=None):
        self.max_call_depth = max_call_depth
        self.call_depth = 0
        self.max_memory_mb = max_memory_mb
        self.timeout_sec = timeout_sec
        self.start_time = None

    def call_function(self, func, args, env):
        self.call_depth += 1
        if self.call_depth > self.max_call_depth:
            raise ContextualError(
                kind=ErrorKind.STACK_OVERFLOW,
                message=f"Call depth exceeded {self.max_call_depth}",
                location=func.location
            )
        try:
            return self._do_call(func, args, env)
        finally:
            self.call_depth -= 1

    def interpret(self, program):
        self.start_time = time.time()
        try:
            self.execute_program(program, self.global_env)
        finally:
            elapsed = time.time() - self.start_time
            if self.timeout_sec and elapsed > self.timeout_sec:
                raise ContextualError(
                    kind=ErrorKind.EXECUTION_TIMEOUT,
                    message=f"Execution exceeded {self.timeout_sec}s",
                    location=program.location if hasattr(program, 'location') else None
                )
```

**Error Kinds (New):**
- `STACK_OVERFLOW = "runtime/resource/stack_overflow"`
- `MEMORY_LIMIT = "runtime/resource/memory_limit"`
- `EXECUTION_TIMEOUT = "runtime/resource/execution_timeout"`

**Testing:**
- Unit tests for max_call_depth (recursion, mutual recursion)
- Unit tests for timeout_sec (long loops, timeout trigger)
- Regression tests for legitimate recursion (factorial, fibonacci with memoization)

---

### 3. Error Schema Versioning

**Problem:** Error structure may evolve; consumers need to handle schema changes gracefully.

**Solution:**
- Add `schema_version` to ContextualError.to_dict()
- Create `ERROR_SCHEMA_VERSION = "1.1"` constant
- Document breaking changes in CHANGELOG
- Provide migration guide for v1.0 → v1.1 → v1.2 error handling

**Design:**

```python
# In errors.py
ERROR_SCHEMA_VERSION = "1.1"

class ContextualError(Exception):
    def to_dict(self) -> dict:
        return {
            "schema_version": ERROR_SCHEMA_VERSION,
            "error_id": self.error_id,
            "kind": self.kind.value,
            "message": self.message,
            "location": asdict(self.location),
            "timestamp": self.timestamp.isoformat(),
            "context_frames": [asdict(f) for f in self.context_frames],
            "tags": sorted(self.tags),
            "help": self.help,
        }
```

**Registry API (Future):**
```python
# Optional: v1.2.1+
from hausalang.core.errors import error_registry

# Lookup by kind
error_def = error_registry.get(ErrorKind.UNDEFINED_VARIABLE)
print(error_def.schema_version)      # "1.1"
print(error_def.is_recoverable)      # True/False
print(error_def.related_kinds)       # [ErrorKind.UNDEFINED_FUNCTION, ...]

# Filter by category
name_errors = error_registry.filter_by_prefix("runtime/name/")
for err in name_errors:
    print(err.kind, err.message_template)
```

---

### 4. Type Annotations (Optional)

**Problem:** Hausalang lacks type information. Users can't document expected types, and interpreters can't catch type errors early.

**Solution (Phase 1):**
- **Type hint syntax:** Optional annotations in function definitions and variables
- **No enforcement:** Annotations are parsed but not validated at runtime (v1.2)
- **Foundation for v1.3:** Type checker and gradual typing support

**Proposed Syntax:**

```hausa
# Function with type hints (comments-based for v1.2)
aiki add(a: jigon, b: jigon) -> jigon:
    mayar a + b

# Variable with type hint (optional)
x: jigon = 5
y: maikalanci = "hello"

# Type aliases (v1.2.1+)
nau Tuples = (jigon, maikalanci)
aiki get_pair() -> Tuples:
    mayar (42, "answer")
```

**Implementation Approach:**
- Extend lexer to recognize `:` and `->` in function/variable contexts
- Extend parser to capture type annotations in AST nodes
- Store annotations but don't enforce (no-op in interpreter)
- Provide `extract_type_hints(program)` utility for future tools

**Testing:**
- Parser tests for type hint syntax (valid annotations, edge cases)
- Interpreter tests that type hints don't affect execution
- Utility tests for type hint extraction

---

### 5. Import System (Foundation)

**Status:** Planned for v1.2.1 or later
**Scope:** Minimal viable set for code reuse

**Design (Sketch):**
```hausa
# hausa_math.ha
aiki factorial(n: jigon) -> jigon:
    idan n <= 1:
        mayar 1
    mayar n * factorial(n - 1)

# main.ha
dawo hausa_math

rubuta hausa_math.factorial(5)
```

**Not in v1.2.0:**
- Packages, namespaces
- Circular import detection
- Standard library

---

## Error Kind Additions (v1.2)

```python
class ErrorKind(Enum):
    # Resource/Execution Errors (new)
    INFINITE_LOOP = "runtime/resource/infinite_loop"
    STACK_OVERFLOW = "runtime/resource/stack_overflow"
    MEMORY_LIMIT = "runtime/resource/memory_limit"
    EXECUTION_TIMEOUT = "runtime/resource/execution_timeout"

    # Type System Errors (v1.2.1+, not enforced in v1.2.0)
    INVALID_TYPE_HINT = "parse/invalid_type_hint"
    TYPE_MISMATCH = "runtime/type/type_mismatch"  # Not yet enforced
```

---

## Testing Strategy

### Phase 1: Unit Tests
- Infinite-loop detection (simple loops, nested, conditional)
- Stack depth tracking (recursion, mutual calls, tail-call optimization test)
- Timeout behavior (real-time, accuracy ±100ms acceptable)
- Type hint parsing (valid syntax, AST structure)

### Phase 2: Integration Tests
- Complex programs: recursive Fibonacci with loop counter
- Edge cases: loop boundary conditions, near-limit recursion
- Regression: all v1.1 programs still pass

### Phase 3: Performance Tests
- Overhead of loop counter: <5% vs. v1.1
- Overhead of stack tracking: <2% vs. v1.1
- Typical program execution time (benchmarks from v1.1)

---

## Backward Compatibility

**Breaking Changes:** None expected.

**Deprecations:** None.

**Additions:**
- New error kinds (mapped to appropriate builtin exceptions)
- New optional parameters to `Interpreter.__init__`
- Type hints are optional syntax (can be added to existing programs)

---

## Documentation Plan

### For v1.2.0 Release:
1. **HAUSALANG_V1_2_DESIGN.md** — Technical design document (this roadmap expanded)
2. **RESOURCE_LIMITS.md** — User guide for configuring limits
3. **LOOP_DETECTION.md** — How infinite-loop detection works, limitations
4. **ERROR_SCHEMA.md** — Error structure, versioning, migration guide
5. Update **README.md** with v1.2 features and new examples

### For v1.2.1 (if released):
6. **TYPE_SYSTEM.md** — Type hint syntax and forward-compatibility notes
7. **IMPORTS.md** — Module system usage (if implemented)

---

## Release Milestones

| Version | Features | Status |
|---------|----------|--------|
| v1.1 (Dec 2025) | ErrorKind, modulo, unary ops | ✅ Released |
| v1.2.0 (Q2 2026) | Loop detection, resource limits, error versioning | 📅 Planned |
| v1.2.1 (Q3 2026) | Type hints (optional), enhanced detection | 📅 Planned |
| v1.3 (Q4 2026) | Type checking, imports, standard library | 🔮 Proposed |

---

## Risk Assessment

| Feature | Risk | Mitigation |
|---------|------|-----------|
| Loop detection | False positives (flagging slow-but-valid code) | Conservative threshold (100k+), allow user override |
| Stack tracking | Performance overhead | Profile and optimize hot paths |
| Type hints | Confusion with enforcement | Clear docs: v1.2 is informational only |
| Timeout | Wall-clock time varies by system | ±10% tolerance acceptable, document limitations |

---

## Open Questions

1. **Loop detection algorithm:** Simple iteration count vs. heuristic analysis?
   - **Decision:** Start with simple count; can evolve in v1.2.1+

2. **Stack limit default:** 1000 or 10000?
   - **Decision:** 1000 (conservative, matches CPython default)

3. **Timeout precision:** Use `time.time()` or `time.perf_counter()`?
   - **Decision:** `time.perf_counter()` for wall-clock accuracy

4. **Memory tracking:** Enabled by default or opt-in?
   - **Decision:** Opt-in (disabled by default) due to overhead

5. **Type hints parser:** Strict or lenient (allow unknown type names)?
   - **Decision:** Lenient (store as strings); v1.3 can resolve

---

## Success Criteria

- ✅ All v1.1 programs run unchanged
- ✅ Infinite loops detected within 1 second (on modern hardware)
- ✅ No performance regression >5% vs. v1.1
- ✅ Full test coverage for new features (>90%)
- ✅ Documentation complete and examples working
- ✅ CI passes on Python 3.9–3.13 (all platforms)

---

**Next Steps:**
1. Implement Phase 1 (Loop + Resource limits) in feature branch
2. Add comprehensive tests (50+ new tests expected)
3. Performance benchmark against v1.1
4. Community feedback on design (GitHub discussions)
5. Finalize documentation
6. Release v1.2.0 with release notes
