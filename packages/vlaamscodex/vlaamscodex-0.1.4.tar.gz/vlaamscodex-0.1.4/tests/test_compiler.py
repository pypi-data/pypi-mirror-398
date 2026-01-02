from __future__ import annotations

from vlaamscodex.compiler import compile_plats


def test_compile_plats_hello_shape() -> None:
    plats = """
plan doe
  zet naam op tekst weeireld amen

  maak funksie groet met wie doe
    klap tekst gdag plakt spatie plakt tekst aan plakt spatie plakt da wie amen
  gedaan

  roep groet met da naam amen
gedaan
""".strip()

    py = compile_plats(plats)
    assert "naam = 'weeireld'" in py
    assert "def groet(wie):" in py
    assert "print(" in py
    assert "groet(naam)" in py

