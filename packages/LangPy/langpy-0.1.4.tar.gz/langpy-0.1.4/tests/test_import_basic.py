import subprocess
import sys
from pathlib import Path


def run_langpy(file: Path):
    return subprocess.run(
        [sys.executable, "-m", "langpy", str(file)],
        capture_output=True,
        text=True,
    )


def test_spanish_basic(tmp_path):
    file = tmp_path / "main.pyes"
    file.write_text("imprimir(verdadero)\n", encoding="utf-8")

    result = run_langpy(file)
    assert result.returncode == 0
    assert "True" in result.stdout


def test_portuguese_basic(tmp_path):
    file = tmp_path / "main.pypt"
    file.write_text("imprimir(verdadeiro)\n", encoding="utf-8")

    result = run_langpy(file)
    assert result.returncode == 0
    assert "True" in result.stdout


def test_french_basic(tmp_path):
    file = tmp_path / "main.pyfr"
    file.write_text("imprimer(vrai)\n", encoding="utf-8")

    result = run_langpy(file)
    assert result.returncode == 0
    assert "True" in result.stdout
