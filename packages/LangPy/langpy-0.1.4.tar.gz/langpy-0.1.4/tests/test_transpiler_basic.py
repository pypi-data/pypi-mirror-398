from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon


def test_basic_translation():
    source = "si verdadero:\n    imprimir('ok')"
    expected = "if True:\n    print('ok')"

    result = transpile(source, SpanishLexicon())

    assert result == expected
