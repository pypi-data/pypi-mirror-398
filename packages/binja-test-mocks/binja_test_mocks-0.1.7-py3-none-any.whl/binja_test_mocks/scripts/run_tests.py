"""Module entry point for test runner."""

import os
import shutil
import subprocess
import sys


def main() -> None:
    """Run pytest with FORCE_BINJA_MOCK environment variable set."""
    # Ensure we're using mocks
    env = os.environ.copy()
    env["FORCE_BINJA_MOCK"] = "1"

    # Add any additional pytest arguments passed to this script
    pytest_args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Check if uv is available
    if shutil.which("uv"):
        # Use uv run to ensure we're in the right environment
        cmd = ["uv", "run", "pytest", *pytest_args]
        print(f"Running: {' '.join(cmd)}")
        print("With FORCE_BINJA_MOCK=1")
    else:
        # Fallback to direct pytest
        cmd = [sys.executable, "-m", "pytest", *pytest_args]
        print(f"Running: {' '.join(cmd)}")
        print("With FORCE_BINJA_MOCK=1")
        print("Note: Install uv for better dependency management: https://github.com/astral-sh/uv")

    result = subprocess.run(cmd, env=env, check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
