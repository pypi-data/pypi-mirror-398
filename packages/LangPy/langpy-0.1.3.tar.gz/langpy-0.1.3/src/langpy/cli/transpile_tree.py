from pathlib import Path
import tokenize
from io import StringIO

from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon
from langpy.core.lexicon.pt import PortugueseLexicon
from langpy.core.lexicon.fr import FrenchLexicon


EXTENSION_TO_LEXICON = {
    ".pyes": SpanishLexicon,
    ".pypt": PortugueseLexicon,
    ".pyfr": FrenchLexicon,
}

SUPPORTED_EXTENSIONS = tuple(EXTENSION_TO_LEXICON.keys())


def transpile_tree(entry_path: Path, *, force: bool = False) -> list[Path]:
    if not entry_path.exists() or not entry_path.is_file():
        raise FileNotFoundError(entry_path)

    entry_path = entry_path.resolve()
    root_dir = entry_path.parent

    processed: set[Path] = set()
    pending: list[Path] = [entry_path]
    generated: list[Path] = []

    # mismo criterio que en ejecución: script dir primero
    search_paths = [root_dir]

    while pending:
        current = pending.pop()

        if current in processed:
            continue

        if not _is_within_root(current, root_dir):
            raise ImportError(f"Import outside root directory: {current}")

        source = current.read_text(encoding="utf-8")

        lexicon_cls = EXTENSION_TO_LEXICON[current.suffix]
        lexicon = lexicon_cls()
        python_source = transpile(source, lexicon)

        imports = _collect_imports(python_source)

        for fullname in imports:
            resolved = _resolve_module(fullname, search_paths)
            if resolved is None:
                continue

            if not _is_within_root(resolved, root_dir):
                raise ImportError(f"Import outside root directory: {resolved}")

            if resolved not in processed:
                pending.append(resolved)

        output_py = _transpile_file(current, force=force)
        generated.append(output_py)
        processed.add(current)

    return generated


def _collect_imports(source: str) -> set[str]:
    imports: set[str] = set()

    tokens = tokenize.generate_tokens(StringIO(source).readline)
    it = iter(tokens)

    for tok in it:
        # import a.b.c
        if tok.type == tokenize.NAME and tok.string == "import":
            parts: list[str] = []

            while True:
                t = next(it, None)
                if t is None:
                    break

                if t.type == tokenize.NAME:
                    parts.append(t.string)
                elif t.type == tokenize.OP and t.string == ".":
                    continue
                else:
                    break

            if parts:
                imports.add(".".join(parts))

        # from a.b.c import x
        elif tok.type == tokenize.NAME and tok.string == "from":
            parts: list[str] = []

            while True:
                t = next(it, None)
                if t is None:
                    break

                if t.type == tokenize.NAME:
                    parts.append(t.string)
                elif t.type == tokenize.OP and t.string == ".":
                    continue
                else:
                    break

            if parts:
                imports.add(".".join(parts))

    return imports


def _resolve_module(fullname: str, search_paths: list[Path]) -> Path | None:
    parts = fullname.split(".")

    for base in search_paths:
        base_path = Path(base)

        # intento jerárquico: a/b/c.<ext>
        candidate_base = base_path
        for part in parts[:-1]:
            candidate_base = candidate_base / part
            if not candidate_base.is_dir():
                break
        else:
            module_name = parts[-1]

            # módulo suelto
            for ext in SUPPORTED_EXTENSIONS:
                candidate = candidate_base / f"{module_name}{ext}"
                if candidate.is_file():
                    return candidate.resolve()

            # paquete
            package_dir = candidate_base / module_name
            if package_dir.is_dir():
                for ext in SUPPORTED_EXTENSIONS:
                    init_file = package_dir / f"__init__{ext}"
                    if init_file.is_file():
                        return init_file.resolve()

    return None


def _transpile_file(path: Path, *, force: bool) -> Path:
    if path.suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported extension: {path.suffix}")

    output = path.with_suffix(".py")

    if output.exists() and not force:
        raise FileExistsError(output)

    lexicon_cls = EXTENSION_TO_LEXICON[path.suffix]
    lexicon = lexicon_cls()

    source = path.read_text(encoding="utf-8")
    result = transpile(source, lexicon)

    output.write_text(result, encoding="utf-8")
    return output


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False
