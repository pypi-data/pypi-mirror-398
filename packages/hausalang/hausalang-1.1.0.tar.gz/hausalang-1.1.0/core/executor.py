def hus_err(ha, en):
    print(f"{ha} ({en})")


def execute(line, variables):
    # =============================
    # rubuta (print)
    # =============================
    if line.startswith("rubuta"):
        content = line.replace("rubuta", "", 1).strip()

        if content.startswith('"') and content.endswith('"'):
            print(content[1:-1])
            return

        if content in variables:
            print(variables[content])
            return

        # try to parse a number literal
        try:
            if content.isdigit() or (content.startswith("-") and content[1:].isdigit()):
                print(int(content))
                return
            # float
            float_val = float(content)
            print(float_val)
            return
        except Exception:
            # try to evaluate as an expression using interpreter's parser (lazy import to avoid circular import)
            try:
                from core.interpreter import parse_literal

                val = parse_literal(content, variables)
                if val is not None:
                    print(val)
                    return
            except Exception:
                pass

            hus_err(
                "kuskure: rubuta yana bukatar rubutu ko variable",
                "error: 'rubuta' needs a string or a variable",
            )
            return

    # =============================
    # Unknown command
    # =============================
    hus_err(
        f"kuskure: ban gane umarnin ba -> {line}", f"error: unknown command -> {line}"
    )
