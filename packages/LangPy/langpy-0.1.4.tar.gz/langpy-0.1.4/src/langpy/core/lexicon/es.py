from .base import Lexicon


class SpanishLexicon(Lexicon):
    language = "es"

    table = {
        # control de flujo
        "si": "if",
        "sino": "else",
        "sino_si": "elif",
        "mientras": "while",
        "para": "for",
        "romper": "break",
        "continuar": "continue",
        "retornar": "return",
        "pasar": "pass",

        # booleanos
        "verdadero": "True",
        "falso": "False",
        "ninguno": "None",

        # operadores
        "y": "and",
        "o": "or",
        "no": "not",

        # estructura
        "definir": "def",
        "clase": "class",
        "con": "with",
        "como": "as",
        "intentar": "try",
        "excepto": "except",
        "finalmente": "finally",
        "lanzar": "raise",

        # imports
        "importar": "import",
        "desde": "from",

        # built-ins mínimos
        "imprimir": "print",
        "longitud": "len",
        "tipo": "type",
        "rango": "range",
    }
