# ynab-cli

A comprehensive Python CLI for the YNAB (You Need A Budget) API, designed specifically for programmatic use by Claude Code and automation tools.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Full API Coverage**: Budgets, accounts, categories, transactions, and months
- **Programmatic Design**: JSON output on all commands for easy parsing
- **Simple Authentication**: One-time `ynab login` command
- **Transfer Helper**: Simplified interface for moving money between accounts
- **Automatic Conversions**: Milliunits ↔ dollars handled transparently
- **Global Installation**: Works from any directory via `uv tool install`
- **Rate Limiting**: Built-in respect for YNAB's 200 req/hour limit

## Installation

Install globally using [uv](https://github.com/astral-sh/uv):

```bash
uv tool install ynab-cli
```

Or install from source:

```bash
git clone https://github.com/dschartman/ynab-cli.git
cd ynab-cli
uv tool install .
```

## Quick Start

### 1. Get Your API Token

Get your personal access token from: https://app.ynab.com/settings/developer

### 2. Login

```bash
ynab login
# Follow prompts to enter your token and budget ID
```

Your credentials are saved to `~/.config/ynab/config.toml` with secure permissions.

### 3. Start Using

```bash
# List all budgets
ynab budgets list --json

# View accounts
ynab accounts list

# Get current month details
ynab months get

# List recent transactions
ynab transactions list --limit 10
```

## Authentication

### Using the Login Command (Recommended)

```bash
ynab login
```

This stores your credentials in `~/.config/ynab/config.toml`.

### Using Environment Variables

```bash
export YNAB_API_TOKEN="your_token_here"
export YNAB_BUDGET_ID="last-used"  # or specific budget UUID
```

Environment variables take precedence over the config file.

### Budget ID Shortcuts

- `last-used` - Most recently used budget (default)
- `default` - Your default budget
- `<uuid>` - Specific budget UUID

## Command Reference

### Budgets

```bash
# List all budgets
ynab budgets list
ynab budgets list --json

# Get specific budget
ynab budgets get [budget-id]
ynab budgets get last-used --json

# Get budget settings
ynab budgets settings
```

### Accounts

```bash
# List accounts
ynab accounts list
ynab accounts list --json

# Get specific account
ynab accounts get <account-id>
```

### Transactions

```bash
# List transactions
ynab transactions list
ynab transactions list --since-date 2024-01-01
ynab transactions list --type unapproved
ynab transactions list --limit 20 --json

# Create transaction
ynab transactions create \\
  --account <account-id> \\
  --date 2024-01-15 \\
  --amount -12.45 \\
  --payee <payee-id> \\
  --category <category-id> \\
  --memo "Coffee" \\
  --cleared \\
  --approved

# Update transaction
ynab transactions update <txn-id> \\
  --amount -15.00 \\
  --memo "Updated memo"

# Delete transaction
ynab transactions delete <txn-id> --confirm

# Transfer between accounts
ynab transactions transfer \\
  --from-account "Checking" \\
  --to-account "Savings" \\
  --amount 100.00 \\
  --date 2024-01-15 \\
  --memo "Monthly savings"
```

### Categories

```bash
# List categories
ynab categories list
ynab categories list --json

# Get specific category
ynab categories get <category-id>
```

### Months

```bash
# Get current month
ynab months get

# Get specific month
ynab months get 2024-01-01

# JSON output for parsing
ynab months get current --json
```

## Usage Examples

### For Claude Code / Automation

All commands support `--json` for programmatic parsing:

```bash
# Get account balances for analysis
ynab accounts list --json | jq '.accounts[] | {name, balance}'

# Find unapproved transactions
ynab transactions list --type unapproved --json

# Calculate total spending by category
ynab months get 2024-01-01 --json | \\
  jq '.month.categories[] | {name, activity}'

# Create automated transfer
ynab transactions transfer \\
  --from-account "Checking" \\
  --to-account "Emergency Fund" \\
  --amount 500.00 \\
  --date $(date +%Y-%m-%d) \\
  --memo "Automated monthly transfer" \\
  --json
```

### Budget Analysis Example

```bash
# Get month data
MONTH_DATA=$(ynab months get 2024-01-01 --json)

# Extract key metrics
INCOME=$(echo "$MONTH_DATA" | jq '.month.income')
BUDGETED=$(echo "$MONTH_DATA" | jq '.month.budgeted')
ACTIVITY=$(echo "$MONTH_DATA" | jq '.month.activity')
TO_BE_BUDGETED=$(echo "$MONTH_DATA" | jq '.month.to_be_budgeted')

echo "Income: $((INCOME / 1000))"
echo "Budgeted: $((BUDGETED / 1000))"
echo "Activity: $((ACTIVITY / 1000))"
echo "To Be Budgeted: $((TO_BE_BUDGETED / 1000))"
```

### Filtering and Searching

```bash
# Find transactions since a date
ynab transactions list --since-date 2024-01-01 --json | \\
  jq '.transactions[] | select(.amount < 0) | {date, payee_name, amount}'

# Get accounts with negative balances
ynab accounts list --json | \\
  jq '.accounts[] | select(.balance < 0) | {name, balance}'

# Find categories over budget
ynab months get current --json | \\
  jq '.month.categories[] | select(.activity > .budgeted) | {name, budgeted, activity}'
```

## Configuration

### Config File Location

`~/.config/ynab/config.toml`

Example:
```toml
# YNAB CLI Configuration
api_token = "your_token_here"
budget_id = "last-used"
```

### Environment Variables

- `YNAB_API_TOKEN` - Your YNAB API token
- `YNAB_BUDGET_ID` - Default budget ID

Priority: Environment variables > Config file > Defaults

## Milliunits

YNAB stores all monetary amounts as integers in "milliunits":
- $1.00 = 1000 milliunits
- $-12.45 = -12450 milliunits

The CLI automatically converts between dollars and milliunits:
- **Input**: Use dollars (e.g., `--amount -12.45`)
- **Output**: Human-readable shows dollars, `--json` shows milliunits

## Troubleshooting

### "API token not configured"

Run `ynab login` to set up your credentials, or set the `YNAB_API_TOKEN` environment variable.

### "Budget ID is required"

Specify a budget:
```bash
ynab transactions list --budget <budget-id>
```

Or set a default:
```bash
export YNAB_BUDGET_ID="last-used"
# Or use ynab login
```

### Rate Limiting

YNAB limits to 200 requests per hour. The CLI includes built-in rate limiting (0.5-1.0 seconds between requests).

If you hit the limit:
- Wait an hour
- Reduce request frequency
- Use delta syncing where available

### Common Errors

**404 Not Found**: Budget ID or resource ID is invalid
**401 Unauthorized**: API token is invalid or expired
**403 Forbidden**: Token doesn't have access to that budget

## Development

### Running Tests

```bash
uv sync
uv run pytest
uv run pytest --cov=ynab_cli --cov-report=html
```

### Running Locally

```bash
uv run python -m ynab_cli.cli.main --help
```

## API Documentation

- [YNAB API Docs](https://api.ynab.com/)
- [OpenAPI Spec](https://api.ynab.com/papi/open_api_spec.yaml)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

This project follows TDD (Test-Driven Development) practices.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [httpx](https://www.python-httpx.org/) - HTTP client
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation

Designed for use with [Claude Code](https://claude.ai/claude-code).
