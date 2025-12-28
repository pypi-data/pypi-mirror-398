from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_force_mock_is_ignored_inside_binary_ninja_process() -> None:
    """FORCE_BINJA_MOCK must not clobber a real Binary Ninja runtime."""
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"

    env = os.environ.copy()
    env["FORCE_BINJA_MOCK"] = "1"
    env.pop("ALLOW_BINJA_MOCK_IN_BINARY_NINJA", None)

    # Ensure the subprocess imports this checkout, not an installed wheel.
    env["PYTHONPATH"] = str(src_dir) + os.pathsep + env.get("PYTHONPATH", "")

    code = """
import sys
sys.executable = "binaryninja"

import binja_test_mocks.binja_api  # noqa: F401

import sys as _sys
print("binaryninja" in _sys.modules)
""".strip()

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"
