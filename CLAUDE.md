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
- **Full API analysis**: See `YNAB_API_ANALYSIS.md`
- **Goals/Targets**: See `LINKED_TRANSACTIONS_AND_TARGETS.md` and `TARGET_BUDGET_CALCULATION.md`
- **OpenAPI spec**: Available in `openapi_spec.yaml` (3,430 lines)

### Design Decisions
- **Global tool**: Installed via `uv tool install ynab-cli` (works anywhere)
- **Config location**: `~/.config/ynab/config.toml`
- **Authentication**: `ynab login` command + environment variable support
- **No database**: Direct API calls (simple, fast, stateless)
- **Rate limiting**: Built-in (200 req/hour YNAB limit)
- **CLI framework**: Typer (modern, type-hint based, built on Click)

### Code to Leverage
The `ynab-budget` project at `../ynab-budget/` has production-ready code:
- API client with rate limiting (`api/client.py`)
- Pydantic Settings config management (`config.py`)
- CLI structure pattern (`cli/main.py`) - but we're using Typer instead of Click
- See `LEARNINGS_FROM_YNAB_BUDGET.md` for details

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
│   ├── LINKED_TRANSACTIONS_AND_TARGETS.md
│   ├── TARGET_BUDGET_CALCULATION.md
│   └── LEARNINGS_FROM_YNAB_BUDGET.md
│
├── openapi_spec.yaml     # Full YNAB API spec
├── pyproject.toml        # Project config
├── CLAUDE.md            # This file
└── README.md            # User documentation

# User's system after install:
~/.config/ynab/
└── config.toml          # Token stored here
```

## CLI Command Structure (Planned)

```bash
# Authentication
ynab login               # Configure API credentials

# Budgets
ynab budgets list        # List all budgets
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
ynab months list         # Budget months
ynab months get <month>  # Month details

# All commands support:
--json                   # JSON output
--budget <id>            # Override default budget
```

## Development Guidelines

### For Claude Code
- Always use trace for work tracking (not TodoWrite)
- Reference API documentation before implementing endpoints
- Test with actual YNAB API (user has account)
- Follow patterns from ynab-budget project
- Prioritize JSON output for programmatic use

### Code Standards
- Python 3.12+
- Async/await for API calls (httpx)
- Typer for CLI framework (type-hint based)
- Pydantic for config/validation
- Type hints everywhere (required for Typer)
- Clear error messages

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
ynab budgets list --json
```

### Key Files
- `YNAB_API_ANALYSIS.md` - Complete API reference
- `LEARNINGS_FROM_YNAB_BUDGET.md` - Code to copy
- `openapi_spec.yaml` - Official API spec
- `CLAUDE.md` - This file (project context)

### Important Links
- YNAB API Docs: https://api.ynab.com/
- OpenAPI Spec: https://api.ynab.com/papi/open_api_spec.yaml
- Get API Token: https://app.ynab.com/settings/developer
- Trace Documentation: https://github.com/dschartman/trace

## Current Status

Project initialized. Ready to build.

Next steps tracked in trace (`trc list`).
