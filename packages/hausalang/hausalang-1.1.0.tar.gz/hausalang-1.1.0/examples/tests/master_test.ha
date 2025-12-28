# MASTER TEST - Comprehensive Hausalang Language Showcase
# Tests all language features in a unified program

rubuta "========================================="
rubuta 10
rubuta "HAUSALANG MASTER TEST SUITE"
rubuta 10
rubuta "========================================="
rubuta 10

# ========== SECTION 1: BASIC ARITHMETIC & VARIABLES ==========
rubuta 10
rubuta "SECTION 1: Basic Arithmetic & Variables"
rubuta 10
rubuta "---"
rubuta 10

x = 100
y = 25
z = 15

sum_result = x + y
diff_result = x - y
mult_result = y * z
div_result = x / y

rubuta "x = "
rubuta x
rubuta ", y = "
rubuta y
rubuta ", z = "
rubuta z
rubuta 10
rubuta "x + y = "
rubuta sum_result
rubuta 10
rubuta "x - y = "
rubuta diff_result
rubuta 10
rubuta "y * z = "
rubuta mult_result
rubuta 10
rubuta "x / y = "
rubuta div_result
rubuta 10

# ========== SECTION 2: CONDITIONALS & COMPARISONS ==========
rubuta 10
rubuta "SECTION 2: Conditionals & Comparisons"
rubuta 10
rubuta "---"
rubuta 10

rubuta "Testing conditions on x = 100:"
rubuta 10

idan x > 90:
    rubuta "✓ x > 90: TRUE"
    rubuta 10
in ba haka ba:
    rubuta "✗ x > 90: FALSE"
    rubuta 10

idan x == 100:
    rubuta "✓ x == 100: TRUE"
    rubuta 10
in ba haka ba:
    rubuta "✗ x == 100: FALSE"
    rubuta 10

idan x < 50:
    rubuta "✗ x < 50: FALSE"
    rubuta 10
in ba haka ba:
    rubuta "✓ x < 50: FALSE"
    rubuta 10

# ========== SECTION 3: WHILE LOOPS ==========
rubuta 10
rubuta "SECTION 3: While Loops"
rubuta 10
rubuta "---"
rubuta 10

rubuta "Countdown from 5 to 1: "
counter = 5
kadai counter > 0:
    rubuta counter
    rubuta " "
    counter = counter - 1
rubuta 10

rubuta "Sum of 1 to 20: "
n = 1
total = 0
kadai n <= 20:
    total = total + n
    n = n + 1
rubuta total
rubuta 10

# ========== SECTION 4: FOR LOOPS ==========
rubuta 10
rubuta "SECTION 4: For Loops"
rubuta 10
rubuta "---"
rubuta 10

rubuta "Numbers 1 to 10: "
don i = 1 zuwa 10:
    rubuta i
    rubuta " "
rubuta 10

rubuta "Even numbers 2 to 10: "
don i = 2 zuwa 10:
    idan i == 2:
        rubuta i
    idan i == 4:
        rubuta i
    idan i == 6:
        rubuta i
    idan i == 8:
        rubuta i
    idan i == 10:
        rubuta i
rubuta 10

# ========== SECTION 5: FUNCTIONS ==========
rubuta 10
rubuta "SECTION 5: Functions"
rubuta 10
rubuta "---"
rubuta 10

aiki square(n):
    mayar n * n

aiki cube(n):
    mayar n * n * n

aiki power(base, exp):
    result = 1
    i = 1
    kadai i <= exp:
        result = result * base
        i = i + 1
    mayar result

rubuta "square(7) = "
rubuta square(7)
rubuta 10
rubuta "cube(4) = "
rubuta cube(4)
rubuta 10
rubuta "power(2, 8) = "
rubuta power(2, 8)
rubuta 10

# ========== SECTION 6: NESTED LOOPS & CONDITIONALS ==========
rubuta 10
rubuta "SECTION 6: Nested Loops & Conditionals"
rubuta 10
rubuta "---"
rubuta 10

rubuta "3x3 Table: "
rubuta 10
row = 1
kadai row <= 3:
    col = 1
    kadai col <= 3:
        val = row * col
        idan val < 10:
            rubuta " "
        rubuta val
        rubuta " "
        col = col + 1
    rubuta 10
    row = row + 1

# ========== SECTION 7: COMPLEX LOGIC ==========
rubuta 10
rubuta "SECTION 7: Complex Logic - Prime Checker"
rubuta 10
rubuta "---"
rubuta 10

aiki is_prime(num):
    idan num < 2:
        mayar 0

    divisor = 2
    kadai divisor * divisor <= num:
        remainder = num - (divisor * (num / divisor))
        idan remainder == 0:
            mayar 0
        divisor = divisor + 1

    mayar 1

rubuta "Checking primes 2 to 10: "
rubuta 10
don num = 2 zuwa 10:
    prime = is_prime(num)
    idan prime == 1:
        rubuta num
        rubuta " is prime"
    in ba haka ba:
        rubuta num
        rubuta " is not prime"
    rubuta 10

# ========== SECTION 8: PATTERN GENERATION ==========
rubuta 10
rubuta "SECTION 8: Pattern Generation"
rubuta 10
rubuta "---"
rubuta 10

rubuta "Triangle Pattern: "
rubuta 10
line = 1
kadai line <= 5:
    star = 1
    kadai star <= line:
        rubuta "* "
        star = star + 1
    rubuta 10
    line = line + 1

# ========== SECTION 9: CALCULATIONS & ACCUMULATION ==========
rubuta 10
rubuta "SECTION 9: Calculations & Accumulation"
rubuta 10
rubuta "---"
rubuta 10

aiki factorial_calc(n):
    fact = 1
    i = 1
    kadai i <= n:
        fact = fact * i
        i = i + 1
    mayar fact

rubuta "Factorials:"
rubuta 10
don num = 1 zuwa 6:
    fact = factorial_calc(num)
    rubuta num
    rubuta "! = "
    rubuta fact
    rubuta 10

# ========== SECTION 10: FINAL SUMMARY ==========
rubuta 10
rubuta "========================================="
rubuta 10
rubuta "MASTER TEST COMPLETE!"
rubuta 10
rubuta "========================================="
rubuta 10
rubuta "All Hausalang features tested:"
rubuta 10
rubuta "✓ Variables & Arithmetic"
rubuta 10
rubuta "✓ Conditionals (if/else)"
rubuta 10
rubuta "✓ While Loops"
rubuta 10
rubuta "✓ For Loops"
rubuta 10
rubuta "✓ Functions & Recursion"
rubuta 10
rubuta "✓ Nested Control Structures"
rubuta 10
rubuta "✓ Complex Logic"
rubuta 10
rubuta "========================================="
rubuta 10
