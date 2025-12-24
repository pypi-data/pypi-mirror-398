import sys
from pathlib import Path
from importlib.machinery import ModuleSpec
from importlib.abc import MetaPathFinder, Loader

from langpy.core.transpiler import transpile
from langpy.core.lexicon.es import SpanishLexicon
from langpy.core.lexicon.pt import PortugueseLexicon
from langpy.core.lexicon.fr import FrenchLexicon


EXTENSION_TO_LEXICON = {
    ".pyes": SpanishLexicon,
    ".pypt": PortugueseLexicon,
    ".pyfr": FrenchLexicon,
}


class LangPyFinder(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        parts = fullname.split(".")
        module_name = parts[-1]

        search_paths = path if path is not None else sys.path

        for base in search_paths:
            base_path = Path(base)

            # ----- módulo suelto: modulo.<ext> -----
            for ext in EXTENSION_TO_LEXICON:
                module_file = base_path / f"{module_name}{ext}"
                if module_file.is_file():
                    return ModuleSpec(
                        name=fullname,
                        loader=LangPyLoader(),
                        origin=str(module_file.resolve()),
                        is_package=False,
                    )

            # ----- paquete: modulo/__init__.<ext> -----
            package_dir = base_path / module_name
            if package_dir.is_dir():
                for ext in EXTENSION_TO_LEXICON:
                    init_file = package_dir / f"__init__{ext}"
                    if init_file.is_file():
                        spec = ModuleSpec(
                            name=fullname,
                            loader=LangPyLoader(),
                            origin=str(init_file.resolve()),
                            is_package=True,
                        )
                        spec.submodule_search_locations = [
                            str(package_dir.resolve())]
                        return spec

        return None


class LangPyLoader(Loader):
    def create_module(self, spec):
        # Usar el mecanismo estándar de Python
        return None

    def exec_module(self, module):
        spec = module.__spec__
        origin = Path(spec.origin)

        ext = origin.suffix
        lexicon_cls = EXTENSION_TO_LEXICON.get(ext)
        if lexicon_cls is None:
            raise ImportError(f"Unsupported PyEs extension: {ext}")

        lexicon = lexicon_cls()

        source = origin.read_text(encoding="utf-8")
        output = transpile(source, lexicon)

        module.__file__ = str(origin)
        module.__loader__ = self
        module.__spec__ = spec

        if spec.submodule_search_locations is not None:
            module.__package__ = module.__name__
            module.__path__ = spec.submodule_search_locations
        else:
            module.__package__ = module.__name__.rpartition(".")[0]

        exec(output, module.__dict__)
