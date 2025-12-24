from .base import Lexicon


class PortugueseLexicon(Lexicon):
    language = "pt"

    table = {
        # controle de fluxo
        "se": "if",
        "senao": "else",
        "senao_se": "elif",
        "enquanto": "while",
        "para": "for",
        "quebrar": "break",
        "continuar": "continue",
        "retornar": "return",
        "passar": "pass",

        # booleanos
        "verdadeiro": "True",
        "falso": "False",
        "nenhum": "None",

        # operadores
        "e": "and",
        "ou": "or",
        "nao": "not",

        # estrutura
        "definir": "def",
        "classe": "class",
        "com": "with",
        "como": "as",
        "tentar": "try",
        "exceto": "except",
        "finalmente": "finally",
        "lancar": "raise",

        # imports
        "importar": "import",
        "de": "from",

        # built-ins mínimos
        "imprimir": "print",
        "comprimento": "len",
        "tipo": "type",
        "intervalo": "range",
    }
