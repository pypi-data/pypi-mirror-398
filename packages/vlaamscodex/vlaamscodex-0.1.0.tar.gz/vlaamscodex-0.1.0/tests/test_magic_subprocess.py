from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_magic_python_file_plats_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "examples" / "hello.plats"

    p = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    assert p.stdout == "gdag aan weeireld\n"

