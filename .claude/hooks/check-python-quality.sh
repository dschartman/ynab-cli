#!/bin/bash
# Hook: PostToolUse for Write/Edit
# Runs ruff and mypy on edited Python files

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract the file path from the tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only run on Python files in src/
if [[ ! "$FILE_PATH" =~ \.py$ ]] || [[ ! "$FILE_PATH" =~ ^.*src/ynab_cli/.* ]]; then
  exit 0  # Not a Python source file, skip silently
fi

# Change to project directory
cd "$CLAUDE_PROJECT_DIR" || exit 1

# Run ruff check
if ! uv run ruff check "$FILE_PATH" 2>&1; then
  echo "Ruff check found issues in $FILE_PATH" >&2
  echo "Run: uv run ruff check $FILE_PATH --fix" >&2
  exit 2  # Blocking error
fi

# Run ruff format check
if ! uv run ruff format "$FILE_PATH" --check 2>&1; then
  echo "File needs formatting: $FILE_PATH" >&2
  echo "Run: uv run ruff format $FILE_PATH" >&2
  exit 2  # Blocking error
fi

# Run mypy on the file
if ! uv run mypy "$FILE_PATH" 2>&1; then
  echo "Mypy found type errors in $FILE_PATH" >&2
  exit 2  # Blocking error
fi

# All checks passed
echo "✓ Code quality checks passed for $FILE_PATH"
exit 0
