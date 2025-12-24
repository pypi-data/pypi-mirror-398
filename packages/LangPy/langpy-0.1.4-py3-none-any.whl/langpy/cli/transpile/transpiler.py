from __future__ import annotations

from pathlib import Path

from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon
from langpy.core.lexicon.pt import PortugueseLexicon
from langpy.core.lexicon.fr import FrenchLexicon

SUPPORTED_EXTENSIONS = (".pyes", ".pyfr", ".pypt")

EXTENSION_TO_LEXICON = {
    ".pyes": SpanishLexicon,
    ".pypt": PortugueseLexicon,
    ".pyfr": FrenchLexicon,
}


def _transpile_file(path: Path, *, force: bool = False) -> Path:
    if path.suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported source file: {path}")

    output = path.with_suffix(".py")

    if output.exists() and not force:
        return output

    source = path.read_text(encoding="utf-8")

    lexicon_cls = EXTENSION_TO_LEXICON[path.suffix]
    lexicon = lexicon_cls()

    python_code = transpile(source, lexicon)

    output.write_text(python_code, encoding="utf-8")
    return output


def _transpile_to_memory(path: Path) -> str:
    if path.suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported source file: {path}")

    source = path.read_text(encoding="utf-8")

    lexicon_cls = EXTENSION_TO_LEXICON[path.suffix]
    lexicon = lexicon_cls()

    return transpile(source, lexicon)
