"""Syntax checker for Platskript - MULTI-VLAAMS! 🇧🇪

Check uw code met elk dialect da ge wilt:
  plats check script.plats       (English)
  plats zijdezekers script.plats (West-Vlaams: zijt ge zeker?)
  plats istdagoe script.plats    (Antwerps: is da goe?)
  plats kloptda script.plats     (Limburgs: klopt dat?)
  plats zalkdagaan script.plats  (Oost-Vlaams)
  plats passedat script.plats    (Brussels)
"""

from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass

# Checker command aliases (Multi-Vlaams!)
CHECKER_ALIASES = {
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
}


@dataclass
class SyntaxIssue:
    """Represents a syntax issue found during checking."""

    line_number: int
    line_content: str
    issue_type: str
    message: str
    suggestion: str | None = None


# Error messages in different dialects
ERROR_MESSAGES = {
    "missing_amen": {
        "default": "Missing 'amen' at end of statement",
        "west-vlaams": "Vergeten 'amen' te zetten, jong!",
        "antwerps": "Manneke, gij zijt 'amen' vergeten!",
        "limburgs": "Efkes nog 'amen' derbij zetten, hè?",
        "oost-vlaams": "Allez, 'amen' vergeten!",
        "brussels": "Eh, 'amen' oublié, sjongen!",
        "genks": "Jaow, 'amen' vergeten!",
    },
    "missing_gedaan": {
        "default": "Missing 'gedaan' to close block",
        "west-vlaams": "Ge moe 'gedaan' zetten, 't blok es nie toe!",
        "antwerps": "'Gedaan' vergeten, manneke! Den blok is open!",
        "limburgs": "Efkes 'gedaan' derbij, den blok is nog open!",
        "oost-vlaams": "Komaan, 'gedaan' vergeten!",
        "brussels": "'Gedaan' vergeten, den blok est open!",
        "genks": "Jaow, 'gedaan' mist!",
    },
    "missing_plan_doe": {
        "default": "Missing 'plan doe' - programs should start with 'plan doe'",
        "west-vlaams": "Begint altijd met 'plan doe', jansen!",
        "antwerps": "Manneke, begin met 'plan doe'!",
        "limburgs": "Allei, 'plan doe' is verplicht aan 't begin!",
        "oost-vlaams": "Zegt, ge moe beginnen met 'plan doe'!",
        "brussels": "Eh, 'plan doe' au début, c'est obligé!",
        "genks": "Jaow, 'plan doe' moet eerst!",
    },
    "unbalanced_blocks": {
        "default": "Unbalanced 'plan doe' and 'gedaan' blocks",
        "west-vlaams": "'plan doe' en 'gedaan' kloppen nie, dat es scheef!",
        "antwerps": "Uwe blokken zijn ambetant, manneke!",
        "limburgs": "Efkes checken: blokken zijn nie in orde!",
        "oost-vlaams": "Allez, uwe blokken zijn scheef!",
        "brussels": "Les blocs sont pas équilibrés, eh!",
        "genks": "Jaow, blokken kloppen nie!",
    },
    "invalid_statement": {
        "default": "Statement doesn't appear to be valid Platskript",
        "west-vlaams": "Da snapt ik nie, da's gin Platskript!",
        "antwerps": "Amai, da's geen goei Platskript!",
        "limburgs": "Allei, da is nie hoe 't moet!",
        "oost-vlaams": "Zegt, da's ambetant!",
        "brussels": "Sjongen, ça marche pas ça!",
        "genks": "Jaow, da klopt nie!",
    },
    "empty_program": {
        "default": "Empty program - nothing to check!",
        "west-vlaams": "Der staat niks, jansen!",
        "antwerps": "Manneke, 't is leeg!",
        "limburgs": "'t Is leeg, efkes iets schrijven!",
        "oost-vlaams": "Allez, der is niks!",
        "brussels": "C'est vide, sjongen!",
        "genks": "Jaow, niks te checken!",
    },
}

# Success messages in different dialects
SUCCESS_MESSAGES = {
    "default": "All good! No issues found.",
    "west-vlaams": "'t Es goe, gie! Gin problemen!",
    "antwerps": "Sjiek! Alles in orde, manneke!",
    "limburgs": "Allei, alles klopt! Sjiek gedaan!",
    "oost-vlaams": "Zegt, da's proper! Geen fouten!",
    "brussels": "C'est bon! Pas de problèmes!",
    "genks": "Jaow! Alles goe!",
}

# Known Platskript keywords
KEYWORDS = {
    "plan", "doe", "gedaan", "zet", "op", "amen",
    "klap", "maak", "funksie", "met", "roep",
    "geeftterug", "tekst", "getal", "da", "spatie",
    "plakt", "derbij", "deraf", "keer", "gedeeld",
    "als", "anders", "zolang", "waar", "onwaar",
    "is", "nie", "en", "of", "groter", "kleiner",
}


def get_error_message(error_type: str, dialect: str = "default") -> str:
    """Get an error message in the specified dialect."""
    messages = ERROR_MESSAGES.get(error_type, {})
    return messages.get(dialect, messages.get("default", f"Unknown error: {error_type}"))


def get_success_message(dialect: str = "default") -> str:
    """Get a success message in the specified dialect."""
    return SUCCESS_MESSAGES.get(dialect, SUCCESS_MESSAGES["default"])


