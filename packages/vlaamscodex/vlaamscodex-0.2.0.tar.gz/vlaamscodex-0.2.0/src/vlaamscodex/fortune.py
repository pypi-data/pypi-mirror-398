"""Flemish Proverbs and Easter Eggs - MULTI-VLAAMS! 🇧🇪

Commands:
  plats fortune     (English)
  plats zegt        (West-Vlaams: "zen moeder zegt...")
  plats watteda     (Antwerps: "wat is da?")
  plats wiste       (Limburgs: "wist ge dat?")
  plats zansen      (Brussels)
  plats spreuk      (Oost-Vlaams)
"""

from __future__ import annotations

import random

# Fortune command aliases (Multi-Vlaams!)
FORTUNE_ALIASES = {
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
}

# =============================================================================
# VLAAMSE SPREUKEN EN GEZEGDEN 🇧🇪
# =============================================================================

WEST_VLAAMSE_SPREUKEN = [
    "'t Es simpel, 't es plansen, 't es Vlaams!",
    "Beter een vogel in de hand dan tien op 't dak, jong!",
    "Ge kunt nie van twee walletjes eten, jansen!",
    "Wuk a nie in uwe kop eit, moe je in uw bienen ebn!",
    "Lik mijn klansen, 'k een gin tied!",
    "Oejeansen, da's e stuutje!",
    "Mee 't hoapen es 't al gedoan!",
    "'t Es nie omda ge peist da 't zo es, da 't zo es!",
    "Elk zen goesting, zei de boer, en hij kuste zen koe.",
    "Ge moe nie zagen, ge moe kapn!",
    "Van een slechte programmeur moekter gin goeie verwachtn!",
    "'n Goe begin es 't halve werk gedoan!",
    "Wie eten wil moe werken, tenzij da ge Python schrijft!",
    "'t Es beter slansen dan jansenst!",
    "Moar dat es lik een ander paar mouwen!",
]

ANTWERPSE_SPREUKEN = [
    "Amai zansen, da's nen dikken!",
    "Ge moet uwe plan trekken, manneke!",
    "Ik zen content, jong!",
    "Da's gansen nie kosjeer, zansen!",
    "In den beginne was er de bug, en de bug was ambetant!",
    "Wie nie compileerd, die nie programmeert!",
    "Schansen, ketansen, zen ge klansen?",
    "Van smansen komt mansansen!",
    "Den Antweransen, die kan programmansen!",
    "Manneke, 't is te dansen vansen ansen!",
    "Zansen ge da? Zansen ge da echt?",
    "Nen bug fixen is lijk nen balansen!",
    "'t Stad is kansen, de code is gransen!",
    "Ge moet nie panikansen, manneke!",
    "Da's pas nen smansen code!",
]

LIMBURGSE_SPREUKEN = [
    "Allei, da geit waal good komme!",
    "Zjwansen, 't is efkes e probleempke!",
    "Rustig, rustig, 't loost zich waal!",
    "Effe geduld, sjansen!",
    "Ge moot efkansen waachte!",
    "Da's sjiek, da's sjiek!",
    "Wiste da Python oet Limburg komt? Nee? Ik ouch nie!",
    "Allei dan, we gansen door!",
    "Efkes rusten, dan opnieuw probansen!",
    "Ge zijt nen echte Limburgansen programmeur!",
    "'t Is good, 't is good, nie zansen!",
    "Da loost zich allemaal wel!",
    "Efkes een bug, maar 't komt good!",
    "Sjiek code schrijven, da's de kunst!",
    "Rustig aon, den bug loopt nie wech!",
]

BRUSSELSE_SPREUKEN = [
    "Allez, stoansen, we zijn er bijna!",
    "Une fois, deux fois, de code marche!",
    "Dikansen, 't is kapot!",
    "Eh bien, we fixen dat!",
    "Sjongen, wat een zeveransen!",
    "Astembulansen, da werkt!",
    "C'est nen gansen, die code!",
    "Moitie moitie, de bug is weg!",
    "Awel, da's pas programmansen!",
    "Zansen en dansen, da's Brusselse stijl!",
    "Une fois gecompileerd, toujours gecompileerd!",
    "Eh manneke, fais pas le zansen!",
    "Zwansen en programmansen, c'est la vie!",
    "Astembull, den code is gereed!",
    "Dikke merci voor den bug report!",
]

OOST_VLAAMSE_SPREUKEN = [
    "Allez, da's rap gedaan!",
    "Nen directe, geen omwegen!",
    "Komaan, we pakken dat aan!",
    "Zegt, da's proper code!",
    "Rap rap, de bug is weg!",
    "Allez, niet zeuren, coden!",
    "Da's directe code, geen poespas!",
    "Komaan dan, compilansen!",
    "Zegt, ge zijt een goeie!",
    "Rap gedaan, goed gedaan!",
    "Allez, nog eentje en we zijn er!",
    "Geen gezanik, gewoon doen!",
    "Da's efficient, da's Oost-Vlaams!",
    "Komaan, we pakken die bug!",
    "Allez, rap rap, coden!",
]

