import sys
from pathlib import Path
from importlib.metadata import version

from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon
from langpy.core.lexicon.pt import PortugueseLexicon
from langpy.core.lexicon.fr import FrenchLexicon
from langpy.cli.transpile_tree import transpile_tree


EXTENSION_TO_LEXICON = {
    ".pyes": SpanishLexicon,
    ".pypt": PortugueseLexicon,
    ".pyfr": FrenchLexicon,
}


def print_info() -> None:
    print(
        "LangPy — Lexical layer for Python\n\n"
        "Write Python using human-language keywords.\n\n"
        "Supported languages:\n"
        "  .pyes  Spanish\n"
        "  .pypt  Portuguese\n"
        "  .pyfr  French\n\n"
        "Run `langpy --help` for usage."
    )


def print_help() -> None:
    print(
        "Usage:\n"
        "  langpy <file>\n"
        "  langpy --transpile <file>\n"
        "  langpy --output <out.py> <file>\n\n"
        "Options:\n"
        "  --help        Show this help message and exit\n"
        "  --version     Print package version and exit\n"
        "  --transpile   Transpile source and local LangPy imports to .py\n"
        "  --output      Transpile only input file to given output path\n"
        "  --force       Overwrite existing .py files (only with --transpile)\n\n"
        "Examples:\n"
        "  langpy main.pyes\n"
        "  langpy --transpile main.pyes\n"
        "  langpy --output build/main.py main.pyes"
    )


def main() -> None:
    args = sys.argv[1:]

    # ---- no args ----
    if not args:
        print_info()
        sys.exit(0)

    # ---- informational flags ----
    if "--help" in args:
        print_help()
        sys.exit(0)

    if "--version" in args:
        print(version("langpy"))
        sys.exit(0)

    transpile_only = "--transpile" in args
    force = "--force" in args
    output_flag = "--output" in args

    if force and not transpile_only:
        print("Error: --force can only be used with --transpile")
        sys.exit(1)

    if output_flag and transpile_only:
        print("Error: --output cannot be used with --transpile")
        sys.exit(1)

    # ---- --output mode ----
    if output_flag:
        idx = args.index("--output")

        try:
            out_path = Path(args[idx + 1])
            in_path = Path(args[idx + 2])
        except IndexError:
            print("Error: --output requires <output> and <input> paths")
            sys.exit(1)

        if not in_path.exists() or not in_path.is_file():
            print(f"Error: file not found: {in_path}")
            sys.exit(1)

        if in_path.suffix not in EXTENSION_TO_LEXICON:
            print(f"Error: unsupported file extension: {in_path.suffix}")
            sys.exit(1)

        lexicon = EXTENSION_TO_LEXICON[in_path.suffix]()
        source = in_path.read_text(encoding="utf-8")
        result = transpile(source, lexicon)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")

        print(out_path.resolve())
        sys.exit(0)

    # ---- remaining args should be the file ----
    files = [a for a in args if not a.startswith("--")]

    if len(files) != 1:
        print("Error: exactly one input file is required")
        sys.exit(1)

    path = Path(files[0])

    if not path.exists() or not path.is_file():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    # ---- transpile mode ----
    if transpile_only:
        try:
            generated = transpile_tree(path, force=force)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        for p in generated:
            print(p)

        sys.exit(0)

    # ---- execution mode (default) ----
    if path.suffix not in EXTENSION_TO_LEXICON:
        print(f"Error: unsupported file extension: {path.suffix}")
        sys.exit(1)

    script_dir = str(path.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    source = path.read_text(encoding="utf-8")
    lexicon = EXTENSION_TO_LEXICON[path.suffix]()
    source = transpile(source, lexicon)

    globals_context = {
        "__name__": "__main__",
        "__file__": str(path.resolve()),
        "__builtins__": __builtins__,
    }

    exec(compile(source, str(path), "exec"), globals_context)
