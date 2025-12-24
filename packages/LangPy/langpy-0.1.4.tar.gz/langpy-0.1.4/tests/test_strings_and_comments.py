from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon


def test_import_translation():
    source = "importar sys"
    expected = "import sys"

    result = transpile(source, SpanishLexicon())

    assert result == expected
