#!/bin/bash
# Claude Code PostToolUse hook for Python linting
# Runs ruff check and format on edited Python files

# Extract file path from JSON input via stdin
file_path=$(cat | python -c "import sys, json; print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))")

# Only lint Python files
[[ "$file_path" != *.py ]] && exit 0

# Check file exists
[[ ! -f "$file_path" ]] && exit 0

# Run ruff check with auto-fix
ruff check --fix "$file_path" 2>&1

# Run ruff format
ruff format "$file_path" 2>&1

# Exit 0 = success (non-blocking)
# Any unfixable issues will be shown to Claude in the output
exit 0
