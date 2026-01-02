"""CLI for VlaamsCodex / Platskript - MULTI-VLAAMS EDITIE! 🇧🇪

Usage:
  plats run path/to/script.plats       (or: plats loop)
  plats build path/to/script.plats     (or: plats bouw)
  plats show-python path/to/script.plats (or: plats toon)
  plats help                           (or: plats haalp)
  plats version                        (or: plats versie)

Multi-Vlaams Dialect Aliassen:
  West-Vlaams  : loop, bouw, tuunt, haalp, versie
  Oost-Vlaams  : doeme, moaktme, toontme, hulpe, welke
  Antwerps     : doet, bouwt, toont, helptemij, versie
  Limburgs     : gaon, maakt, loatziejn, helpt, welke
  Brussels     : doeda, bouwtda, toonmansen, helpansen, welkansen
  Genks        : jaodoen, maktme, loatkieke, helptme, versje
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import compile_plats
from . import __version__
from .repl import run_repl, detect_dialect, REPL_ALIASES
from .fortune import print_fortune, detect_fortune_dialect, FORTUNE_ALIASES
from .init import create_project, detect_init_dialect, print_init_help, INIT_ALIASES
from .checker import check_file, detect_checker_dialect, print_checker_help, CHECKER_ALIASES
from .examples import (
    list_examples, show_example, run_example, save_example,
    detect_examples_dialect, print_examples_help, EXAMPLES_ALIASES
)

# =============================================================================
# MULTI-VLAAMS DIALECT ALIASSEN 🇧🇪
# =============================================================================
# Elke regio in Vlaanderen krijgt zijn eigen dialect aliassen!
#
# Regio's:
#   - West-Vlaams  : plansen, zacht
#   - Oost-Vlaams  : rap, direct
#   - Antwerps     : smos, ketjes
#   - Vlaams-Brabants : zenansen
#   - Limburgs     : zjweet, rustig
#   - Brussels     : zwansen, stoef
#   - Genks        : cité-taal
# =============================================================================

# Command aliases: All Flemish dialects -> English
COMMAND_ALIASES = {
    # === RUN COMMAND ===
    # Standard Flemish
    "loop": "run",
    # West-Vlaams
    "voertuut": "run",
    # Oost-Vlaams
    "doeme": "run",
    "komaan": "run",
    # Antwerps
    "doet": "run",
    "doeda": "run",
    # Vlaams-Brabants
    "startop": "run",
    # Limburgs
    "gaon": "run",
    # Brussels
    "doedansen": "run",
    # Genks
    "jaodoen": "run",

    # === BUILD COMMAND ===
    # Standard Flemish
    "bouw": "build",
    # West-Vlaams
    "moakt": "build",
    # Oost-Vlaams
    "moaktme": "build",
    # Antwerps
    "bouwt": "build",
    # Vlaams-Brabants
    "maakda": "build",
    # Limburgs
    "maakt": "build",
    # Brussels
    "bouwtda": "build",
    # Genks
    "maktme": "build",

    # === SHOW-PYTHON COMMAND ===
    # Standard Flemish
    "toon": "show-python",
    # West-Vlaams
    "tuunt": "show-python",
    "tuuntnekeer": "show-python",
    # Oost-Vlaams
    "toontme": "show-python",
    # Antwerps
    "toont": "show-python",
    "toondada": "show-python",
    # Vlaams-Brabants
    "loatkiejke": "show-python",
    # Limburgs
    "loatziejn": "show-python",
    "loatskiejn": "show-python",
    # Brussels
    "toonmansen": "show-python",
    # Genks
    "loatkieke": "show-python",

    # === HELP COMMAND ===
    # Standard Flemish
    "haalp": "help",
    # West-Vlaams
    "hulpe": "help",
    # Oost-Vlaams
    "hulpme": "help",
    # Antwerps
    "helptemij": "help",
    # Vlaams-Brabants
    "helpme": "help",
    # Limburgs
    "helpt": "help",
    # Brussels
    "helpansen": "help",
    # Genks
    "helptme": "help",

    # === VERSION COMMAND ===
    # Standard Flemish
    "versie": "version",
    # West-Vlaams
    "welke": "version",
    # Oost-Vlaams
    "welkversie": "version",
    # Antwerps (same as standard)
    # Vlaams-Brabants
    "watversie": "version",
    # Limburgs (same as West-Vlaams)
    # Brussels
    "welkansen": "version",
    # Genks
    "versje": "version",

    # === REPL COMMAND (NEW!) ===
    # West-Vlaams
    "proboir": "repl",
    # Antwerps
    "smos": "repl",
    "smossen": "repl",
    # Limburgs
    "efkes": "repl",
    "efkesproberen": "repl",
    # Brussels
    "klansen": "repl",
    "zwansen": "repl",
    # Oost-Vlaams
    "probeer": "repl",
    "probeertme": "repl",
    # Genks
    "probeirme": "repl",
    # Vlaams-Brabants
    "probeerdansen": "repl",

    # === FORTUNE COMMAND (Easter Egg!) ===
    # West-Vlaams
    "zegt": "fortune",
    "zenmoederzegt": "fortune",
    "spreuke": "fortune",
    # Antwerps
    "watteda": "fortune",
    "manneke": "fortune",
    # Limburgs
    "wiste": "fortune",
    "wistedak": "fortune",
    # Brussels
    "zansen": "fortune",
    "eikes": "fortune",
    # Oost-Vlaams
    "spreuk": "fortune",
    "gezegd": "fortune",
    # Genks
    "jaow": "fortune",
    # Vlaams-Brabants
    "zegansen": "fortune",

    # === INIT COMMAND (Project Scaffolding) ===
    # West-Vlaams
    "allehop": "init",
    "startop": "init",
    "beginme": "init",
    # Antwerps
    "awel": "init",
    "aweldan": "init",
    # Limburgs
    "allei": "init",
    "gaonme": "init",
    # Oost-Vlaams
    "komaan": "init",
    "komme": "init",
    # Brussels
    "allez": "init",
    "allezdan": "init",
    # Genks
    "jaowel": "init",
    # Vlaams-Brabants
    "startdansen": "init",

    # === CHECK COMMAND (Syntax Checker) ===
    # West-Vlaams
    "zijdezekers": "check",
    "zekers": "check",
    "okeej": "check",
    # Antwerps
    "istdagoe": "check",
    "isdatgoe": "check",
    "goeddansen": "check",
    # Limburgs
    "kloptda": "check",
    "kloptdat": "check",
    "goedzowie": "check",
    # Oost-Vlaams
    "zalkdagaan": "check",
    "checktem": "check",
    # Brussels
    "passedat": "check",
    "camarche": "check",
    # Genks
    "jaowklopt": "check",
    "probeircheck": "check",
    # Vlaams-Brabants
    "checkdansen": "check",

    # === EXAMPLES COMMAND (Examples Browser) ===
    # West-Vlaams
    "tuuntnekeer": "examples",
    "voorbeeldskes": "examples",
    "tuuntse": "examples",
    # Antwerps
    "toondada": "examples",
    "voorbeeldekes": "examples",
    # Limburgs
    "loatskiejn": "examples",
    "voorbeeldjes": "examples",
    "kiekenseffe": "examples",
    # Oost-Vlaams
    "ziedievoorbeelden": "examples",
    "toontdie": "examples",
    # Brussels
    "toontmansen": "examples",
    "voorbeeldansen": "examples",
    # Genks
    "jaowkiek": "examples",
    # Vlaams-Brabants
    "voorbeeldanse": "examples",
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
VlaamsCodex v{__version__} - Platskript Transpiler - MULTI-VLAAMS EDITIE! 🇧🇪
=============================================================================

A transpiler for Platskript (.plats), a parody programming language
that uses Flemish dialect keywords and compiles to Python.

COMMANDS (English):
  plats run <file.plats>                Run a Platskript program
  plats build <file.plats> --out <file> Compile to Python source file
  plats show-python <file.plats>        Display generated Python code
  plats help                            Show this help message
  plats version                         Show version information

MULTI-VLAAMS DIALECTEN! 🇧🇪
Elke regio heeft zijn eigen commando's:

  RUN (voer uut):
    West-Vlaams   : plats loop / plats voertuut
    Oost-Vlaams   : plats doeme / plats komaan
    Antwerps      : plats doet / plats doeda
    Limburgs      : plats gaon
    Brussels      : plats doedansen
    Genks         : plats jaodoen

  BUILD (bouw):
    West-Vlaams   : plats bouw / plats moakt
    Oost-Vlaams   : plats moaktme
    Antwerps      : plats bouwt
    Limburgs      : plats maakt
    Brussels      : plats bouwtda
    Genks         : plats maktme

  SHOW-PYTHON (toon):
    West-Vlaams   : plats toon / plats tuunt / plats tuuntnekeer
    Oost-Vlaams   : plats toontme
    Antwerps      : plats toont / plats toondada
    Limburgs      : plats loatziejn / plats loatskiejn
    Brussels      : plats toonmansen
    Genks         : plats loatkieke

  HELP (hulp):
    West-Vlaams   : plats haalp / plats hulpe
    Oost-Vlaams   : plats hulpme
    Antwerps      : plats helptemij
    Limburgs      : plats helpt
    Brussels      : plats helpansen
    Genks         : plats helptme

  VERSION (versie):
    Standard      : plats versie
    West-Vlaams   : plats welke
    Brussels      : plats welkansen
    Genks         : plats versje

MAGIC MODE:
  python <file.plats>                   Run directly with Python!

EXAMPLES:
  plats run hello.plats                 Run a program
  plats loop hello.plats                West-Vlaams!
  plats doet hello.plats                Antwerps!
  plats gaon hello.plats                Limburgs!

QUICK START:
  1. Create a file 'hello.plats':

     # coding: vlaamsplats
     plan doe
       klap tekst gdag wereld amen
     gedaan

  2. Run it (pick your dialect!):
     plats run hello.plats      (English)
     plats loop hello.plats     (West-Vlaams)
     plats doet hello.plats     (Antwerps)
     plats gaon hello.plats     (Limburgs)

For more info: https://github.com/anubissbe/Vlaamse-Codex
""")
    return 0


