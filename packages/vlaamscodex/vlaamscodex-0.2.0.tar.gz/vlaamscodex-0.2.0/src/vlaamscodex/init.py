"""Project scaffolding for Platskript - MULTI-VLAAMS! 🇧🇪

Start een nieuw project met elk dialect da ge wilt:
  plats init myproject    (English)
  plats allehop mijnproj  (West-Vlaams: hier gaan we!)
  plats awel mijnproj     (Antwerps: kom, we beginnen)
  plats allei mijnproj    (Limburgs: vooruit dan)
  plats komaan mijnproj   (Oost-Vlaams)
  plats allez mijnproj    (Brussels)
  plats jaowel mijnproj   (Genks)
"""

from __future__ import annotations

from pathlib import Path

# Init command aliases (Multi-Vlaams!)
INIT_ALIASES = {
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
    "jaodoen": "init",
    # Vlaams-Brabants
    "startdansen": "init",
}

# Template for hello.plats
HELLO_PLATS = """# coding: vlaamsplats
# 🇧🇪 Uw eerste Platskript programma!

plan doe
  # Stel een variabele in
  zet naam op tekst weeireld amen

  # Maak een funksie
  maak funksie groet met wie doe
    klap tekst gdag plakt spatie plakt tekst aan plakt spatie plakt da wie amen
  gedaan

  # Roep de funksie aan
  roep groet met da naam amen
gedaan
"""

# Template for README (in Flemish!)
LEESMIJ_MD = """# {project_name} - Platskript Project 🇧🇪

Welkom bij uw nieuw Platskript project!

## Snel Starten

### Voer uw programma uit (kies uw dialect!)

```bash
# English
plats run hallo.plats

# West-Vlaams
plats loop hallo.plats

# Antwerps
plats doet hallo.plats

# Limburgs
plats gaon hallo.plats

# Oost-Vlaams
plats doeme hallo.plats

# Brussels
plats doedansen hallo.plats

# Genks
plats jaodoen hallo.plats
```

### Of direct met Python (Magic Mode!)

```bash
python hallo.plats
```

## Platskript Taal Referentie

| Syntax | Beschrijving |
|--------|--------------|
| `plan doe ... gedaan` | Begin en einde van programma |
| `zet X op Y amen` | Variabele toewijzing |
| `klap X amen` | Print naar scherm |
| `maak funksie X doe ... gedaan` | Functie definitie |
| `roep X met Y amen` | Functie aanroep |
| `geeftterug X amen` | Return statement |
| `tekst woorden` | String literal |
| `getal 123` | Nummer literal |
| `da X` | Variabele referentie |
| `plakt` | String concatenatie |
| `spatie` | Spatie karakter |

## Nuttige Commands

```bash
# Start interactieve REPL
plats repl      # of: plats proboir / plats smos / plats efkes

# Toon gegenereerde Python
plats toon hallo.plats

# Compileer naar Python bestand
plats bouw hallo.plats --out hallo.py

# Vlaamse wijsheid!
plats fortune   # of: plats zegt / plats watteda / plats wiste
```

## Meer Informatie

- GitHub: https://github.com/anubissbe/Vlaamse-Codex
- PyPI: https://pypi.org/project/vlaamscodex/

---

't Es simpel, 't es plansen, 't es Multi-Vlaams! 🇧🇪
"""

# Welcome messages per dialect
WELCOME_MESSAGES = {
    "west-vlaams": """
🇧🇪 Allehop! Uw project '{name}' es aangemaakt!

   Begint met:
     cd {name}
     plats loop hallo.plats
""",
    "antwerps": """
🇧🇪 Awel manneke! Uw project '{name}' is aangemaakt!

   Begint met:
     cd {name}
     plats doet hallo.plats
""",
    "limburgs": """
🇧🇪 Allei! Uw project '{name}' is aangemaakt!

   Begint met:
     cd {name}
     plats gaon hallo.plats
""",
    "oost-vlaams": """
🇧🇪 Komaan! Uw project '{name}' is aangemaakt!

   Begint met:
     cd {name}
     plats doeme hallo.plats
""",
    "brussels": """
🇧🇪 Allez! Uw project '{name}' est aangemaakt!

   Begint met:
     cd {name}
     plats doedansen hallo.plats
""",
    "genks": """
🇧🇪 Jaow! Uw project '{name}' is aangemaakt!

   Begint met:
     cd {name}
     plats jaodoen hallo.plats
""",
    "default": """
🇧🇪 Project '{name}' created successfully!

   Get started:
     cd {name}
     plats run hallo.plats
""",
}


def detect_init_dialect(command: str) -> str:
    """Detect dialect from init command alias."""
    if command in ("allehop", "startop", "beginme"):
        return "west-vlaams"
    elif command in ("awel", "aweldan"):
        return "antwerps"
    elif command in ("allei", "gaonme"):
        return "limburgs"
    elif command in ("komaan", "komme"):
        return "oost-vlaams"
    elif command in ("allez", "allezdan"):
        return "brussels"
    elif command in ("jaowel", "jaodoen"):
        return "genks"
    return "default"


def create_project(name: str, dialect: str = "default") -> int:
    """Create a new Platskript project.

    Args:
        name: Project name (will be used as directory name)
        dialect: Dialect for welcome message

    Returns:
        Exit code (0 for success)
    """
    project_dir = Path(name)

    # Check if directory already exists
    if project_dir.exists():
        print(f"Error: Directory '{name}' already exists!")
        print("  Tip: Choose a different name or remove the existing directory.")
        return 1

    # Create project structure
    try:
        project_dir.mkdir(parents=True)

        # Create hallo.plats
        (project_dir / "hallo.plats").write_text(HELLO_PLATS, encoding="utf-8")

        # Create LEESMIJ.md (README in Flemish)
        readme_content = LEESMIJ_MD.format(project_name=name)
        (project_dir / "LEESMIJ.md").write_text(readme_content, encoding="utf-8")

        # Show welcome message
        welcome = WELCOME_MESSAGES.get(dialect, WELCOME_MESSAGES["default"])
        print(welcome.format(name=name))

        return 0

    except OSError as e:
        print(f"Error creating project: {e}")
        return 1


def print_init_help() -> int:
    """Print help for init command."""
    print("""
🇧🇪 Platskript Project Scaffolding - MULTI-VLAAMS!

USAGE:
  plats init <project-name>

MULTI-VLAAMS ALIASSEN:
  West-Vlaams   : plats allehop <naam>
  Antwerps      : plats awel <naam>
  Limburgs      : plats allei <naam>
  Oost-Vlaams   : plats komaan <naam>
  Brussels      : plats allez <naam>
  Genks         : plats jaowel <naam>

EXAMPLES:
  plats init myproject
  plats allehop mijnproject
  plats awel mijnproject

CREATED FILES:
  <project>/
  ├── hallo.plats    Sample Platskript program
  └── LEESMIJ.md     Quick start guide (in Flemish!)

't Es simpel, 't es plansen!
""")
    return 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        create_project(sys.argv[1])
    else:
        print_init_help()
