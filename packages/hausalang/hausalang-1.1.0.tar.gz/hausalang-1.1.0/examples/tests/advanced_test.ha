# Advanced Test - More Complex Examples

# Fibonacci Sequence (While Loop)
rubuta "Fibonacci Series: "
rubuta 10
a = 0
b = 1
count = 0
kadai count < 6:
    rubuta a
    rubuta " "
    temp = a + b
    a = b
    b = temp
    count = count + 1
rubuta 10

# Factorial (For Loop + Function)
rubuta "Factorials: "
rubuta 10
aiki factorial(n):
    result = 1
    i = 1
    kadai i <= n:
        result = result * i
        i = i + 1
    mayar result

fact5 = factorial(5)
rubuta "5! = "
rubuta fact5
rubuta 10

# Multiplication Table
rubuta "Multiplication Table (3x3): "
rubuta 10
row = 1
kadai row <= 3:
    col = 1
    kadai col <= 3:
        product = row * col
        rubuta product
        rubuta " "
        col = col + 1
    rubuta 10
    row = row + 1

# Complex Conditional Logic
rubuta "Grade Assignment: "
rubuta 10
aiki get_grade(score):
    idan score >= 90:
        mayar "A"
    idan score >= 80:
        mayar "B"
    idan score >= 70:
        mayar "C"
    idan score >= 60:
        mayar "D"
    mayar "F"

grade1 = get_grade(95)
rubuta "Score 95: "
rubuta grade1
rubuta 10

grade2 = get_grade(75)
rubuta "Score 75: "
rubuta grade2
rubuta 10

# Array-like Loop with Accumulation
rubuta "Sum and Product: "
rubuta 10
sum = 0
product = 1
don i = 1 zuwa 5:
    sum = sum + i
    product = product * i
rubuta "Sum(1-5) = "
rubuta sum
rubuta 10
rubuta "Product(1-5) = "
rubuta product
rubuta 10

rubuta "Test Complete!"
rubuta 10
