from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
from .imports import ImportEvent

SUPPORTED_EXTENSIONS = (".pyes", ".pyfr", ".pypt")


def resolve_import_event(
    event: ImportEvent,
    *,
    current_file: Path,
    root_dir: Path,
    search_paths: List[Path],
) -> Iterable[Path]:

    results: list[Path] = []

    # base path según nivel relativo
    if event.level > 0:
        base = current_file.parent
        for _ in range(event.level - 1):
            base = base.parent
        candidates = [base]
    else:
        candidates = search_paths

    modules: list[str] = []

    if event.is_from:
        if event.module:
            modules.append(event.module)
    else:
        modules.extend(event.names)

    for module in modules:
        parts = module.split(".")

        for base in candidates:
            pkg_path = base.joinpath(*parts)

            # archivo directo
            for ext in SUPPORTED_EXTENSIONS:
                file_candidate = pkg_path.with_suffix(ext)
                if file_candidate.exists():
                    results.append(file_candidate.resolve())

            # paquete (__init__)
            for ext in SUPPORTED_EXTENSIONS:
                init_candidate = pkg_path / f"__init__{ext}"
                if init_candidate.exists():
                    results.append(init_candidate.resolve())

    return results
