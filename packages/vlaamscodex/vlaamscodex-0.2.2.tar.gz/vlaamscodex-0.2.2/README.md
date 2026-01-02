# VlaamsCodex - Multi-Vlaams Editie 🇧🇪

[![PyPI version](https://img.shields.io/pypi/v/vlaamscodex.svg)](https://pypi.org/project/vlaamscodex/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/vlaamscodex.svg)](https://pypi.org/project/vlaamscodex/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/brentishere41848/Vlaamse-Codex/actions/workflows/ci.yml/badge.svg)](https://github.com/brentishere41848/Vlaamse-Codex/actions/workflows/ci.yml)

> **'t Es simpel, 't es plansen, 't es Vlaams!**

A transpiler toolchain for **Platskript** (`.plats`), a parody programming language that uses Flemish dialect keywords. VlaamsCodex compiles Platskript source code to Python and executes it.

**NEW in v0.2.0**: Full Multi-Vlaams dialect support with 80+ command aliases from all Flemish regions!

---

## Quick Start

```bash
# Install
pip install vlaamscodex

# Run your first program
plats run examples/hello.plats

# Or use magic mode - run .plats directly with Python!
python examples/hello.plats
```

Output:
```
gdag aan weeireld
```

---

## Multi-Vlaams Dialect Commands 🇧🇪

Every command works in **7 Flemish dialects**! Use whichever feels most natural:

### Run a Program

| Dialect | Command | Meaning |
|---------|---------|---------|
| English | `plats run script.plats` | Run |
| West-Vlaams | `plats voertuut script.plats` | Voer 't uut |
| Antwerps | `plats doet script.plats` | Doe 't |
| Limburgs | `plats gaon script.plats` | Gaan |
| Brussels | `plats doeda script.plats` | Doe da |

### Interactive REPL

```bash
plats repl              # English
plats proboir           # West-Vlaams: proberen
plats smos              # Antwerps: praten/uitproberen
plats efkes             # Limburgs: eventjes
plats praot             # Brussels: praten
```

### Browse Examples

```bash
plats examples              # List all examples
plats tuuntnekeer           # West-Vlaams: toon eens
plats toondada              # Antwerps: toon da da
plats loatskiejn            # Limburgs: laat 's kijken
plats examples --run hello  # Run an example
```

### Check Syntax

```bash
plats check script.plats        # English
plats zijdezekers script.plats  # West-Vlaams: zijt ge zeker?
plats istdagoe script.plats     # Antwerps: is da goe?
plats kloptda script.plats      # Limburgs: klopt da?
```

Error messages come in your dialect:
```
Manneke, gij zijt 'amen' vergeten op lijn 5!  (Antwerps)
Jansen, ge zijt 'amen' vergeten op lijn 5!    (West-Vlaams)
```

### Create a New Project

```bash
plats init myproject        # English
plats allehop mijnproject   # West-Vlaams: hier gaan we!
plats awel mijnproject      # Antwerps: kom, we beginnen
plats allei mijnproject     # Limburgs: vooruit dan
```

### Flemish Fortune (Easter Egg!)

```bash
plats fortune    # Random Flemish proverb
plats zegt       # West-Vlaams: "zen moeder zegt..."
plats watteda    # Antwerps: wat is da?
plats wiste      # Limburgs: wist ge dat?
```

Example output:
```
╔════════════════════════════════════════╗
║ Beter een vogel in de hand dan tien    ║
║ op 't dak, jong!                       ║
╚════════════════════════════════════════╝
```

---

## All Dialect Aliases

| Command | Standard | West-Vlaams | Antwerps | Limburgs | Brussels | Genks |
|---------|----------|-------------|----------|----------|----------|-------|
| run | `loop` | `voertuut` | `doet` | `gaon` | `doeda` | `jaowdoen` |
| repl | `repl` | `proboir` | `smos` | `efkes` | `praot` | `babbel` |
| examples | `examples` | `tuuntnekeer` | `toondada` | `loatskiejn` | `toontmansen` | `jaowkiek` |
| check | `check` | `zijdezekers` | `istdagoe` | `kloptda` | `isdagoe` | `istokin` |
| init | `init` | `allehop` | `awel` | `allei` | `maakaan` | `pakaan` |
| fortune | `fortune` | `zegt` | `watteda` | `wiste` | `spreuk` | `jaowzegt` |
| build | `bouw` | `moakt` | `bouwt` | `maakt` | `fabrikeert` | `bouwt` |
| help | `haalp` | `hulpe` | `helptemij` | `helpt` | `aidez` | `hulp` |

---

## Installation

### Option 0: npm / npx (Node.js users)

Requires **Python 3.10+** to be installed (because the compiler is implemented in Python).

Global install (adds `plats` and `vlaamscodex` to your PATH):

```bash
npm install -g vlaamscodex
plats version
```

Run without installing globally:

```bash
npx vlaamscodex --help
npx plats version
```

### Option 0b: Chocolatey (Windows)

Requires **Python 3.10+**.

This repo includes a Chocolatey package skeleton in `chocolatey/` (build/pack separately). See `chocolatey/README.md`.

### Option A: pip (Recommended)

```bash
pip install vlaamscodex
```

### Option B: pipx (Isolated)

```bash
pipx install vlaamscodex
```

### Option C: Development

```bash
git clone https://github.com/brentishere41848/Vlaamse-Codex.git
cd Vlaamse-Codex
pip install -e ".[dev]"
```

---

## Example Programs

### Hello World

```text
# coding: vlaamsplats
plan doe
  zet naam op tekst weeireld amen

  maak funksie groet met wie doe
    klap tekst gdag plakt spatie plakt tekst aan plakt spatie plakt da wie amen
  gedaan

  roep groet met da naam amen
gedaan
```

### Calculator

```text
# coding: vlaamsplats
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
```

### Run Built-in Examples

```bash
plats examples --list          # Show all examples
plats examples --show hello    # View the code
plats examples --run rekenen   # Run calculator example
```

---

## Magic Mode

Platskript files with the encoding header can run directly with Python:

```text
# coding: vlaamsplats
plan doe
  klap tekst hallo amen
gedaan
```

```bash
python script.plats  # Works after installing VlaamsCodex!
```

---

## Language Specification (v0.1)

### Program Structure

Programs are wrapped in `plan doe ... gedaan`. Statements terminate with `amen`.

### Statements

| Syntax | Description |
|--------|-------------|
| `zet <var> op <expr> amen` | Variable assignment |
| `klap <expr> amen` | Print expression |
| `maak funksie <name> met <params...> doe ... gedaan` | Function definition |
| `roep <name> met <args...> amen` | Function call |
| `geeftterug <expr> amen` | Return statement |

### Expressions

| Syntax | Description |
|--------|-------------|
| `tekst <words...>` | String literal |
| `getal <digits>` | Numeric literal |
| `da <name>` | Variable reference |
| `spatie` | Space character |
| `plakt` | String concatenation |

### Operators

| Platskript | Python | Description |
|------------|--------|-------------|
| `derbij` | `+` | Addition |
| `deraf` | `-` | Subtraction |
| `keer` | `*` | Multiplication |
| `gedeeld` | `/` | Division |
| `isgelijk` | `==` | Equals |
| `isniegelijk` | `!=` | Not equals |
| `isgroterdan` | `>` | Greater than |
| `iskleinerdan` | `<` | Less than |

---

## VS Code Extension

Install the VlaamsCodex extension for syntax highlighting:

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "VlaamsCodex"
4. Click Install

---

## Documentation

- [Overview](docs/01_overview.md)
- [How Python Runs It](docs/02_how_python_runs_it.md)
- [Packaging & Installation](docs/03_packaging_and_install.md)
- [Language Specification](docs/04_language_spec.md)
- [Security Notes](docs/05_security_and_safety.md)
- [User Guide](docs/06_user_guide.md)
- [CLI Documentation](docs/08_plats_documentation_en.md)

---

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

Bugs? Ideas? [Open an issue](https://github.com/brentishere41848/Vlaamse-Codex/issues)!

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ in Flanders**

*'t Es simpel, 't es plansen!*
