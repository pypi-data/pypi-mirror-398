import io
import tokenize
from typing import List


def tokenize_source(source: str) -> List[tokenize.TokenInfo]:
    reader = io.StringIO(source).readline
    return list(tokenize.generate_tokens(reader))
