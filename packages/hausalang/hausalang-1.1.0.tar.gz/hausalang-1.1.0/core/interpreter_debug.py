from core.executor import execute
import re


def hus_err(ha, en):
    print(f"{ha} ({en})")


def is_valid_name(name):
    return re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name) is not None


def parse_literal(token, variables):
    token = token.strip()
    # String literal
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        return token[1:-1]

    # Number literal int or float
    if re.match(r"^-?\d+$", token):
        return int(token)
    if re.match(r"^-?\d+\.\d+$", token):
        return float(token)

    # Variable reference
    if token in variables:
        return variables[token]

    # Unknown
    return None


def compare_values(left, op, right):
    try:
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
    except TypeError:
        return False
    return False


def run(code):
    lines = code.splitlines()
    variables = {}

    in_block = False
    block_base_indent = 0
    block_condition = True
    else_mode = False

    ops = ["==", "!=", ">=", "<=", ">", "<"]

    for raw in lines:
        # handle BOM and trailing whitespace
        raw = raw.rstrip("\n\r")
        if raw.strip() == "":
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.lstrip(" ")

        print(
            f"[DEBUG] indent={indent}, in_block={in_block}, block_base_indent={block_base_indent}, line={repr(line[:30])}"
        )

        # leaving a block
        if (
            in_block
            and indent <= block_base_indent
            and not line.startswith("in ba haka ba")
        ):
            in_block = False
            else_mode = False
            block_condition = True
            print("[DEBUG] LEFT BLOCK")

        # if
        if line.startswith("idan"):
            condition = line.replace("idan", "", 1).strip()

            if not condition.endswith(":"):
                hus_err(
                    "kuskure: idan dole ya kare da ':'",
                    "error: 'idan' must end with ':'",
                )
                in_block = False
                continue

            condition = condition[:-1].strip()

            # find operator
            found = None
            for o in ops:
                if o in condition:
                    found = o
                    break

            if not found:
                hus_err(
                    "kuskure: idan yana bukatar ma'aunin kwatanci (==, !=, >, <, >=, <=)",
                    "error: 'idan' requires a comparison operator",
                )
                in_block = False
                continue

            left_s, right_s = condition.split(found, 1)
            left_s = left_s.strip()
            right_s = right_s.strip()

            left = parse_literal(left_s, variables)
            right = parse_literal(right_s, variables)

            if left is None:
                hus_err(
                    f"kuskure: ba a san {left_s} ba", f"error: unknown value {left_s}"
                )
                in_block = False
                continue

            if right is None:
                hus_err(
                    f"kuskure: ba a san {right_s} ba", f"error: unknown value {right_s}"
                )
                in_block = False
                continue

            block_condition = compare_values(left, found, right)
            in_block = True
            block_base_indent = indent
            else_mode = False
            print(f"[DEBUG] IF: condition={block_condition}")
            continue

        # else
        if line.startswith("in ba haka ba"):
            if not line.endswith(":"):
                hus_err(
                    "kuskure: 'in ba haka ba' dole ya kare da ':'",
                    "error: 'in ba haka ba' must end with ':'",
                )
                in_block = False
                continue
            else_mode = True
            in_block = True
            print("[DEBUG] ELSE")
            continue

        # assignment
        if "=" in line:
            name, value = line.split("=", 1)
            name = name.strip()
            value_s = value.strip()

            if not is_valid_name(name):
                hus_err(
                    f"kuskure: sunan variable mara kyau -> {name}",
                    f"error: invalid variable name -> {name}",
                )
                continue

            val = parse_literal(value_s, variables)
            if val is None:
                hus_err(
                    f"kuskure: darajar ba ta da inganci -> {value_s}",
                    f"error: invalid value -> {value_s}",
                )
                continue

            variables[name] = val
            print(f"[DEBUG] ASSIGN: {name} = {val}")
            continue

        # execution
        should_run = True
        if in_block:
            if indent <= block_base_indent:
                should_run = True
            else:
                should_run = (not block_condition) if else_mode else block_condition

        print(
            f"[DEBUG] EXECUTE: should_run={should_run}, in_block={in_block}, indent={indent}, block_base_indent={block_base_indent}"
        )
        if should_run:
            execute(line, variables)