def cmd_version() -> int:
    print(f"VlaamsCodex v{__version__}")
    return 0


def cmd_repl(dialect: str = "default") -> int:
    """Start the interactive REPL."""
    return run_repl(dialect=dialect)


def cmd_fortune(dialect: str | None = None) -> int:
    """Show a random Flemish fortune/proverb."""
    return print_fortune(dialect=dialect)


def cmd_init(name: str | None = None, dialect: str = "default") -> int:
    """Initialize a new Platskript project."""
    if name is None:
        return print_init_help()
    return create_project(name, dialect=dialect)


def cmd_check(path: Path | None = None, dialect: str = "default") -> int:
    """Check Platskript syntax with Flemish error messages."""
    if path is None:
        return print_checker_help()
    success, message = check_file(path, dialect=dialect)
    print(message)
    return 0 if success else 1


def cmd_examples(
    show: str | None = None,
    run: str | None = None,
    save: str | None = None,
    dialect: str = "default"
) -> int:
    """Browse and run built-in examples."""
    if show:
        return show_example(show)
    if run:
        return run_example(run)
    if save:
        return save_example(save)
    list_examples(dialect)
    return 0


def cmd_haalp() -> int:
    print(f"""
VlaamsCodex v{__version__} - Platskansen Vertoaler - MULTI-VLAAMS! 🇧🇪
======================================================================

Een vertoaler vo Platskript (.plats), ne parodie programmeertaal
die Vlaamse dialectwoorden gebruukt en compileert na Python.

MULTI-VLAAMS DIALECTEN! 🇧🇪
Elke regio in Vlaanderen krijgt zen eigen commando's:

  LOOP (voer uut):
    West-Vlaams   : plats loop / plats voertuut
    Oost-Vlaams   : plats doeme / plats komaan
    Antwerps      : plats doet / plats doeda
    Limburgs      : plats gaon
    Brussels      : plats doedansen
    Genks         : plats jaodoen

  BOUW (compileer):
    West-Vlaams   : plats bouw / plats moakt
    Oost-Vlaams   : plats moaktme
    Antwerps      : plats bouwt
    Limburgs      : plats maakt
    Brussels      : plats bouwtda
    Genks         : plats maktme

  TOON (Python code):
    West-Vlaams   : plats toon / plats tuunt / plats tuuntnekeer
    Oost-Vlaams   : plats toontme
    Antwerps      : plats toont / plats toondada
    Limburgs      : plats loatziejn / plats loatskiejn
    Brussels      : plats toonmansen
    Genks         : plats loatkieke

  HAALP (hulp):
    West-Vlaams   : plats haalp / plats hulpe
    Oost-Vlaams   : plats hulpme
    Antwerps      : plats helptemij
    Limburgs      : plats helpt
    Brussels      : plats helpansen
    Genks         : plats helptme

MAGISCHE MODUS:
  python <bestand.plats>                  Direct uitvoeren me Python!

VOORBEELDEN:
  plats loop hallo.plats                  West-Vlaams
  plats doet hallo.plats                  Antwerps
  plats gaon hallo.plats                  Limburgs
  plats doeme hallo.plats                 Oost-Vlaams

SNE STARTEN:
  1. Mokt een bestand 'hallo.plats':

     # coding: vlaamsplats
     plan doe
       klap tekst gdag weeireld amen
     gedaan

  2. Voer 't uut (kiest uw dialect!):
     plats loop hallo.plats     (West-Vlaams)
     plats doet hallo.plats     (Antwerps)
     plats gaon hallo.plats     (Limburgs)

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

't Es simpel, 't es plansen, 't es Multi-Vlaams! 🇧🇪
""")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Handle 'help' and 'version' before argparse
    if argv is None:
        argv = sys.argv[1:]

    # Save original command for dialect detection (before translation)
    original_cmd = argv[0] if argv else ""

    # Translate Flemish aliases to English commands
    if argv and argv[0] in COMMAND_ALIASES:
        argv = [COMMAND_ALIASES[argv[0]]] + argv[1:]

    # Quick handlers for simple commands (no args needed)
    if len(argv) == 1:
        if argv[0] in ("help", "-h", "--help"):
            return cmd_help()
        if argv[0] in ("version", "-v", "--version", "-V", "versie"):
            return cmd_version()
        if argv[0] == "repl":
            # Detect dialect from original command
            dialect = detect_dialect(original_cmd)
            return cmd_repl(dialect=dialect)
        if argv[0] == "fortune":
            # Detect dialect from original command for fortune
            dialect = detect_fortune_dialect(original_cmd)
            return cmd_fortune(dialect=dialect)

    # No args? Start the REPL!
    if not argv:
        return cmd_repl()

    p = argparse.ArgumentParser(
        prog="plats",
        description="VlaamsCodex - Platskript transpiler - MULTI-VLAAMS! 🇧🇪 (West-Vlaams, Antwerps, Limburgs, Brussels, Genks...)",
        epilog="Multi-Vlaams help: plats help | plats haalp | plats doet/gaon/jaodoen work too! | https://github.com/anubissbe/Vlaamse-Codex"
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

    # REPL command (Multi-Vlaams!)
    sub.add_parser("repl", help="Start interactive REPL (proboir/smos/efkes/klansen)")

    # Fortune command (Easter Egg! Multi-Vlaams!)
    sub.add_parser("fortune", help="Vlaamse wijsheid! (zegt/watteda/wiste/zansen)")

    # Init command (Project Scaffolding! Multi-Vlaams!)
    p_init = sub.add_parser("init", help="Create new project (allehop/awel/allei/komaan)")
    p_init.add_argument("name", nargs="?", help="Project name")

    # Check command (Syntax Checker! Multi-Vlaams!)
    p_check = sub.add_parser("check", help="Check syntax (zijdezekers/istdagoe/kloptda)")
    p_check.add_argument("path", type=Path, nargs="?", help="Path to .plats file")

    # Examples command (Examples Browser! Multi-Vlaams!)
    p_examples = sub.add_parser("examples", help="Browse examples (tuuntnekeer/toondada/loatskiejn)")
    p_examples.add_argument("--show", metavar="NAME", help="Show example code")
    p_examples.add_argument("--run", metavar="NAME", help="Run an example")
    p_examples.add_argument("--save", metavar="NAME", help="Save example to file")

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
    if args.cmd == "repl":
        dialect = detect_dialect(original_cmd)
        return cmd_repl(dialect=dialect)
    if args.cmd == "fortune":
        dialect = detect_fortune_dialect(original_cmd)
        return cmd_fortune(dialect=dialect)
    if args.cmd == "init":
        dialect = detect_init_dialect(original_cmd)
        return cmd_init(name=args.name, dialect=dialect)
    if args.cmd == "check":
        dialect = detect_checker_dialect(original_cmd)
        return cmd_check(path=args.path, dialect=dialect)
    if args.cmd == "examples":
        dialect = detect_examples_dialect(original_cmd)
        return cmd_examples(show=args.show, run=args.run, save=args.save, dialect=dialect)
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
