import subprocess
import sys
from pathlib import Path


def run_langpy(file: Path):
    return subprocess.run(
        [sys.executable, "-m", "langpy", str(file)],
        capture_output=True,
        text=True,
    )


# ─────────────────────────────────────────────────────────────
# IMPORT SIMPLE ENTRE ARCHIVOS HERMANOS
# main -> file1
# ─────────────────────────────────────────────────────────────

def test_import_sibling_module(tmp_path):
    main = tmp_path / "main.pyes"
    file1 = tmp_path / "file1.pyes"

    file1.write_text(
        "imprimir(verdadero)\n",
        encoding="utf-8",
    )

    main.write_text(
        "import file1\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "True" in result.stdout


# ─────────────────────────────────────────────────────────────
# IMPORT DESDE PAQUETE
# main -> folder.file2
# ─────────────────────────────────────────────────────────────

def test_import_from_package(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()

    file2 = folder / "file2.pyes"
    main = tmp_path / "main.pyes"

    file2.write_text(
        "imprimir(verdadero)\n",
        encoding="utf-8",
    )

    main.write_text(
        "import folder.file2\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "True" in result.stdout


# ─────────────────────────────────────────────────────────────
# IMPORT FROM x IMPORT y
# main -> from folder import file2
# ─────────────────────────────────────────────────────────────

def test_from_import_module(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()

    file2 = folder / "file2.pyes"
    main = tmp_path / "main.pyes"

    file2.write_text(
        "imprimir(verdadero)\n",
        encoding="utf-8",
    )

    main.write_text(
        "from folder import file2\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "True" in result.stdout


# ─────────────────────────────────────────────────────────────
# IMPORT RECURSIVO
# main -> file1 -> folder.file3
# ─────────────────────────────────────────────────────────────

def test_recursive_import_chain(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()

    main = tmp_path / "main.pyes"
    file1 = tmp_path / "file1.pyes"
    file3 = folder / "file3.pyes"

    file3.write_text(
        "imprimir(verdadero)\n",
        encoding="utf-8",
    )

    file1.write_text(
        "import folder.file3\n",
        encoding="utf-8",
    )

    main.write_text(
        "import file1\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "True" in result.stdout


# ─────────────────────────────────────────────────────────────
# PAQUETE CON __init__.pyes
# main -> import folder
# ─────────────────────────────────────────────────────────────

def test_package_init_import(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()

    init = folder / "__init__.pyes"
    main = tmp_path / "main.pyes"

    init.write_text(
        "imprimir(verdadero)\n",
        encoding="utf-8",
    )

    main.write_text(
        "import folder\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "True" in result.stdout


# ─────────────────────────────────────────────────────────────
# IMPORT MIXTO DE IDIOMAS
# main.pyes -> file_pt.pypt
# ─────────────────────────────────────────────────────────────

def test_cross_language_import(tmp_path):
    main = tmp_path / "main.pyes"
    file_pt = tmp_path / "file_pt.pypt"

    file_pt.write_text(
        "imprimir(verdadeiro)\n",
        encoding="utf-8",
    )

    main.write_text(
        "import file_pt\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
    assert "True" in result.stdout


# ─────────────────────────────────────────────────────────────
# IMPORT CIRCULAR (NO DEBE EXPLOTAR)
# main -> file1 -> main
# ─────────────────────────────────────────────────────────────

def test_circular_import(tmp_path):
    main = tmp_path / "main.pyes"
    file1 = tmp_path / "file1.pyes"

    main.write_text(
        "import file1\n",
        encoding="utf-8",
    )

    file1.write_text(
        "import main\n",
        encoding="utf-8",
    )

    result = run_langpy(main)
    assert result.returncode == 0
