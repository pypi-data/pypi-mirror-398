from core.lexer import tokenize_program
import sys

s = sys.argv[1] if len(sys.argv) > 1 else "1 + 2"
for t in tokenize_program(s):
    print(repr(t))
