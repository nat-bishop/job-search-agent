#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "ruff>=0.8.0",
# ]
# ///
"""Claude Code PostToolUse hook for Python linting.

Runs ruff check and format on edited Python files.
Uses UV single-file script pattern for dependency isolation.
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    file_path = payload.get("tool_input", {}).get("file_path", "")

    # Only lint Python files
    if not file_path.endswith(".py"):
        return

    # Check file exists
    if not Path(file_path).exists():
        return

    # Run ruff check with auto-fix
    result = subprocess.run(
        ["ruff", "check", "--fix", file_path],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Run ruff format
    result = subprocess.run(
        ["ruff", "format", file_path],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
