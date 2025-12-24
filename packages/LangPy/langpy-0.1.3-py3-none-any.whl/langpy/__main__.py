import sys

from langpy.core.importer import LangPyFinder


def _register_import_hook():
    # Evitar registrar el finder más de una vez
    for finder in sys.meta_path:
        if isinstance(finder, LangPyFinder):
            return

    sys.meta_path.insert(0, LangPyFinder())


def main():
    _register_import_hook()

    # Import tardío a propósito: el hook debe existir antes
    from langpy.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
