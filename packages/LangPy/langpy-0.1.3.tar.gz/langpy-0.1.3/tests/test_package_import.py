import subprocess
import sys
from pathlib import Path


def run_langpy(file: Path):
    return subprocess.run(
        [sys.executable, "-m", "langpy", str(file)],
        capture_output=True,
        text=True,
    )


def test_package_import(tmp_path):
    pkg = tmp_path / "paquete"
    pkg.mkdir()

    init = pkg / "__init__.pyes"
    init.write_text(
        "definir saludar():\n    retornar 'hola'\n",
        encoding="utf-8",
    )

    mod = pkg / "modulo.pypt"
    mod.write_text(
        "definir valor():\n    retornar 5\n",
        encoding="utf-8",
    )

    main = tmp_path / "main.pyes"
    main.write_text(
        "importar paquete\n"
        "desde paquete importar modulo\n"
        "imprimir(paquete.saludar())\n"
        "imprimir(modulo.valor())\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "hola" in result.stdout
    assert "5" in result.stdout
