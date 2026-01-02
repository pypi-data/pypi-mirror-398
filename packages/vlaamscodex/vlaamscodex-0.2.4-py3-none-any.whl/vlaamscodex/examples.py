"""Examples browser for Platskript - MULTI-VLAAMS! 🇧🇪

Browse and run examples with elk dialect:
  plats examples           (English)
  plats tuuntnekeer        (West-Vlaams: toon eens)
  plats toondada           (Antwerps: toon da da)
  plats loatskiejn         (Limburgs: laat 's kijken)
  plats ziedievoorbeelden  (Oost-Vlaams)
  plats toontmansen        (Brussels)
"""

from __future__ import annotations

import code
from pathlib import Path

# Examples command aliases (Multi-Vlaams!)
EXAMPLES_ALIASES = {
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
    "loatkieke": "examples",
    # Vlaams-Brabants
    "voorbeeldanse": "examples",
}

# Built-in examples with descriptions
BUILTIN_EXAMPLES = {
    "hello": {
        "name": "Hello World",
        "description": "Uw eerste programma - zegt 'gdag' aan de weeireld!",
        "code": """# coding: vlaamsplats
plan doe
  zet naam op tekst weeireld amen

  maak funksie groet met wie doe
    klap tekst gdag plakt spatie plakt tekst aan plakt spatie plakt da wie amen
  gedaan

  roep groet met da naam amen
gedaan
""",
    },
    "rekenen": {
        "name": "Rekenmachine",
        "description": "Basis rekenen met getallen",
        "code": """# coding: vlaamsplats
plan doe
  zet x op getal 10 amen
  zet y op getal 5 amen

  zet som op da x derbij da y amen
  klap da som amen

  zet verschil op da x deraf da y amen
  klap da verschil amen

  zet product op da x keer da y amen
  klap da product amen
gedaan
""",
    },
    "funksies": {
        "name": "Funksies",
        "description": "Maak en roep funksies aan!",
        "code": """# coding: vlaamsplats
plan doe
  maak funksie zeghallo met naam doe
    klap tekst hallo plakt spatie plakt da naam amen
  gedaan

  roep zeghallo met tekst Vlaanderen amen
  roep zeghallo met tekst Antwerpen amen
  roep zeghallo met tekst Brussel amen
gedaan
""",
    },
    "begroeting": {
        "name": "Begroeting",
        "description": "Verschillende begroetingen samenstellen",
        "code": """# coding: vlaamsplats
plan doe
  maak funksie begroet met naam doe
    klap tekst gdag plakt spatie plakt da naam amen
  gedaan

  roep begroet met tekst jansen amen
  roep begroet met tekst manneke amen
  roep begroet met tekst sansen amen
gedaan
""",
    },
    "teller": {
        "name": "Teller",
        "description": "Een simpele teller met variabelen",
        "code": """# coding: vlaamsplats
plan doe
  zet teller op getal 1 amen

  klap da teller amen
  zet teller op da teller derbij getal 1 amen
  klap da teller amen
  zet teller op da teller derbij getal 1 amen
  klap da teller amen
  zet teller op da teller derbij getal 1 amen
  klap da teller amen
  zet teller op da teller derbij getal 1 amen
  klap da teller amen
gedaan
""",
    },
}


def detect_examples_dialect(command: str) -> str:
    """Detect dialect from examples command alias."""
    if command in ("tuuntnekeer", "voorbeeldskes", "tuuntse"):
        return "west-vlaams"
    elif command in ("toondada", "voorbeeldekes"):
        return "antwerps"
    elif command in ("loatskiejn", "voorbeeldjes", "kiekenseffe"):
        return "limburgs"
    elif command in ("ziedievoorbeelden", "toontdie"):
        return "oost-vlaams"
    elif command in ("toontmansen", "voorbeeldansen"):
        return "brussels"
    elif command in ("jaowkiek", "loatkieke"):
        return "genks"
    return "default"


def list_examples(dialect: str = "default") -> None:
    """List all available examples."""
    headers = {
        "default": "Available Examples",
        "west-vlaams": "Voorbeeldskes",
        "antwerps": "Voorbeelden, manneke!",
        "limburgs": "Voorbeeldjes",
        "oost-vlaams": "Voorbeelden",
        "brussels": "Les exemples",
        "genks": "Voorbeelden jaow",
    }

    print(f"""
🇧🇪 {headers.get(dialect, headers['default'])}
{'=' * 50}
""")

    for key, example in BUILTIN_EXAMPLES.items():
        print(f"  {key:15} - {example['name']}")
        print(f"  {' ':15}   {example['description']}")
        print()

    print("=" * 50)
    print("""
Usage:
  plats examples --show <name>   Show the code
  plats examples --run <name>    Run the example
  plats examples --list          List all examples
""")


def show_example(name: str) -> int:
    """Show the code of an example."""
    if name not in BUILTIN_EXAMPLES:
        print(f"Example '{name}' not found!")
        print(f"Available: {', '.join(BUILTIN_EXAMPLES.keys())}")
        return 1

    example = BUILTIN_EXAMPLES[name]
    print(f"""
🇧🇪 {example['name']}
{'=' * 50}
{example['description']}

{example['code']}
""")
    return 0


def run_example(name: str) -> int:
    """Run an example using InteractiveConsole for safe execution."""
    if name not in BUILTIN_EXAMPLES:
        print(f"Example '{name}' not found!")
        print(f"Available: {', '.join(BUILTIN_EXAMPLES.keys())}")
        return 1

    from .compiler import compile_plats

    example = BUILTIN_EXAMPLES[name]
    source_code = example["code"]

    # Strip coding header
    lines = source_code.splitlines()
    if lines and "coding" in lines[0]:
        source_code = "\n".join(lines[1:])

    print(f"🇧🇪 Running: {example['name']}")
    print("=" * 40)
    print()

    try:
        py_code = compile_plats(source_code)
        # Use InteractiveConsole for safe code execution
        console = code.InteractiveConsole()
        console.runsource(py_code, f"<{name}.plats>", "exec")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    print()
    print("=" * 40)
    return 0


def save_example(name: str, path: Path | None = None) -> int:
    """Save an example to a file."""
    if name not in BUILTIN_EXAMPLES:
        print(f"Example '{name}' not found!")
        print(f"Available: {', '.join(BUILTIN_EXAMPLES.keys())}")
        return 1

    example = BUILTIN_EXAMPLES[name]

    if path is None:
        path = Path(f"{name}.plats")

    path.write_text(example["code"], encoding="utf-8")
    print(f"Saved '{name}' to {path}")
    return 0


def print_examples_help() -> int:
    """Print help for examples command."""
    print("""
🇧🇪 Platskript Examples Browser - MULTI-VLAAMS!

USAGE:
  plats examples                    List all examples
  plats examples --show <name>      Show example code
  plats examples --run <name>       Run an example
  plats examples --save <name>      Save example to file

MULTI-VLAAMS ALIASSEN:
  West-Vlaams   : plats tuuntnekeer
  Antwerps      : plats toondada
  Limburgs      : plats loatskiejn
  Oost-Vlaams   : plats ziedievoorbeelden
  Brussels      : plats toontmansen
  Genks         : plats jaowkiek

EXAMPLES:
  plats examples --run hello
  plats tuuntnekeer --show rekenen
  plats toondada --save funksies

AVAILABLE EXAMPLES:
""")
    for key, example in BUILTIN_EXAMPLES.items():
        print(f"  {key:15} - {example['name']}")

    print("\n't Es simpel, 't es plansen!\n")
    return 0


if __name__ == "__main__":
    print_examples_help()
