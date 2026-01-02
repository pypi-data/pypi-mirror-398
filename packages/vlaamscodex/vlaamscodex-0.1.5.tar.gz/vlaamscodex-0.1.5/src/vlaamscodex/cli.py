"""CLI for VlaamsCodex / Platskript.

Usage:
  plats run path/to/script.plats
  plats build path/to/script.plats --out out.py
  plats show-python path/to/script.plats
  plats help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import compile_plats

__version__ = "0.1.5"


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


def cmd_help() -> int:
    print(f"""
VlaamsCodex v{__version__} - Platskript Transpiler
================================================

A transpiler for Platskript (.plats), a parody programming language
that uses Flemish dialect keywords and compiles to Python.

COMMANDS:
  plats run <file.plats>                Run a Platskript program
  plats build <file.plats> --out <file> Compile to Python source file
  plats show-python <file.plats>        Display generated Python code
  plats help                            Show this help message
  plats version                         Show version information

MAGIC MODE:
  python <file.plats>                   Run directly with Python!

EXAMPLES:
  plats run hello.plats                 Run a program
  plats show-python hello.plats         See the Python output
  plats build hello.plats --out out.py  Compile to .py file
  python hello.plats                    Magic mode (requires install)

QUICK START:
  1. Create a file 'hello.plats':

     # coding: vlaamsplats
     plan doe
       klap tekst gdag wereld amen
     gedaan

  2. Run it:
     plats run hello.plats

For more info: https://github.com/anubissbe/Vlaamse-Codex
""")
    return 0


def cmd_version() -> int:
    print(f"VlaamsCodex v{__version__}")
    return 0


def cmd_haalp() -> int:
    print(f"""
VlaamsCodex v{__version__} - Platskansen Vertoaler
===================================================

Een vertoaler vo Platskript (.plats), ne parodie programmeertaal
die Vlaamse dialectwoorden gebruukt en compileert na Python.

COMMANDO'S:
  plats run <bestand.plats>                 Voer een Platskript programma uut
  plats build <bestand.plats> --out <file>  Compileer na Python broncode
  plats show-python <bestand.plats>         Toon de gegenereerde Python code
  plats help                                Toon hulp in 't Engels
  plats haalp                               Toon hulp in 't Vlaams
  plats version                             Toon versie informatie

MAGISCHE MODUS:
  python <bestand.plats>                    Direct uitvoeren me Python!

VOORBEELDEN:
  plats run hallo.plats                     Voer een programma uut
  plats show-python hallo.plats             Bekijk de Python output
  plats build hallo.plats --out uit.py      Compileer na .py bestand
  python hallo.plats                        Magische modus

SNE STARTEN:
  1. Mokt een bestand 'hallo.plats':

     # coding: vlaamsplats
     plan doe
       klap tekst gdag weeireld amen
     gedaan

  2. Voer 't uut:
     plats run hallo.plats

  Of direct:
     python hallo.plats

PLATSKRIPT TAALE:
  plan doe ... gedaan     Begin en einde van 't programma
  zet X op Y amen         Variabele toewijzing
  klap X amen             Print na 't scherm
  maak funksie ... doe    Maak een funksie
  roep X met Y amen       Roep een funksie aan
  geeftterug X amen       Geef een waarde terug
  tekst woorden           String literal
  getal 123               Nummer literal
  da variabele            Variabele referentie
  plakt                   String concatenatie
  spatie                  Spatie karakter

Mier info: https://github.com/anubissbe/Vlaamse-Codex

't Es simpel, 't es plansen, 't es Vlaams! 🇧🇪
""")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Handle 'help' and 'version' before argparse
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 1:
        if argv[0] in ("help", "-h", "--help"):
            return cmd_help()
        if argv[0] == "haalp":
            return cmd_haalp()
        if argv[0] in ("version", "-v", "--version", "-V"):
            return cmd_version()

    p = argparse.ArgumentParser(
        prog="plats",
        description="VlaamsCodex - Platskript transpiler",
        epilog="For help: plats help | Docs: https://github.com/anubissbe/Vlaamse-Codex"
    )
    p.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True, metavar="command")

    p_run = sub.add_parser("run", help="Run a Platskript program")
    p_run.add_argument("path", type=Path, help="Path to .plats file")

    p_build = sub.add_parser("build", help="Compile to Python source file")
    p_build.add_argument("path", type=Path, help="Path to .plats file")
    p_build.add_argument("--out", type=Path, required=True, help="Output .py file")

    p_show = sub.add_parser("show-python", help="Display generated Python code")
    p_show.add_argument("path", type=Path, help="Path to .plats file")

    sub.add_parser("help", help="Show detailed help")
    sub.add_parser("haalp", help="Toon hulp in 't Vlaams")
    sub.add_parser("version", help="Show version")

    args = p.parse_args(argv)

    if args.cmd == "run":
        return cmd_run(args.path)
    if args.cmd == "build":
        return cmd_build(args.path, args.out)
    if args.cmd == "show-python":
        return cmd_show_python(args.path)
    if args.cmd == "help":
        return cmd_help()
    if args.cmd == "haalp":
        return cmd_haalp()
    if args.cmd == "version":
        return cmd_version()

    p.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
