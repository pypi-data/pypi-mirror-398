"""CLI for VlaamsCodex / Platskript.

Usage:
  plats run path/to/script.plats
  plats build path/to/script.plats --out out.py
  plats show-python path/to/script.plats
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .compiler import compile_plats


def _read_plats(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # ignore coding cookie if present
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("#") and "coding" in lines[0]:
        lines = lines[1:]
    return "\n".join(lines)


def cmd_run(path: Path) -> int:
    plats_src = _read_plats(path)
    py_src = compile_plats(plats_src)
    codeobj = compile(py_src, str(path), "exec")
    exec(codeobj, {})
    return 0


def cmd_build(path: Path, out: Path) -> int:
    plats_src = _read_plats(path)
    py_src = compile_plats(plats_src)
    out.write_text(py_src, encoding="utf-8")
    print(f"Wrote: {out}")
    return 0


def cmd_show_python(path: Path) -> int:
    plats_src = _read_plats(path)
    py_src = compile_plats(plats_src)
    print(py_src)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="plats", description="Run/compile Platskript (.plats) files.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Compile and run a .plats program")
    p_run.add_argument("path", type=Path)

    p_build = sub.add_parser("build", help="Compile a .plats program to Python source")
    p_build.add_argument("path", type=Path)
    p_build.add_argument("--out", type=Path, required=True)

    p_show = sub.add_parser("show-python", help="Print the generated Python source")
    p_show.add_argument("path", type=Path)

    args = p.parse_args(argv)

    if args.cmd == "run":
        return cmd_run(args.path)
    if args.cmd == "build":
        return cmd_build(args.path, args.out)
    if args.cmd == "show-python":
        return cmd_show_python(args.path)

    p.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
