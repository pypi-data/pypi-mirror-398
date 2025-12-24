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


def test_transpile_with_imports(tmp_path):
    (tmp_path / "mod.pyes").write_text(
        "definir f():\n    retornar 1", encoding="utf-8"
    )

    (tmp_path / "main.pyes").write_text(
        "importar mod\nimprimir(mod.f())", encoding="utf-8"
    )

    result = run_langpy("--transpile", "main.pyes", cwd=tmp_path)
    assert result.returncode == 0

    assert (tmp_path / "main.py").exists()
    assert (tmp_path / "mod.py").exists()
