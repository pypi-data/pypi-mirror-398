"""Entrypoint for Hausalang REPL (Phase 1)."""

from __future__ import annotations

from hausalang.repl.session import ReplSession
from hausalang.repl.input_handler import read_prompt, load_history, save_history
from hausalang.repl.directives import DirectiveProcessor


def main() -> None:
    session = ReplSession()
    directives = DirectiveProcessor(session)
    load_history()
    try:
        while True:
            line = read_prompt("hausa> ")
            if not line:
                continue
            # Handle colon-prefixed directives in Phase 2
            if line.strip().startswith(":"):
                out = directives.process(line)
                if out == "__EXIT__":
                    print("Goodbye!")
                    break
                if out:
                    print(out)
                continue
            # For Phase 1 we allow multi-line blocks by simple heuristic:
            # lines ending with ':' start a block that reads until a blank line.
            if line.rstrip().endswith(":"):
                lines = [line]
                while True:
                    nxt = read_prompt("....> ")
                    if nxt.strip() == "":
                        break
                    lines.append(nxt)
                source = "\n".join(lines)
            else:
                source = line

            result = session.execute(source)
            out = session.format_result(result)
            if out:
                print(out)
    finally:
        save_history()


if __name__ == "__main__":
    main()
