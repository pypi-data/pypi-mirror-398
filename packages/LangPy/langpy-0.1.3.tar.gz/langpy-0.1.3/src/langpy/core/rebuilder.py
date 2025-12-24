import tokenize
from typing import List


def rebuild_source(tokens: List[tokenize.TokenInfo]) -> str:
    return tokenize.untokenize(tokens)
