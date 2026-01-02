"""CLI for VlaamsCodex / Platskript.

Usage:
  plats run path/to/script.plats       (or: plats loop)
  plats build path/to/script.plats     (or: plats bouw)
  plats show-python path/to/script.plats (or: plats toon)
  plats help                           (or: plats haalp)
  plats version                        (or: plats versie)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import compile_plats

__version__ = "0.1.6"

# Command aliases: Flemish -> English
COMMAND_ALIASES = {
    "loop": "run",
    "bouw": "build",
    "toon": "show-python",
    "haalp": "help",
    "versie": "version",
}


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

COMMANDS (English):
  plats run <file.plats>                Run a Platskript program
  plats build <file.plats> --out <file> Compile to Python source file
  plats show-python <file.plats>        Display generated Python code
  plats help                            Show this help message
  plats version                         Show version information

COMMANDO'S (Vlaams):
  plats loop <bestand.plats>            Voer een programma uut
  plats bouw <bestand.plats> --out <f>  Compileer na Python
  plats toon <bestand.plats>            Toon de Python code
  plats haalp                           Hulp in 't Vlaams
  plats versie                          Toon versie

Note: Flemish commands are full aliases - they work exactly like
      their English counterparts. Use whichever you prefer!

MAGIC MODE:
  python <file.plats>                   Run directly with Python!

EXAMPLES:
  plats run hello.plats                 Run a program
  plats loop hello.plats                Same, but in Flemish!
  plats show-python hello.plats         See the Python output
  plats toon hello.plats                Same, but in Flemish!
  plats build hello.plats --out out.py  Compile to .py file
  python hello.plats                    Magic mode (requires install)

QUICK START:
  1. Create a file 'hello.plats':

     # coding: vlaamsplats
     plan doe
       klap tekst gdag wereld amen
     gedaan

  2. Run it:
     plats run hello.plats   (or: plats loop hello.plats)

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

VLAAMSE COMMANDO'S:
  plats loop <bestand.plats>              Voer een Platskript programma uut
  plats bouw <bestand.plats> --out <file> Compileer na Python broncode
  plats toon <bestand.plats>              Toon de gegenereerde Python code
  plats haalp                             Toon dees hulp bericht
  plats versie                            Toon versie informatie

ENGELSE ALTERNATIEVEN:
  plats run      (= loop)                 Run a program
  plats build    (= bouw)                 Compile to Python
  plats show-python (= toon)              Show generated Python
  plats help     (= haalp)                Help in English
  plats version  (= versie)               Show version

Nota: De Vlaamse en Engelse commando's zijn volledig gelijkwaardig.
      Gebruukt gerust welke da ge wilt!

MAGISCHE MODUS:
  python <bestand.plats>                  Direct uitvoeren me Python!

VOORBEELDEN:
  plats loop hallo.plats                  Voer een programma uut
  plats toon hallo.plats                  Bekijk de Python output
  plats bouw hallo.plats --out uit.py     Compileer na .py bestand
  python hallo.plats                      Magische modus

SNE STARTEN:
  1. Mokt een bestand 'hallo.plats':

     # coding: vlaamsplats
     plan doe
       klap tekst gdag weeireld amen
     gedaan

  2. Voer 't uut:
     plats loop hallo.plats

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

    # Translate Flemish aliases to English commands
    if argv and argv[0] in COMMAND_ALIASES:
        argv = [COMMAND_ALIASES[argv[0]]] + argv[1:]

    # Quick handlers for simple commands
    if len(argv) == 1:
        if argv[0] in ("help", "-h", "--help"):
            return cmd_help()
        if argv[0] in ("version", "-v", "--version", "-V", "versie"):
            return cmd_version()

    p = argparse.ArgumentParser(
        prog="plats",
        description="VlaamsCodex - Platskript transpiler (Flemish aliases: loop, bouw, toon, haalp, versie)",
        epilog="For help: plats help | Vo haalp: plats haalp | Docs: https://github.com/anubissbe/Vlaamse-Codex"
    )
    p.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True, metavar="command")

    # English commands
    p_run = sub.add_parser("run", help="Run a Platskript program", aliases=["loop"])
    p_run.add_argument("path", type=Path, help="Path to .plats file")

    p_build = sub.add_parser("build", help="Compile to Python source file", aliases=["bouw"])
    p_build.add_argument("path", type=Path, help="Path to .plats file")
    p_build.add_argument("--out", type=Path, required=True, help="Output .py file")

    p_show = sub.add_parser("show-python", help="Display generated Python code", aliases=["toon"])
    p_show.add_argument("path", type=Path, help="Path to .plats file")

    sub.add_parser("help", help="Show detailed help (English)")
    sub.add_parser("haalp", help="Toon hulp in 't Vlaams")
    sub.add_parser("version", help="Show version", aliases=["versie"])

    args = p.parse_args(argv)

    if args.cmd in ("run", "loop"):
        return cmd_run(args.path)
    if args.cmd in ("build", "bouw"):
        return cmd_build(args.path, args.out)
    if args.cmd in ("show-python", "toon"):
        return cmd_show_python(args.path)
    if args.cmd == "help":
        return cmd_help()
    if args.cmd == "haalp":
        return cmd_haalp()
    if args.cmd in ("version", "versie"):
        return cmd_version()

    p.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
