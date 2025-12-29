#!/usr/bin/env python3
"""Run the project's lint and type-check suite."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Mapping, Optional, Sequence


def run(
    name: str,
    command: Sequence[str],
    *,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    print(f"\n>>> {name}")
    result = subprocess.run(command, check=False, env=env)
    if result.returncode != 0:
        print(f"{name} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    commands = [
        ("black", [sys.executable, "-m", "black", "src", "tests", "--check"]),
        (
            "isort",
            [
                sys.executable,
                "-m",
                "isort",
                "src",
                "tests",
                "--check-only",
            ],
        ),
        ("flake8", [sys.executable, "-m", "flake8", "src", "tests"]),
        ("pylint", [sys.executable, "-m", "pylint", "src", "tests"]),
        (
            "mypy-package",
            [
                sys.executable,
                "-m",
                "mypy",
                "-p",
                "zoho_creator_sdk",
            ],
        ),
        (
            "mypy-tests",
            [sys.executable, "-m", "mypy", "tests"],
        ),
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