GENKS_SPREUKEN = [
    "Jaow, da werkt!",
    "Allei, maakt, 't is goei!",
    "Cité-code, beste code!",
    "Jaow jaow, we gansen door!",
    "Probeirme, 't lukt wel!",
    "Da's Genks, da's goei!",
    "Allei manneke, codens!",
    "Jaow, den bug is weg!",
    "Genks programmansen is beste programmansen!",
    "Jaow, da compileerd!",
    "Allei, nie zansen, doen!",
    "Maakt, maakt, 't komt goei!",
    "Jaow, we fixens dat!",
    "Genks code, sterke code!",
    "Allei, nog efkes en klaar!",
]

# Programmer humor in Flemish
PROGRAMMER_HUMOR = [
    "Waarom compileert de code niet? Omdat ge 'amen' vergeten zijt, jansen!",
    "99 bugs op den stack... fix er een... 127 bugs op den stack!",
    "In Python is alles ne object, behalve mijn code die is ne bug!",
    "'plan doe' zei ik, 'gedaan' zeg ik nu... maar tussendoor: 47 bugs!",
    "Hoe noemt ge ne programmeur uit Antwerpen? Een smosser!",
    "Hoe noemt ge ne programmeur uit West-Vlaanderen? Een planser!",
    "Mijn code werkt... 't is een wonder!",
    "Commentaar schrijven? Da's voor mensen die hun code nie snappen!",
    "Waarom testen? De gebruiker vindt de bugs toch wel!",
    "Copy paste is herbruik... toch?",
    "'t Werkt op mijn machine! - beroemde laatste woorden",
    "Kansen compileert nie? Probeer 't uit en aan te zetten!",
    "De beste code is geen code - dan zijn er geen bugs!",
    "Platskript: waar 'amen' niet alleen voor in de kerk is!",
    "Git commit -m 'het werkt nu echt' - narrator: het werkte niet",
]

# Seasonal/special fortunes
SPECIAL_FORTUNES = [
    "🍺 Het is ergens vijven! Tijd voor een Jupiler!",
    "🍟 Ne frietje met stoofvleessaus, da's het echte programmeurs eten!",
    "🇧🇪 België: klein land, grote code!",
    "⚽ Code is als voetbal: ge mist 100% van de bugs die ge nie zoekt!",
    "🎭 Het leven is een theater, en uw code is de comediant!",
]

ALL_FORTUNES = (
    WEST_VLAAMSE_SPREUKEN
    + ANTWERPSE_SPREUKEN
    + LIMBURGSE_SPREUKEN
    + BRUSSELSE_SPREUKEN
    + OOST_VLAAMSE_SPREUKEN
    + GENKS_SPREUKEN
    + PROGRAMMER_HUMOR
    + SPECIAL_FORTUNES
)


def get_fortune(dialect: str | None = None) -> str:
    """Get a random Flemish fortune.

    Args:
        dialect: Optional dialect to filter by (west-vlaams, antwerps, limburgs, etc.)

    Returns:
        A random fortune string.
    """
    if dialect == "west-vlaams":
        pool = WEST_VLAAMSE_SPREUKEN + PROGRAMMER_HUMOR[:5]
    elif dialect == "antwerps":
        pool = ANTWERPSE_SPREUKEN + PROGRAMMER_HUMOR[:5]
    elif dialect == "limburgs":
        pool = LIMBURGSE_SPREUKEN + PROGRAMMER_HUMOR[:5]
    elif dialect == "brussels":
        pool = BRUSSELSE_SPREUKEN + PROGRAMMER_HUMOR[:5]
    elif dialect == "oost-vlaams":
        pool = OOST_VLAAMSE_SPREUKEN + PROGRAMMER_HUMOR[:5]
    elif dialect == "genks":
        pool = GENKS_SPREUKEN + PROGRAMMER_HUMOR[:5]
    else:
        pool = ALL_FORTUNES

    return random.choice(pool)


def print_fortune(dialect: str | None = None) -> int:
    """Print a random Flemish fortune."""
    fortune = get_fortune(dialect)

    # Add some flair
    print()
    print("  " + "═" * (len(fortune) + 4))
    print(f"  ║ {fortune} ║")
    print("  " + "═" * (len(fortune) + 4))
    print()
    print("        - Vlaamse wijsheid 🇧🇪")
    print()

    return 0


def detect_fortune_dialect(command: str) -> str | None:
    """Detect dialect from fortune command alias."""
    if command in ("zegt", "zenmoederzegt", "spreuke"):
        return "west-vlaams"
    elif command in ("watteda", "manneke"):
        return "antwerps"
    elif command in ("wiste", "wistedak"):
        return "limburgs"
    elif command in ("zansen", "eikes"):
        return "brussels"
    elif command in ("spreuk", "gezegd"):
        return "oost-vlaams"
    elif command == "jaow":
        return "genks"
    return None


if __name__ == "__main__":
    print_fortune()
