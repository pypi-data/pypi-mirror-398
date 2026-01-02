"""Custom source encoding codec for `# coding: vlaamsplats`.

If this codec is registered early enough (via a .pth startup hook),
then a `.plats` file can be executed as:

    python myscript.plats

because Python will use this codec to decode the file and will receive
valid Python source back.

See docs/02_how_python_runs_it.md for the full explanation.
"""

from __future__ import annotations

import codecs
import io
from typing import Optional


def _compile_plats_bytes(b: bytes, errors: str) -> tuple[str, int]:
    from .compiler import compile_plats

    utf8 = codecs.lookup("utf-8")

    # Decode original bytes as UTF-8 text (Plats source).
    text, _ = utf8.decode(b, errors)

    # Remove first-line coding cookie so the Plats compiler doesn't see it.
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("#") and "coding" in lines[0]:
        lines = lines[1:]
    plats_src = "\n".join(lines)

    # Compile to Python source text.
    py_src = "# coding: utf-8\n" + compile_plats(plats_src)
    return py_src, len(b)


def _search(encoding_name: str) -> Optional[codecs.CodecInfo]:
    name = encoding_name.replace("-", "_").lower()
    if name not in {"vlaamsplats", "plats"}:
        return None

    utf8 = codecs.lookup("utf-8")

    class Codec(codecs.Codec):
        def encode(self, s: str, errors: str = "strict"):
            return utf8.encode(s, errors)

        def decode(self, b: bytes, errors: str = "strict"):
            if not b:
                return "", 0
            return _compile_plats_bytes(b, errors)

    class IncrementalDecoder(codecs.IncrementalDecoder):
        def __init__(self, errors: str = "strict"):
            super().__init__(errors)
            self._buffer = bytearray()
            self._done = False

        def decode(self, input: bytes, final: bool = False) -> str:  # type: ignore[override]
            if input:
                self._buffer.extend(input)
            if not final:
                return ""
            if self._done or not self._buffer:
                return ""
            out, _ = _compile_plats_bytes(bytes(self._buffer), self.errors)
            self._buffer.clear()
            self._done = True
            return out

        def reset(self) -> None:  # noqa: D401 - match codecs API
            self._buffer.clear()
            self._done = False

    class StreamReader(codecs.StreamReader):
        def __init__(self, stream, errors: str = "strict"):
            super().__init__(stream, errors)
            self._compiled: io.StringIO | None = None

        def _ensure_compiled(self) -> io.StringIO:
            if self._compiled is None:
                raw = self.stream.read()
                py_src, _ = _compile_plats_bytes(raw, self.errors)
                self._compiled = io.StringIO(py_src)
            return self._compiled

        def read(self, size: int = -1, chars: int = -1, firstline: bool = False):  # type: ignore[override]
            sio = self._ensure_compiled()
            if size is None or size < 0:
                return sio.read()
            return sio.read(size)

        def readline(self, size: int | None = None, keepends: bool = True):  # type: ignore[override]
            sio = self._ensure_compiled()
            line = sio.readline(-1 if size is None else size)
            if not keepends and line:
                line = line.splitlines(keepends=False)[0]
            return line

    class StreamWriter(Codec, codecs.StreamWriter):
        pass

    return codecs.CodecInfo(
        name=encoding_name,
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )


def register() -> None:
    """Register the codec search function."""
    codecs.register(_search)
