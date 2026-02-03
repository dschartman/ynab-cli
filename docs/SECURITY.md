# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in ynab-cli, please report it responsibly:

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **schartmand@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Updates**: Regular updates on our progress
- **Timeline**: We aim to address critical issues within 7 days
- **Credit**: You'll be credited in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

### For Users

1. **Protect your API token**
   - Never commit your token to version control
   - Never share your token publicly
   - Revoke and regenerate if exposed
   - Get tokens from: https://app.ynab.com/settings/developer

2. **Configuration security**
   - Config file is automatically set to 600 permissions (user read/write only)
   - Located at `~/.config/ynab/config.toml`
   - Use environment variables for CI/CD: `YNAB_API_TOKEN`

3. **Keep updated**
   - Update to the latest version regularly
   - Check CHANGELOG.md for security fixes

### For Developers

1. **Never hardcode credentials**
   - Use config file or environment variables
   - Test with mock data when possible

2. **Input validation**
   - All user inputs are validated
   - Use type hints and Pydantic for validation

3. **Dependency security**
   - Keep dependencies updated
   - Review security advisories

## Known Security Considerations

### API Token Storage

- Tokens are stored in `~/.config/ynab/config.toml`
- File permissions are set to 600 (user read/write only)
- On shared systems, consider using environment variables instead

### Rate Limiting

- YNAB API has a 200 requests/hour limit
- Built-in rate limiting prevents accidental abuse
- Excessive requests may temporarily lock your account

### HTTPS Only

- All API calls use HTTPS (enforced by httpx)
- Certificate validation is enabled by default

## Disclosure Policy

When a security issue is fixed:
1. We'll release a patch version
2. Publish a security advisory on GitHub
3. Update CHANGELOG.md with details
4. Credit the reporter (with permission)

## Scope

### In Scope
- Authentication bypass
- API token exposure
- Code injection
- Privilege escalation
- Data leakage

### Out of Scope
- YNAB API vulnerabilities (report to YNAB directly)
- Social engineering attacks
- Denial of service (rate limiting is intentional)
- Issues in dependencies (report to upstream)

## Comments

This project interacts with financial data through the YNAB API. We take security seriously and appreciate your help in keeping the project secure.

Thank you for helping make ynab-cli safe for everyone!
