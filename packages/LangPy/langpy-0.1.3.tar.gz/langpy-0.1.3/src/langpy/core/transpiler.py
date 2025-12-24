import tokenize
from typing import List

from .tokenizer import tokenize_source
from .rebuilder import rebuild_source
from .lexicon.base import Lexicon


def transpile(source: str, lexicon: Lexicon) -> str:
    tokens = tokenize_source(source)
    new_tokens: List[tokenize.TokenInfo] = []

    prev_token: tokenize.TokenInfo | None = None

    for token in tokens:
        if token.type == tokenize.NAME:
            is_attribute = (
                prev_token is not None
                and prev_token.type == tokenize.OP
                and prev_token.string == "."
            )

            if not is_attribute:
                translated = lexicon.translate(token.string)

                if translated != token.string:
                    token = tokenize.TokenInfo(
                        token.type,
                        translated,
                        token.start,
                        token.end,
                        token.line,
                    )

        new_tokens.append(token)
        prev_token = token

    return rebuild_source(new_tokens)