def check_syntax(source: str, dialect: str = "default") -> list[SyntaxIssue]:
    """Check Platskript source code for common issues.

    Args:
        source: The Platskript source code to check.
        dialect: Dialect for error messages.

    Returns:
        List of SyntaxIssue objects describing problems found.
    """
    issues: list[SyntaxIssue] = []
    lines = source.splitlines()

    # Skip empty programs
    if not source.strip():
        issues.append(SyntaxIssue(
            line_number=1,
            line_content="",
            issue_type="empty_program",
            message=get_error_message("empty_program", dialect),
        ))
        return issues

    # Check for plan doe ... gedaan structure
    has_plan_doe = "plan doe" in source
    if not has_plan_doe:
        # Find first non-comment, non-empty line
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                issues.append(SyntaxIssue(
                    line_number=i,
                    line_content=line,
                    issue_type="missing_plan_doe",
                    message=get_error_message("missing_plan_doe", dialect),
                    suggestion="plan doe",
                ))
                break

    # Count block openers and closers
    plan_doe_count = source.count("plan doe") + source.count("maak funksie")
    gedaan_count = source.count("gedaan")
    if plan_doe_count != gedaan_count:
        issues.append(SyntaxIssue(
            line_number=len(lines),
            line_content="",
            issue_type="unbalanced_blocks",
            message=get_error_message("unbalanced_blocks", dialect),
            suggestion=f"'plan doe'/'maak funksie': {plan_doe_count}, 'gedaan': {gedaan_count}",
        ))

    # Check each line for common issues
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Skip block structure lines
        if stripped in ("plan doe", "gedaan", "anders"):
            continue

        # Check for statements that should end with 'amen'
        amen_statements = [
            r"^zet\s+\w+\s+op\s+",       # zet X op Y amen
            r"^klap\s+",                  # klap X amen
            r"^roep\s+",                  # roep X amen
            r"^geeftterug\s+",            # geeftterug X amen
        ]

        for pattern in amen_statements:
            if re.match(pattern, stripped) and not stripped.endswith("amen"):
                issues.append(SyntaxIssue(
                    line_number=i,
                    line_content=line,
                    issue_type="missing_amen",
                    message=get_error_message("missing_amen", dialect),
                    suggestion=f"{stripped} amen",
                ))
                break

        # Check for 'maak funksie' without 'doe'
        if stripped.startswith("maak funksie") and "doe" not in stripped:
            issues.append(SyntaxIssue(
                line_number=i,
                line_content=line,
                issue_type="invalid_statement",
                message=get_error_message("invalid_statement", dialect),
                suggestion="maak funksie <naam> met <params> doe",
            ))

    return issues


def format_issues(issues: list[SyntaxIssue], path: str | None = None) -> str:
    """Format syntax issues for display."""
    if not issues:
        return ""

    lines = []
    if path:
        lines.append(f"\n📝 Checking: {path}\n")

    lines.append("=" * 60)

    for issue in issues:
        lines.append(f"\n❌ Line {issue.line_number}: {issue.message}")
        if issue.line_content:
            lines.append(f"   → {issue.line_content.strip()}")
        if issue.suggestion:
            lines.append(f"   💡 Suggestie: {issue.suggestion}")

    lines.append("\n" + "=" * 60)
    lines.append(f"Found {len(issues)} issue(s)")

    return "\n".join(lines)


def check_file(path: Path, dialect: str = "default") -> tuple[bool, str]:
    """Check a Platskript file for syntax issues.

    Args:
        path: Path to the .plats file.
        dialect: Dialect for error messages.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, f"File not found: {path}"
    except Exception as e:
        return False, f"Error reading file: {e}"

    # Strip coding header if present
    lines = source.splitlines()
    if lines and "coding" in lines[0]:
        source = "\n".join(lines[1:])

    issues = check_syntax(source, dialect)

    if not issues:
        success_msg = get_success_message(dialect)
        return True, f"\n✅ {path}: {success_msg}\n"

    return False, format_issues(issues, str(path))


def detect_checker_dialect(command: str) -> str:
    """Detect dialect from checker command alias."""
    if command in ("zijdezekers", "zekers", "okeej"):
        return "west-vlaams"
    elif command in ("istdagoe", "isdatgoe", "goeddansen"):
        return "antwerps"
    elif command in ("kloptda", "kloptdat", "goedzowie"):
        return "limburgs"
    elif command in ("zalkdagaan", "checktem"):
        return "oost-vlaams"
    elif command in ("passedat", "camarche"):
        return "brussels"
    elif command in ("jaowklopt", "probeircheck"):
        return "genks"
    return "default"


def print_checker_help() -> int:
    """Print help for check command."""
    print("""
🇧🇪 Platskript Syntax Checker - MULTI-VLAAMS!

USAGE:
  plats check <file.plats>

MULTI-VLAAMS ALIASSEN:
  West-Vlaams   : plats zijdezekers <bestand>
  Antwerps      : plats istdagoe <bestand>
  Limburgs      : plats kloptda <bestand>
  Oost-Vlaams   : plats zalkdagaan <bestand>
  Brussels      : plats passedat <bestand>
  Genks         : plats jaowklopt <bestand>

EXAMPLES:
  plats check hello.plats
  plats zijdezekers hallo.plats
  plats istdagoe script.plats

CHECKS FOR:
  - Missing 'plan doe' at start
  - Missing 'gedaan' closures
  - Missing 'amen' at statement ends
  - Unbalanced block structure
  - Invalid statement patterns

Error messages are shown in your dialect!

't Es simpel, 't es plansen!
""")
    return 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        success, message = check_file(path)
        print(message)
        exit(0 if success else 1)
    else:
        print_checker_help()
