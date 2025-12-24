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


def test_transpile_tree_recursive(tmp_path):
    """
    Verifica la transpilación recursiva profunda:
    test.pyes -> importa hijo1.pyes -> importa folder/hijo2.pyes
    """
    root = tmp_path

    # Nivel 0: Archivo principal
    (root / "test.pyes").write_text(
        "importar hijo1\nimprimir('test ok')",
        encoding="utf-8",
    )

    # Nivel 1: hijo1 importa a hijo2 (que está en una subcarpeta)
    # Usamos la sintaxis de importación de carpetas/módulos de Python
    (root / "hijo1.pyes").write_text(
        "importar folder.hijo2\nimprimir('hijo1 ok')",
        encoding="utf-8",
    )

    # Nivel 2: Subcarpeta y archivo hijo2
    sub = root / "folder"
    sub.mkdir()
    (sub / "hijo2.pyes").write_text(
        "imprimir('hijo2 ok')",
        encoding="utf-8",
    )

    # Ejecutamos la transpilación desde el punto de entrada
    result = run_langpy("--transpile", "test.pyes", cwd=root)

    assert result.returncode == 0

    # Recolectamos nombres de archivos generados de la salida para validar logs
    generated = {
        Path(line.strip()).name
        for line in result.stdout.splitlines()
        if line.strip()
    }

    # Validamos que todos los niveles se hayan procesado
    assert "test.py" in generated
    assert "hijo1.py" in generated
    assert "hijo2.py" in generated

    # Verificación de existencia física en sus respectivas rutas
    assert (root / "test.py").exists()
    assert (root / "hijo1.py").exists()
    assert (sub / "hijo2.py").exists()

    # Verificación de contenido (transpilación de palabras clave)
    assert "print('hijo2 ok')" in (
        sub / "hijo2.py").read_text(encoding="utf-8")
