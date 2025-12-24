import subprocess
import sys
from pathlib import Path


def run_langpy(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "langpy", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_cli_no_args():
    result = run_langpy()
    assert result.returncode == 0
    assert "langpy" in result.stdout.lower() or "uso" in result.stdout.lower()


def test_cli_version():
    result = run_langpy("--version")
    assert result.returncode == 0
    assert result.stdout.strip()
