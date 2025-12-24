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
