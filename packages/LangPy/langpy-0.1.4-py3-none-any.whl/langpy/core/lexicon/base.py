from typing import Dict


class Lexicon:
    language: str
    table: Dict[str, str]

    def translate(self, name: str) -> str:
        return self.table.get(name, name)
