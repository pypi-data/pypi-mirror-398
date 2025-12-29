#!/usr/bin/env python3
"""Run the project's lint and type-check suite."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Mapping, Sequence


def run(
    name: str,
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> int:
    print(f"\n>>> {name}")
    result = subprocess.run(command, check=False, env=env)
    if result.returncode != 0:
        print(f"{name} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    commands = [
        ("black", ["uv", "run", "black", "src", "tests", "--check"]),
        (
            "isort",
            ["uv", "run", "isort", "src", "tests", "--check-only"],
        ),
        ("flake8", ["uv", "run", "flake8", "src", "tests"]),
        ("pylint", ["uv", "run", "pylint", "src", "tests"]),
        (
            "mypy-package",
            ["uv", "run", "mypy", "-p", "zoho_projects_sdk"],
        ),
        # Skip mypy-tests since tests are excluded in mypy configuration
        # (
        #     "mypy-tests",
        #     ["uv", "run", "mypy", "tests"],
        # ),
    ]

    for name, command in commands:
        env = None
        if name.startswith("mypy"):
            env = {**os.environ, "MYPYPATH": "src"}
        code = run(name, command, env=env)
        if code != 0:
            return code

    print("\nAll lint checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
