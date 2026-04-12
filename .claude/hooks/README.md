# Claude Code Hooks

This directory contains hooks that automatically enforce code quality standards.

## Configured Hooks

### PostToolUse: check-python-quality.sh

**Triggers:** After `Write` or `Edit` operations on Python files in `src/ynab_cli/`

**What it does:**
1. Runs `ruff check` on the modified file
2. Runs `ruff format --check` to verify formatting
3. Runs `mypy` type checking on the modified file

**Behavior:**
- Exits with code 2 (blocking error) if any check fails
- Shows helpful error messages with commands to fix issues
- Skips silently for non-Python files or files outside `src/ynab_cli/`

### Stop: verify-quality.sh

**Triggers:** Before Claude finishes responding (Stop event)

**What it does:**
1. Runs `ruff check .` on all files
2. Runs `ruff format . --check` on all files
3. Runs `mypy src/ynab_cli` for type checking
4. Runs `pytest tests/test_cli/` to ensure tests pass

**Behavior:**
- Exits with code 2 (blocking error) if any check fails
- Prevents Claude from stopping until all checks pass
- Provides helpful error messages and commands to fix issues
- Returns success context to Claude when all checks pass

## How Hooks Work

Hooks receive JSON input via stdin with information about the event (tool name, file path, etc.). They can:

- **Exit 0**: Success, allow the action to proceed
- **Exit 2**: Blocking error, prevent the action and show stderr to Claude
- **Other exit codes**: Non-blocking error, shown in verbose mode only

## Managing Hooks

View and manage hooks using the `/hooks` command in Claude Code, or edit `.claude/settings.json` directly.

To temporarily disable all hooks, add to `.claude/settings.json`:
```json
{
  "disableAllHooks": true
}
```

## Debugging

Run `claude --debug` to see hook execution details, or press `Ctrl+O` to toggle verbose mode and see hook progress in the transcript.
