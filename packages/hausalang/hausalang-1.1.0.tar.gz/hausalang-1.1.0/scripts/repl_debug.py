from hausalang.core.lexer import tokenize_program
from hausalang.core import parser
from hausalang.core.interpreter import Interpreter

src = "1 + 2"
print("SOURCE:", repr(src))
print("\nTOKENS:")
for t in tokenize_program(src):
    print(" ", t)

print("\nPARSE:")
toks = tokenize_program(src)
prog = parser.Parser(toks).parse()
print(prog)

print("\nEVAL:")
i = Interpreter()
# If single expression, evaluate it
if len(prog.statements) == 1 and isinstance(
    prog.statements[0], parser.ExpressionStatement
):
    val = i.eval_expression(prog.statements[0].expression, i.global_env)
    print("VALUE:", val)
else:
    i.interpret(prog)
    print("Executed program")
