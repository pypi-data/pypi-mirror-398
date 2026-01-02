"""VlaamsCodex (Platskript) — toy reference implementation.

This package exists to demonstrate the mechanism described in /docs:
- Platskript (.plats) is translated into Python.
- A custom Python source encoding (`vlaamsplats`) can decode Plats source into Python source
  so `python script.plats` works (with a startup hook that registers the codec).

This is intentionally small and not production-ready.
"""

__all__ = ["__version__"]
__version__ = "0.1.7"
