import sys
from langpy.core.importer import LangPyFinder


def _register_import_hook():
    for finder in sys.meta_path:
        if isinstance(finder, LangPyFinder):
            return
    sys.meta_path.insert(0, LangPyFinder())


_register_import_hook()
