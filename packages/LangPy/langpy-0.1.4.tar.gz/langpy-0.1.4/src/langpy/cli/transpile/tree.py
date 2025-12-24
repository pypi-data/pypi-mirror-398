from __future__ import annotations

from pathlib import Path
from typing import List, Set

from .imports import parse_imports
from .resolver import resolve_import_event
from .transpiler import _transpile_file


def _ensure_within_root(path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError:
        raise RuntimeError(f"Import escapes root directory: {path}")


def transpile_tree(
    entry_path: Path,
    *,
    force: bool = False,
) -> List[Path]:

    if not entry_path.exists() or not entry_path.is_file():
        raise FileNotFoundError(entry_path)

    entry_path = entry_path.resolve()
    root_dir = entry_path.parent

    search_paths = [root_dir]

    pending: list[Path] = [entry_path]
    processed: set[Path] = set()
    generated: list[Path] = []

    while pending:
        current = pending.pop()

        if current in processed:
            continue

        _ensure_within_root(current, root_dir)

        # 1. transpilar archivo actual
        output_py = _transpile_file(current, force=force)
        generated.append(output_py)

        # 2. parsear imports del .py generado
        python_source = output_py.read_text(encoding="utf-8")
        events = parse_imports(python_source)

        # 3. resolver imports
        for event in events:
            resolved = resolve_import_event(
                event,
                current_file=current,
                root_dir=root_dir,
                search_paths=search_paths,
            )

            for path in resolved:
                if path not in processed:
                    pending.append(path)

        processed.add(current)

    return generated
