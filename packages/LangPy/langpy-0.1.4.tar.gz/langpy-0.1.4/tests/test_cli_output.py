import sys
import subprocess
from pathlib import Path


def run_langpy(*args, cwd):
    # Mantenemos la estructura de tu base original para invocar el módulo
    return subprocess.run(
        [sys.executable, "-m", "langpy", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )

# --- Tests de Sobrescritura (Base) ---


def test_transpile_refuses_overwrite(tmp_path):
    (tmp_path / "main.pyes").write_text("imprimir('a')", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('existing')", encoding="utf-8")

    result = run_langpy("--transpile", "main.pyes", cwd=tmp_path)
    assert result.returncode != 0


def test_transpile_force_overwrite(tmp_path):
    (tmp_path / "main.pyes").write_text("imprimir('b')", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('old')", encoding="utf-8")

    result = run_langpy("--transpile", "--force", "main.pyes", cwd=tmp_path)
    assert result.returncode == 0
    assert "print" in (tmp_path / "main.py").read_text(encoding="utf-8")

# --- Test de Salida Específica (Adaptado) ---


def test_output_single_file(tmp_path):
    # Preparamos los archivos de prueba
    (tmp_path / "main.pyes").write_text("imprimir('hola')", encoding="utf-8")
    (tmp_path / "otro.pyes").write_text("imprimir('no')", encoding="utf-8")

    # Definimos la ruta de salida personalizada
    out_dir = tmp_path / "build"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "main.py"

    # Ejecutamos con la bandera --output
    result = run_langpy("--output", str(out_file), "main.pyes", cwd=tmp_path)

    # Verificaciones
    assert result.returncode == 0
    assert out_file.exists()
    assert "print('hola')" in out_file.read_text(encoding="utf-8")

    # Verificamos que no haya efectos secundarios (no se debe crear otro.py)
    assert not (tmp_path / "otro.py").exists()
