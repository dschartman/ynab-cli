# Claude Code Memory - YNAB CLI

## Project Purpose

A comprehensive Python CLI tool for the YNAB (You Need A Budget) API, designed specifically for programmatic use by Claude Code and automation tools. Provides full API coverage for budgets, accounts, categories, transactions, and goals.

## Target User

**Primary user: Claude Code** - All design decisions prioritize programmatic usage:
- JSON output on all commands
- Clear, predictable command structure
- Environment-based authentication
- Comprehensive error messages
- Global installation via `uv tool install`

## Critical Context

### API Understanding
- **Full API analysis**: See `docs/YNAB_API_ANALYSIS.md`
- **OpenAPI spec**: Available in `docs/openapi_spec.yaml` (3,430 lines)

### Design Decisions
- **Global tool**: Installed via `uv tool install ynab-cli` (works anywhere)
- **Config location**: `~/.config/ynab/config.toml`
- **Authentication**: `ynab login` command + environment variable support
- **No database**: Direct API calls (simple, fast, stateless)
- **Rate limiting**: Built-in (200 req/hour YNAB limit)
- **CLI framework**: Typer (modern, type-hint based, built on Click)

## Key Technical Concepts

### Milliunits
All YNAB monetary amounts are integers in "milliunits":
- $1.00 = 1000
- $-12.45 = -12450
- CLI should convert automatically

### Delta Syncing
- Each API response includes `server_knowledge` integer
- Pass as `last_knowledge_of_server` query param for incremental updates
- Reduces API calls significantly

### Budget ID Shortcuts
- `"last-used"` - Most recently used budget
- `"default"` - User's default budget
- Actual UUID also works

### Goal Types
- `MF` (Monthly Funding) - Monthly budget target
- `NEED` (Plan Your Spending) - Recurring irregular expenses
- `TBD` (Target Balance by Date) - Savings with deadline
- `TB` (Target Category Balance) - One-time savings goal
- `DEBT` (Debt Payoff) - Pay off debt by date

### Transfer Transactions
- Transfers create TWO linked transactions
- Use account's `transfer_payee_id` to create transfers
- Both have `transfer_transaction_id` linking them

## Code Quality Hooks

