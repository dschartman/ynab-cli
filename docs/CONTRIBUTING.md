# Contributing to ynab-cli

Thank you for your interest in contributing to ynab-cli! This project is designed for programmatic use by Claude Code and automation tools, and we welcome contributions that improve functionality, documentation, or test coverage.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management

### Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/ynab-cli.git
   cd ynab-cli
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Install the CLI locally for testing**
   ```bash
   uv tool install -e .
   ```

4. **Configure your YNAB API credentials**
   ```bash
   ynab login
   ```
   Get your API token from: https://app.ynab.com/settings/developer

## Development Workflow

### Running Tests

This project follows **Test-Driven Development (TDD)** practices:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=ynab_cli --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=ynab_cli --cov-report=html
# Open htmlcov/index.html in your browser
```

**Important**: When adding new features:
1. Write tests FIRST that define the desired behavior
2. Run tests to confirm they fail (red)
3. Write minimal code to make tests pass (green)
4. Refactor for clarity
5. Ensure coverage stays above 90%

### Running the CLI Locally

```bash
# Run directly without installation
uv run python -m ynab_cli.cli.main --help

# Or use the installed version
ynab --help
```

### Code Style

- Use type hints on all functions and methods
- Follow existing code patterns in the project
- Keep functions focused and single-purpose
- Add docstrings to all public functions/classes
- Use descriptive variable names

### Project Structure

```
ynab-cli/
├── src/ynab_cli/
│   ├── api/              # YNAB API client
│   ├── cli/              # Typer-based CLI commands
│   ├── config.py         # Settings management
│   ├── error_handling.py # Exception classes
│   ├── validation.py     # Input validation
│   └── utils.py          # Helper functions
├── tests/                # Test suite (mirrors src/)
├── docs/                 # Documentation
└── CLAUDE.md            # AI-assisted development context
```

## Making Changes

### Before You Start

1. Check existing issues or create a new one to discuss your idea
2. Make sure tests pass: `uv run pytest`
3. Create a feature branch: `git checkout -b feature/your-feature-name`

### While Working

1. **Write tests first** (TDD approach)
2. Make your changes
3. Ensure all tests pass
4. Check test coverage hasn't decreased
5. Update documentation if needed

### Committing Changes

- Write clear, descriptive commit messages
- Reference issue numbers in commits (e.g., "Fix #123: Add category filtering")
- Keep commits focused on a single change

## Pull Request Process

1. **Update documentation**
   - Update README.md if adding new features
   - Add entries to CHANGELOG.md under "Unreleased"
   - Update docstrings and inline comments

2. **Ensure tests pass**
   ```bash
   uv run pytest --cov=ynab_cli
   ```

3. **Create the pull request**
   - Use a clear, descriptive title
   - Reference related issues
   - Describe what changes you made and why
   - Note any breaking changes

4. **Respond to feedback**
   - Address code review comments
   - Make requested changes
   - Keep the conversation respectful and constructive

## Types of Contributions

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)
- Relevant error messages or logs

### Feature Requests

Include:
- Clear description of the feature
- Use case or problem it solves
- Proposed implementation (if you have ideas)
- Consider if it fits the project's "programmatic first" philosophy

### Documentation

- Fix typos or unclear explanations
- Add examples
- Improve API documentation
- Update guides

### Code Contributions

- New CLI commands
- API client improvements
- Better error handling
- Performance improvements
- Test coverage improvements

## API Guidelines

When working with the YNAB API:
- Respect rate limits (200 requests/hour)
- Use the built-in rate limiting decorator
- Handle errors gracefully with user-friendly messages
- Always convert between milliunits and dollars transparently
- Test with the actual YNAB API (not just mocks)

## Questions?

- Open an issue for questions about contributing
- Check existing issues and documentation first
- Be patient and respectful

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something useful together.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ynab-cli! 🎉
