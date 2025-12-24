import sys
from pathlib import Path
from importlib.metadata import version

from langpy.cli.messages import info, help
from langpy.cli.transpile.tree import transpile_tree
from langpy.cli.transpile.transpiler import (
    _transpile_file,
    _transpile_to_memory,
)


def main() -> None:
    args = sys.argv[1:]

    # ---- no args ----
    if not args:
        print(info())
        sys.exit(0)

    # ---- informational flags ----
    if "--help" in args:
        print(help())
        sys.exit(0)

    if "--version" in args:
        print(version("langpy"))
        sys.exit(0)

    transpile_mode = "--transpile" in args
    force = "--force" in args
    output_mode = "--output" in args

    if force and not transpile_mode:
        print("Error: --force can only be used with --transpile")
        sys.exit(1)

    if output_mode and transpile_mode:
        print("Error: --output cannot be used with --transpile")
        sys.exit(1)

    # ---- --output mode ----
    if output_mode:
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

        try:
            tmp_py = _transpile_file(in_path, force=True)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            tmp_py.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

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

    # ---- transpile tree mode ----
    if transpile_mode:
        output_entry = path.with_suffix(".py")

        if output_entry.exists() and not force:
            print(f"Error: output file already exists: {output_entry}")
            sys.exit(1)

        try:
            generated = transpile_tree(path, force=force)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        for p in generated:
            print(p)

        sys.exit(0)

    # ---- execution mode (default) ----
    try:
        source = _transpile_to_memory(path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    script_dir = str(path.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    globals_context = {
        "__name__": "__main__",
        "__file__": str(path.resolve()),
        "__builtins__": __builtins__,
    }

    exec(compile(source, str(path), "exec"), globals_context)
