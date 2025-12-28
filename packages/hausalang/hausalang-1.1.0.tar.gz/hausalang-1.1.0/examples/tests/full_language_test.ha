# Variables and arithmetic
x = 10
y = 5
z = x * y + 20
rubuta "Result: "
rubuta z
rubuta 10

# If / Else
rubuta "If/Else: "
idan z > 50:
    rubuta "z is big"
in ba haka ba:
    rubuta "z is small"
rubuta 10

# While loop
rubuta "While loop sum: "
i = 0
sum = 0
kadai i < 5:
    sum = sum + i
    i = i + 1
rubuta sum
rubuta 10

# For loop
rubuta "For loop sum: "
total = 0
don n = 1 zuwa 5:
    total = total + n
rubuta total
rubuta 10

# Function definition
rubuta "Function result: "
aiki add(a, b):
    mayar a + b

result = add(7, 8)
rubuta result
rubuta 10

# Nested control
rubuta "Nested control: "
count = 0
kadai count < 3:
    idan count == 1:
        rubuta "middle "
    in ba haka ba:
        rubuta count
        rubuta " "
    count = count + 1
rubuta 10

rubuta "Done!"
rubuta 10
