from .base import Lexicon


class FrenchLexicon(Lexicon):
    language = "fr"

    table = {
        # contrôle de flux
        "si": "if",
        "sinon": "else",
        "sinon_si": "elif",
        "tant_que": "while",
        "pour": "for",
        "rompre": "break",
        "continuer": "continue",
        "retourner": "return",
        "passer": "pass",

        # booléens
        "vrai": "True",
        "faux": "False",
        "aucun": "None",

        # opérateurs
        "et": "and",
        "ou": "or",
        "non": "not",

        # structure
        "definir": "def",
        "classe": "class",
        "avec": "with",
        "comme": "as",
        "essayer": "try",
        "excepté": "except",
        "finalement": "finally",
        "lancer": "raise",

        # imports
        "importer": "import",
        "depuis": "from",

        # built-ins mínimos
        "imprimer": "print",
        "longueur": "len",
        "type": "type",
        "intervalle": "range",
    }
