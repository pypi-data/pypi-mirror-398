import re


def parse_signature(sig: str):
    sig = sig.strip()
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\((.*)\)$", sig)
    if not m:
        return None
    name = m.group(1)
    inner = m.group(2).strip()
    params = []
    if inner:
        params = [p.strip() for p in inner.split(",")]
    return name, params


def split_args(args: str):
    # naive split by commas; does not handle nested commas in strings
    if not args:
        return []
    return [a.strip() for a in args.split(",")]