This project uses [Claude Code Hooks](https://code.claude.com/docs/en/hooks) to automatically enforce code quality standards.

**Configured Hooks:**

1. **PostToolUse Hook** - Runs after editing Python files in `src/ynab_cli/`:
   - ✓ Ruff linting (`ruff check`)
   - ✓ Ruff formatting (`ruff format --check`)
   - ✓ Mypy type checking
   - Blocks edits that don't pass checks

2. **Stop Hook** - Runs before Claude finishes responding:
   - ✓ Full codebase ruff check and format verification
   - ✓ Complete mypy type checking on `src/ynab_cli/`
   - ✓ Test suite execution (`pytest tests/test_cli/`)
   - Prevents stopping until all checks pass

**Hook Files:**
- `.claude/settings.json` - Hook configuration (committed to git)
- `.claude/hooks/check-python-quality.sh` - PostToolUse script
- `.claude/hooks/verify-quality.sh` - Stop script
- `.claude/hooks/README.md` - Hook documentation

**Managing Hooks:**
- View/edit: `/hooks` command in Claude Code
- Disable temporarily: Set `"disableAllHooks": true` in `.claude/settings.json`
- Debug: Run `claude --debug` or press `Ctrl+O` for verbose mode

## Using Trace for Work Tracking

This project uses [Trace](https://github.com/dschartman/trace) for persistent
work tracking across AI sessions.

**When to use trace vs TodoWrite:**

Use trace instead of TodoWrite for any non-trivial work. If it involves multiple
files, could span sessions, or needs to persist - use trace.

- **TodoWrite**: Single-session trivial tasks only
- **Trace**: Everything else (features, bugs, planning, multi-step work)
- **When in doubt**: Use trace

**Why this matters:** Trace persists across sessions and commits to git. TodoWrite
is ephemeral. For a tool designed around persistent work tracking, using TodoWrite
defeats the purpose.

**Setup (required once per project):**

```bash
trc init  # Run this first in your git repo
```

If you forget, you'll see: "Error: Project not initialized. Run 'trc init' first"

**Core workflow:**

```bash
# Create work
trc create "title" --description "context"
trc create "subtask" --description "details" --parent <id>

# Discover work
trc ready              # What's unblocked and ready to work on
trc list               # Current backlog (excludes closed)
trc show <id>          # Full details with dependencies

# Complete work
trc close <id> [...]   # Close one or more issues
```

**Essential details:**

- `--description` is required (preserves context across sessions for AI agents)
  - Use `--description ""` to explicitly skip if truly not needed
- Structure is fluid: Break down or reorganize as understanding evolves
- Use `--parent <id>` to create hierarchical breakdowns
- Cross-project: Add `--project <name>` to work across repositories
- Use `trc <command> --help` for full options

For more details: https://github.com/dschartman/trace

## Project Structure

```
ynab-cli/
├── src/ynab_cli/
│   ├── api/              # YNAB API client
│   │   └── client.py     # HTTP client with rate limiting
│   ├── cli/              # Typer-based CLI
│   │   ├── main.py       # Entry point and command groups
│   │   ├── budgets.py    # Budget commands
│   │   ├── accounts.py   # Account commands
│   │   ├── transactions.py # Transaction commands
│   │   └── auth.py       # login/logout commands
│   ├── config.py         # Settings management
│   └── __init__.py
│
├── tests/                # Test suite (TDD)
│   ├── conftest.py       # Shared fixtures
│   ├── test_config.py    # Config tests
│   ├── test_api/         # API client tests
│   └── test_cli/         # CLI command tests
│       └── test_main.py
│
├── docs/
│   ├── YNAB_API_ANALYSIS.md
│   └── openapi_spec.yaml     # Full YNAB API spec
│
├── pyproject.toml        # Project config
├── CLAUDE.md            # This file
└── README.md            # User documentation

# User's system after install:
~/.config/ynab/
└── config.toml          # Token stored here
```

## CLI Command Structure

```bash
# Authentication
ynab login               # Configure API credentials

# Budgets
ynab budgets list        # List all budgets (JSON output by default)
ynab budgets get [id]    # Get budget details
ynab budgets settings    # Budget settings

# Accounts
ynab accounts list       # List accounts
ynab accounts get <id>   # Account details
ynab accounts create     # Create account

# Categories
ynab categories list     # List categories
ynab categories get <id> # Category details

# Transactions
ynab transactions list   # List transactions
ynab transactions get <id>
ynab transactions create
ynab transactions update <id>
ynab transactions delete <id>

# Months
ynab months get <month>  # Month details

# Common options:
--table                  # Human-readable table output (default is JSON)
--budget <id>            # Override default budget
```

## Development Guidelines

### For Claude Code
- Always use trace for work tracking (not TodoWrite)
- Reference API documentation before implementing endpoints
- Test with actual YNAB API (user has account)
- Follow existing patterns in the codebase (see `src/ynab_cli/`)
- Prioritize JSON output for programmatic use
- **Code quality hooks enforce standards automatically** - they'll block bad code

### Code Standards
- Python 3.12+
- Async/await for API calls (httpx)
- Typer for CLI framework (type-hint based)
- Pydantic for config/validation
- Type hints everywhere (required for Typer)
- Clear error messages

### Code Quality Checks

**Automated via Hooks** - Code quality is enforced automatically:

- **PostToolUse Hook**: Runs after editing Python files in `src/ynab_cli/`
  - Ruff linting and formatting checks
  - Mypy type checking
  - Blocks the edit if any check fails

- **Stop Hook**: Runs before Claude finishes responding
  - Full codebase ruff check and format verification
  - Complete mypy type checking
  - Test suite execution
  - Prevents stopping until all checks pass

**Manual checks** (if needed):
```bash
# Run ruff for linting and formatting
uv run ruff check .
uv run ruff format .

# Run mypy for type checking
uv run mypy src/ynab_cli

# Run tests
uv run pytest tests/test_cli/
```

**Hook configuration**: See `.claude/settings.json` and `.claude/hooks/`
**Manage hooks**: Use `/hooks` command or edit settings files directly

### Testing - Test-Driven Development (TDD) Required

**CRITICAL: Write tests BEFORE implementation code.**

TDD Workflow:
1. Write a failing test that defines the desired behavior
2. Run the test to confirm it fails (red)
3. Write minimal code to make the test pass (green)
4. Refactor for clarity and maintainability
5. Repeat

Testing Standards:
- Use pytest with pytest-asyncio for all tests
- Every function/method must have corresponding tests
- Test files mirror source structure: `tests/test_*.py` matches `src/ynab_cli/*.py`
- Mock external dependencies (API responses, file I/O, environment variables)
- Test CLI commands using Typer's testing utilities
- Validate JSON output format for all commands
- Aim for >90% code coverage
- Tests must be fast (<100ms per test for unit tests)

Test Organization:
```
tests/
├── test_config.py       # Config and settings tests
├── test_api/
│   └── test_client.py   # API client tests
└── test_cli/
    ├── test_main.py     # CLI entry point tests
    ├── test_budgets.py  # Budget command tests
    └── test_auth.py     # Auth command tests
```

Key Testing Tools:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `typer.testing.CliRunner` - CLI command testing
- `unittest.mock` - Mocking dependencies
- `pytest-cov` - Coverage reporting

## Quick Reference

### Getting Started
```bash
# Install dependencies
uv sync

# Run locally during development
uv run python -m ynab_cli.cli.main --help

# Install globally for testing
uv tool install .

# Use the tool
ynab login
ynab budgets list           # JSON output (default)
ynab budgets list --table   # Table output (human-readable)
```

### Key Files
- `docs/YNAB_API_ANALYSIS.md` - Complete API reference
- `docs/openapi_spec.yaml` - Official API spec
- `CLAUDE.md` - This file (project context)

### Important Links
- YNAB API Docs: https://api.ynab.com/
- OpenAPI Spec: https://api.ynab.com/papi/open_api_spec.yaml
- Get API Token: https://app.ynab.com/settings/developer
- Trace Documentation: https://github.com/dschartman/trace

## Current Status

Project initialized. Ready to build.

Next steps tracked in trace (`trc list`).
