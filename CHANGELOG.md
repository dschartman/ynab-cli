# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-02

### Added
- Initial release of ynab-cli
- Full YNAB API coverage for budgets, accounts, categories, transactions, and months
- `ynab login` command for credential management
- JSON output support on all commands via `--json` flag
- Automatic milliunit ↔ dollar conversion
- `ynab transactions transfer` helper for account transfers
- Built-in rate limiting (respects YNAB's 200 req/hour limit)
- Comprehensive error handling with user-friendly messages
- Debug mode with `--debug` flag for detailed error traces
- Verbose logging with `--verbose` flag for API request/response tracking
- Configuration file at `~/.config/ynab/config.toml` with secure permissions (600)
- Environment variable support (YNAB_API_TOKEN, YNAB_BUDGET_ID)
- Complete test suite with >90% coverage
- Comprehensive documentation and API analysis

### Commands
- `ynab login` - Configure API credentials
- `ynab budgets list` - List all budgets
- `ynab budgets get` - Get budget details
- `ynab budgets settings` - Get budget settings
- `ynab accounts list` - List accounts
- `ynab accounts get` - Get account details
- `ynab categories list` - List categories
- `ynab categories get` - Get category details
- `ynab transactions list` - List transactions (with filters)
- `ynab transactions create` - Create transaction
- `ynab transactions update` - Update transaction
- `ynab transactions delete` - Delete transaction
- `ynab transactions transfer` - Transfer between accounts
- `ynab months get` - Get month budget data

[0.1.0]: https://github.com/dschartman/ynab-cli/releases/tag/v0.1.0
