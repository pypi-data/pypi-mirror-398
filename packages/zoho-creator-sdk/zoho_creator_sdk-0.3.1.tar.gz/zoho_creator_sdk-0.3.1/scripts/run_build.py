#!/usr/bin/env python3
"""Build source and wheel distributions for the project."""

from __future__ import annotations

import subprocess
import sys
from typing import Optional, Sequence


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv or sys.argv[1:])
    command = [sys.executable, "-m", "build", *args]
    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
