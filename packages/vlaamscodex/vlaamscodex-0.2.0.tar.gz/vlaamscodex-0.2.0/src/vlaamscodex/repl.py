"""Interactive REPL for Platskript - MULTI-VLAAMS! 🇧🇪

Start de REPL met elk dialect da ge wilt:
  plats repl          (English)
  plats proboir       (West-Vlaams: proberen)
  plats smos          (Antwerps: praten/uitproberen)
  plats efkes         (Limburgs: eventjes)
  plats klansen       (Brussels: klappen/babbelen)
  plats probeer       (Oost-Vlaams)
  plats probeirme     (Genks)
"""

from __future__ import annotations

import code
import sys
from typing import TextIO

from .compiler import compile_plats

# REPL command aliases (Multi-Vlaams!)
REPL_ALIASES = {
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
}

# Flemish prompts for different dialects
PROMPTS = {
    "west-vlaams": ("plansen> ", "  ... "),
    "antwerps": ("sansen> ", "  ... "),
    "limburgs": ("allei> ", "  ... "),
    "brussels": ("awel> ", "  ... "),
    "default": ("plats> ", "  ... "),
}

# Welcome messages per dialect
WELCOME_MESSAGES = {
    "west-vlaams": """
🇧🇪 Welkom in de Platskript REPL! (West-Vlaams mode)
   Typt 'n programma en 't wordt direct uutgevoerd.
   Commands: .haalp, .tuunt, .weg

   Tip: Begint me 'plan doe' en eindigt me 'gedaan'
""",
    "antwerps": """
🇧🇪 Welkom in de Platskript REPL! (Antwerps mode)
   Typt ne programma en 't wordt direct uitgevoerd, manneke!
   Commands: .helptemij, .toont, .weg

   Tip: Begint me 'plan doe' en eindigt me 'gedaan'
""",
    "limburgs": """
🇧🇪 Welkom in de Platskript REPL! (Limburgs mode)
   Tiept 'n programma en 't weurt direct oetgevoerd.
   Commands: .helpt, .loatziejn, .wech

   Tip: Begint met 'plan doe' en eindigt met 'gedaan'
""",
    "default": """
🇧🇪 Welkom in de Platskript REPL! (Multi-Vlaams mode)
   Type a program and it will be executed immediately.
   Commands: .help, .show, .exit

   Tip: Start with 'plan doe' and end with 'gedaan'
""",
}

# Exit commands
EXIT_COMMANDS = {".exit", ".quit", ".weg", ".wech", ".stop", ".gedaan"}

# Help commands
HELP_COMMANDS = {".help", ".haalp", ".hulpe", ".helptemij", ".helpt", ".helpansen"}

# Show Python commands
SHOW_COMMANDS = {".show", ".toon", ".tuunt", ".toont", ".loatziejn", ".toondada"}


def detect_dialect(command: str) -> str:
    """Detect which dialect the user started the REPL with."""
    if command in ("proboir", "voertuut"):
        return "west-vlaams"
    elif command in ("smos", "smossen", "doet"):
        return "antwerps"
    elif command in ("efkes", "gaon"):
        return "limburgs"
    elif command in ("klansen", "zwansen"):
        return "brussels"
    else:
        return "default"


