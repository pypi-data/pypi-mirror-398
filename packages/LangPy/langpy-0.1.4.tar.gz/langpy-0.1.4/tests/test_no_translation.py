from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon


def test_strings_not_translated():
    source = 'imprimir("si sino verdadero")'
    expected = 'print("si sino verdadero")'

    result = transpile(source, SpanishLexicon())

    assert result == expected
