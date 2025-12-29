#!/usr/bin/env python3
"""Execute the test suite with coverage enforcement."""

from __future__ import annotations

import subprocess
import sys
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    command = ["uv", "run", "pytest", *args]
    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