class PlatsREPL:
    """Interactive REPL for Platskript using Python's code module."""

    def __init__(
        self,
        dialect: str = "default",
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
    ):
        self.dialect = dialect
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.prompt, self.continuation = PROMPTS.get(dialect, PROMPTS["default"])
        self.buffer: list[str] = []
        self.last_code: str = ""
        self.running = True
        # Use Python's code.InteractiveConsole for safe code execution
        self.console = code.InteractiveConsole()

    def write(self, text: str) -> None:
        """Write to output stream."""
        self.output_stream.write(text)
        self.output_stream.flush()

    def show_welcome(self) -> None:
        """Show welcome message."""
        msg = WELCOME_MESSAGES.get(self.dialect, WELCOME_MESSAGES["default"])
        self.write(msg)

    def show_help(self) -> None:
        """Show help message."""
        self.write("""
Platskript REPL Commands:
  .help / .haalp        Show this help
  .show / .toon         Show generated Python for last input
  .exit / .weg          Exit the REPL
  .clear / .wis         Clear the screen
  .reset / .opnieuw     Reset the environment

Language Quick Reference:
  plan doe ... gedaan   Program wrapper
  zet X op Y amen       Variable assignment
  klap X amen           Print
  maak funksie N doe    Define function
  roep F met X amen     Call function
  tekst woorden         String literal
  getal 123             Number literal
  da X                  Variable reference
  plakt                 String concatenation
""")

    def show_python(self, code_str: str) -> None:
        """Show generated Python code."""
        try:
            py_code = compile_plats(code_str)
            self.write(f"\n--- Generated Python ---\n{py_code}--- End ---\n\n")
        except Exception as e:
            self.write(f"Error: {e}\n")

    def is_complete(self, code_str: str) -> bool:
        """Check if code block is complete (all 'plan doe' closed with 'gedaan')."""
        opens = code_str.count("plan doe") + code_str.count("maak funksie")
        closes = code_str.count("gedaan")
        return opens <= closes

    def run_platskript(self, plats_code: str) -> None:
        """Compile Platskript to Python and run it."""
        try:
            py_code = compile_plats(plats_code)
            self.last_code = plats_code
            # Use InteractiveConsole to run the Python code safely
            self.console.runsource(py_code, "<platskript>", "exec")
        except Exception as e:
            self.write(f"\n❌ Fout: {e}\n")

    def handle_command(self, line: str) -> bool:
        """Handle REPL commands. Returns True if command was handled."""
        line_lower = line.strip().lower()

        if line_lower in EXIT_COMMANDS:
            self.write("\n👋 Tot ziens! / Salut! / Ciao!\n")
            self.running = False
            return True

        if line_lower in HELP_COMMANDS:
            self.show_help()
            return True

        if line_lower in SHOW_COMMANDS:
            if self.last_code:
                self.show_python(self.last_code)
            else:
                self.write("Nothing to show. Enter some code first.\n")
            return True

        if line_lower in (".clear", ".wis", ".kuisen"):
            self.write("\033[2J\033[H")  # ANSI clear screen
            return True

        if line_lower in (".reset", ".opnieuw", ".herstart"):
            self.console = code.InteractiveConsole()
            self.buffer = []
            self.last_code = ""
            self.write("🔄 Environment reset.\n")
            return True

        return False

    def run(self) -> None:
        """Run the REPL."""
        self.show_welcome()

        while self.running:
            try:
                # Show appropriate prompt
                if self.buffer:
                    prompt = self.continuation
                else:
                    prompt = self.prompt

                self.write(prompt)
                line = self.input_stream.readline()

                if not line:  # EOF
                    self.write("\n👋 Tot ziens!\n")
                    break

                line = line.rstrip("\n")

                # Handle empty lines
                if not line.strip():
                    if self.buffer:
                        # Empty line in multiline mode - try to run
                        plats_code = "\n".join(self.buffer)
                        if self.is_complete(plats_code):
                            self.run_platskript(plats_code)
                            self.buffer = []
                    continue

                # Handle REPL commands
                if line.startswith("."):
                    if self.handle_command(line):
                        continue

                # Add to buffer
                self.buffer.append(line)
                plats_code = "\n".join(self.buffer)

                # Check if code is complete
                if self.is_complete(plats_code):
                    self.run_platskript(plats_code)
                    self.buffer = []

            except KeyboardInterrupt:
                self.write("\n^C\n")
                self.buffer = []
            except EOFError:
                self.write("\n👋 Tot ziens!\n")
                break


def run_repl(dialect: str = "default") -> int:
    """Run the Platskript REPL."""
    repl = PlatsREPL(dialect=dialect)
    repl.run()
    return 0


if __name__ == "__main__":
    run_repl()
