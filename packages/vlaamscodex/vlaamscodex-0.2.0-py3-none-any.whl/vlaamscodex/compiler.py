"""Platskript -> Python compiler (toy).

Supported constructs (v0.1):
- program: `plan doe ... gedaan`
- statement terminator: `amen`
- assignment: `zet <name> op <expr> amen`
- print: `klap <expr> amen`
- function def: `maak funksie <name> met <params...> doe ... gedaan`
- function call: `roep <name> [met <args...>] amen`
- return: `geeftterug <expr> amen`

Expressions (toy):
- `tekst <words...>` -> string literal
- `getal <digits>` -> number literal
- `da <name>` -> variable reference
- `spatie` -> " "
- operators: `plakt` (+) and a handful of arithmetic/boolean comparisons in OP_MAP

This compiler is written to be easy to read, not to be fully correct.
For a real language, write a real parser and an AST.
"""

from __future__ import annotations

import re

OP_MAP = {
    "plakt": "+",
    "derbij": "+",
    "deraf": "-",
    "keer": "*",
    "gedeeld": "/",
    "isgelijk": "==",
    "isniegelijk": "!=",
    "isgroterdan": ">",
    "iskleinerdan": "<",
    "enook": "and",
    "ofwel": "or",
    "nie": "not",
}

_EXPR_STOP = {"dan", "doe", "amen"}


def _split_args(tokens: list[str]) -> list[list[str]]:
    """Split arguments separated by the token `en`."""
    args: list[list[str]] = []
    cur: list[str] = []
    for t in tokens:
        if t == "en":
            if cur:
                args.append(cur)
                cur = []
        else:
            cur.append(t)
    if cur:
        args.append(cur)
    return args


def _parse_expr(tokens: list[str]) -> str:
    """Parse a minimal expression into a Python expression string."""
    parts: list[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in _EXPR_STOP:
            break

        if t == "spatie":
            parts.append(repr(" "))
            i += 1
            continue

        if t == "tekst":
            i += 1
            words: list[str] = []
            while (
                i < len(tokens)
                and tokens[i] not in OP_MAP
                and tokens[i] not in _EXPR_STOP
                and tokens[i] != "en"
            ):
                words.append(tokens[i])
                i += 1
            parts.append(repr(" ".join(words)))
            continue

        if t == "getal":
            i += 1
            if i >= len(tokens):
                raise ValueError("getal without value")
            num = tokens[i]
            i += 1
            if not re.fullmatch(r"-?\d+(\.\d+)?", num):
                raise ValueError(f"invalid number literal: {num}")
            parts.append(num)
            continue

        if t == "da":
            i += 1
            if i >= len(tokens):
                raise ValueError("da without identifier")
            parts.append(tokens[i])
            i += 1
            continue

        if t in OP_MAP:
            parts.append(OP_MAP[t])
            i += 1
            continue

        # fallback: treat as identifier
        parts.append(t)
        i += 1

    return " ".join(parts) if parts else "None"


def compile_plats(plats_src: str) -> str:
    """Compile Platskript source to Python source."""
    py_lines: list[str] = []
    indent = 0
    stack: list[str] = []

    def emit(line: str) -> None:
        py_lines.append(("    " * indent) + line)

    for raw in plats_src.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Skip coding cookie if present (the codec will remove it too, but this is safe).
        if line.startswith("#") and "coding" in line:
            continue

        tokens = line.split()

        # close block
        if tokens == ["gedaan"]:
            if not stack:
                raise ValueError("gedaan without open block")
            kind = stack.pop()
            if kind in {"funksie"}:
                indent -= 1
            continue

        # start program (no indent; just a marker)
        if tokens[:2] == ["plan", "doe"]:
            stack.append("plan")
            continue

        # function start: maak funksie NAME met ... doe
        if len(tokens) >= 5 and tokens[0:2] == ["maak", "funksie"] and tokens[-1] == "doe":
            name = tokens[2]
            if "met" not in tokens:
                raise ValueError("function missing 'met'")
            met_i = tokens.index("met")
            params_tokens = tokens[met_i + 1 : -1]
            params = [t for t in params_tokens if t != "en"]
            emit(f"def {name}({', '.join(params)}):")
            indent += 1
            stack.append("funksie")
            continue

        # statements must end with 'amen'
        if not tokens or tokens[-1] != "amen":
            raise ValueError(f"missing 'amen' statement terminator: {line}")
        tokens = tokens[:-1]

        if not tokens:
            continue

        if tokens[0] == "klap":
            emit(f"print({_parse_expr(tokens[1:])})")
            continue

        if tokens[0] == "zet":
            if "op" not in tokens:
                raise ValueError("zet missing 'op'")
            op_i = tokens.index("op")
            var = tokens[1]
            emit(f"{var} = {_parse_expr(tokens[op_i + 1:])}")
            continue

        if tokens[0] == "roep":
            func = tokens[1]
            if "met" in tokens:
                met_i = tokens.index("met")
                args = [_parse_expr(a) for a in _split_args(tokens[met_i + 1 :])]
                emit(f"{func}({', '.join(args)})")
            else:
                emit(f"{func}()")
            continue

        if tokens[0] == "geeftterug":
            emit(f"return {_parse_expr(tokens[1:])}")
            continue

        raise ValueError(f"unknown instruction: {line}")

    if stack:
        raise ValueError(f"unclosed blocks: {stack}")
    if indent != 0:
        raise ValueError(f"internal error: indent={indent}")

    return "\n".join(py_lines) + "\n"

