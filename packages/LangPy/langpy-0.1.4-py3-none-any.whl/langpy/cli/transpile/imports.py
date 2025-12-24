from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import ast


@dataclass(frozen=True)
class ImportEvent:
    module: Optional[str]
    names: List[str]
    level: int
    is_from: bool


def parse_imports(source: str) -> List[ImportEvent]:
    tree = ast.parse(source)
    events: list[ImportEvent] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            events.append(
                ImportEvent(
                    module=None,
                    names=[alias.name for alias in node.names],
                    level=0,
                    is_from=False,
                )
            )

        elif isinstance(node, ast.ImportFrom):
            events.append(
                ImportEvent(
                    module=node.module,
                    names=[alias.name for alias in node.names],
                    level=node.level or 0,
                    is_from=True,
                )
            )

    return events
