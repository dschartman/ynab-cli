#!/bin/bash
# Hook: Stop
# Verifies all code quality checks pass before finishing

set -e

# Change to project directory
cd "$CLAUDE_PROJECT_DIR" || exit 1

# Run ruff check on all files
echo "Running ruff check..." >&2
if ! uv run ruff check . 2>&1; then
  cat >&2 <<EOF
Ruff check failed. Please fix linting errors before finishing.
Run: uv run ruff check . --fix
EOF
  exit 2  # Blocking error
fi

# Run ruff format check on all files
echo "Checking code formatting..." >&2
if ! uv run ruff format . --check 2>&1; then
  cat >&2 <<EOF
Code formatting check failed. Please format the code before finishing.
Run: uv run ruff format .
EOF
  exit 2  # Blocking error
fi

# Run mypy on src/
echo "Running mypy type checking..." >&2
if ! uv run mypy src/ynab_cli 2>&1; then
  cat >&2 <<EOF
Mypy type checking failed. Please fix type errors before finishing.
Run: uv run mypy src/ynab_cli
EOF
  exit 2  # Blocking error
fi

# Run tests to ensure nothing broke
echo "Running tests..." >&2
if ! uv run pytest tests/test_cli/ -q 2>&1; then
  cat >&2 <<EOF
Tests failed. Please ensure all tests pass before finishing.
Run: uv run pytest tests/test_cli/
EOF
  exit 2  # Blocking error
fi

# All checks passed - return success with context for Claude
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "additionalContext": "✓ All code quality checks passed: ruff, mypy, and tests"
  }
}
EOF

exit 0
