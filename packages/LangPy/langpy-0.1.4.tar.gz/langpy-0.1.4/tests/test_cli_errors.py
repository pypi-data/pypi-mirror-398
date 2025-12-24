import sys
import subprocess
from pathlib import Path


def run_langpy(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "langpy", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )

# --- Tests de Conflictos y Errores ---


def test_output_and_transpile_conflict(tmp_path):
    """Verifica que no se pueden usar --output y --transpile al mismo tiempo."""
    (tmp_path / "a.pyes").write_text("imprimir('x')", encoding="utf-8")

    # Intentamos usar ambas banderas simultáneamente
    result = run_langpy("--output", "out.py",
                        "--transpile", "a.pyes", cwd=tmp_path)

    assert result.returncode != 0
    # Comprobamos que el mensaje de error mencione el conflicto
    error_msg = (result.stdout + result.stderr).lower()
    assert "cannot be used" in error_msg or "conflict" in error_msg


def test_unsupported_extension(tmp_path):
    """Verifica que el compilador falle con extensiones no soportadas."""
    (tmp_path / "a.txt").write_text("hola", encoding="utf-8")

    result = run_langpy("a.txt", cwd=tmp_path)

    assert result.returncode != 0

# --- Tests Previos (Manteniendo consistencia) ---


def test_output_single_file(tmp_path):
    (tmp_path / "main.pyes").write_text("imprimir('hola')", encoding="utf-8")

    out_file = tmp_path / "build" / "main.py"
    out_file.parent.mkdir(exist_ok=True)

    result = run_langpy("--output", str(out_file), "main.pyes", cwd=tmp_path)

    assert result.returncode == 0
    assert out_file.exists()
    assert "print('hola')" in out_file.read_text(encoding="utf-8")
