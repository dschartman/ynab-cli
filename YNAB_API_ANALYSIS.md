# YNAB API Analysis & CLI Design Reference

## API Overview

- **Version**: 1.77.0
- **Base URL**: `https://api.ynab.com/v1`
- **Protocol**: REST with JSON over HTTPS
- **Authentication**: Bearer token (Personal Access Token or OAuth)
- **Rate Limit**: 200 requests per hour per access token (rolling window)

## Authentication Methods

### Personal Access Tokens (Recommended for CLI)
- Generated from Account Settings → Developer Settings
- Non-expiring tokens
- Simple bearer token authentication
- Perfect for CLI tools and automation

### OAuth (For Multi-User Apps)
- Implicit Grant: 2-hour expiring tokens
- Authorization Code Grant: Supports refresh tokens
- Not needed for CLI tool designed for personal use

## Core Concepts

### 1. Milliunits
All monetary amounts are in "milliunits" where 1000 = one unit of currency
- $1.00 = 1000
- $-12.45 = -12450
- €50.99 = 50990

### 2. Delta Syncing (Server Knowledge)
Critical for efficiency:
- Each response includes `server_knowledge` integer
- Pass as `last_knowledge_of_server` query param on next request
- Returns only entities changed since that point
- Supported on: budgets, accounts, categories, transactions, payees, payee_locations

### 3. Import IDs
Prevent duplicate transactions:
- Format: `YNAB:[amount in milliunits]:[ISO date]:[occurrence number]`
- Example: `YNAB:-1230:2024-01-15:1` for -$1.23 on 2024-01-15 (first occurrence)
- If duplicate import_id, returns 409 conflict

### 4. Budget ID Shortcuts
- `"last-used"` - Most recently used budget
- `"default"` - User's default budget
- Actual UUID also accepted

### 5. Cleared Status
- `"cleared"` - Transaction has cleared the bank
- `"uncleared"` - Pending transaction
- `"reconciled"` - Manually reconciled in YNAB

### 6. Flag Colors
- Enum: `"red"`, `"orange"`, `"yellow"`, `"green"`, `"blue"`, `"purple"`, `null`

### 7. Account Types
Supported types:
- Checking, Savings, Cash
- Credit Card, Line of Credit
- Other Asset, Other Liability
- Mortgage, Auto Loan, Student Loan, Personal Loan, Medical Debt, Other Debt

## API Resources & Endpoints

### User
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/user` | GET | Get authenticated user info |

### Budgets
| Endpoint | Method | Description | Notes |
|----------|--------|-------------|-------|
| `/budgets` | GET | List all budgets | Optional `include_accounts` param |
| `/budgets/{budget_id}` | GET | Full budget export | All related entities included |
| `/budgets/{budget_id}/settings` | GET | Budget settings | Date/currency formats |

### Accounts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/budgets/{budget_id}/accounts` | GET | List all accounts |
| `/budgets/{budget_id}/accounts` | POST | Create account |
| `/budgets/{budget_id}/accounts/{account_id}` | GET | Single account |

### Categories
| Endpoint | Method | Description | Notes |
|----------|--------|-------------|-------|
| `/budgets/{budget_id}/categories` | GET | List categories | Grouped by category group |
| `/budgets/{budget_id}/categories/{category_id}` | GET | Single category | Current month amounts |
| `/budgets/{budget_id}/categories/{category_id}` | PATCH | Update category | Name, note, etc. |
| `/budgets/{budget_id}/months/{month}/categories/{category_id}` | GET | Category for specific month | |
| `/budgets/{budget_id}/months/{month}/categories/{category_id}` | PATCH | Update budgeted amount | Month-specific |

**Note**: Amounts are specific to current budget month (UTC) unless month specified

### Payees
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/budgets/{budget_id}/payees` | GET | List all payees |
| `/budgets/{budget_id}/payees/{payee_id}` | GET | Single payee |
| `/budgets/{budget_id}/payees/{payee_id}` | PATCH | Update payee name |

### Payee Locations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/budgets/{budget_id}/payee_locations` | GET | All payee locations |
| `/budgets/{budget_id}/payee_locations/{payee_location_id}` | GET | Single location |
| `/budgets/{budget_id}/payees/{payee_id}/payee_locations` | GET | Locations for payee |

**Purpose**: GPS coordinates for mobile app location-based payee suggestions

### Months
| Endpoint | Method | Description | Notes |
|----------|--------|-------------|-------|
| `/budgets/{budget_id}/months` | GET | List budget months | Ready to Assign, Age of Money |
| `/budgets/{budget_id}/months/{month}` | GET | Single month | Use "current" or ISO date |

**Format**: ISO date (YYYY-MM-DD) or keyword "current"

### Transactions
| Endpoint | Method | Description | Notes |
|----------|--------|-------------|-------|
| `/budgets/{budget_id}/transactions` | GET | List transactions | Excludes scheduled (future dated) |
| `/budgets/{budget_id}/transactions` | POST | Create transaction(s) | Single or bulk |
| `/budgets/{budget_id}/transactions` | PATCH | Update multiple | By ID or import_id |
| `/budgets/{budget_id}/transactions/{transaction_id}` | GET | Single transaction | |
| `/budgets/{budget_id}/transactions/{transaction_id}` | PUT | Update transaction | |
| `/budgets/{budget_id}/transactions/{transaction_id}` | DELETE | Delete transaction | |
| `/budgets/{budget_id}/transactions/import` | POST | Import from linked accounts | |
| `/budgets/{budget_id}/accounts/{account_id}/transactions` | GET | Account transactions | |
| `/budgets/{budget_id}/categories/{category_id}/transactions` | GET | Category transactions | |
| `/budgets/{budget_id}/payees/{payee_id}/transactions` | GET | Payee transactions | |
| `/budgets/{budget_id}/months/{month}/transactions` | GET | Month transactions | |

**Query Parameters**:
- `since_date`: ISO format (YYYY-MM-DD)
- `type`: Filter by `uncategorized` or `unapproved`
- `last_knowledge_of_server`: Delta sync

**Split Transactions**: Use `subtransactions` array instead of single `category_id`

**Transfers**: Use `transfer_payee_id` from target account

### Scheduled Transactions
| Endpoint | Method | Description | Notes |
|----------|--------|-------------|-------|
| `/budgets/{budget_id}/scheduled_transactions` | GET | List scheduled | Future-dated transactions |
| `/budgets/{budget_id}/scheduled_transactions` | POST | Create scheduled | |
| `/budgets/{budget_id}/scheduled_transactions/{id}` | GET | Single scheduled | |
| `/budgets/{budget_id}/scheduled_transactions/{id}` | PUT | Update scheduled | |
| `/budgets/{budget_id}/scheduled_transactions/{id}` | DELETE | Delete scheduled | |

**Important**: Cannot create scheduled transactions on regular transaction endpoint

## Request/Response Patterns

### Request Wrapper
```json
{
  "resource_name": {
    "property": "value"
  }
}
```

### Response Wrapper
```json
{
  "data": {
    "resource": {...},
    "server_knowledge": 12345
  }
}
```

### Error Response
```json
{
  "error": {
    "id": "unique-error-id",
    "name": "error_type",
    "detail": "Human readable message"
  }
}
```

### HTTP Status Codes
- **200**: Success (GET, PATCH)
- **201**: Created (POST)
- **209**: Multi-resource update success
- **400**: Validation error
- **404**: Resource not found
- **409**: Conflict (duplicate import_id)
- **429**: Rate limit exceeded (implied)

## Best Practices from YNAB

1. **Use Delta Syncing**: Track `server_knowledge` and pass `last_knowledge_of_server` on subsequent requests
2. **Implement Caching**: Store data locally to reduce API calls
3. **Request Only What You Need**: Use specific endpoints rather than full budget exports
4. **Handle Rate Limits**: 200 requests/hour - implement backoff
5. **Use Import IDs**: Prevent duplicate transactions when importing
6. **Build Fault Tolerance**: Handle errors gracefully with retries
7. **Follow Transfer Patterns**: Use `transfer_payee_id` for proper transfer handling
8. **Respect Date Constraints**: Future-dated transactions must use scheduled endpoint

## CLI Design Considerations

### For Claude Code Usability

1. **Structured Output**
   - Default to JSON output for easy parsing
   - Optional table/human-readable formats
   - Include `--json` flag on all commands

2. **Authentication**
   - Environment variable: `YNAB_API_TOKEN`
   - Config file: `~/.ynab/config`
   - Command line: `--token` flag
   - Priority order: CLI flag > ENV var > config file

3. **Budget Selection**
   - Environment variable: `YNAB_BUDGET_ID`
   - Support shortcuts: "last-used", "default"
   - `--budget` flag on all commands

4. **Command Structure**
   - Resource-based: `ynab budgets list`, `ynab transactions create`
   - Clear CRUD operations: list, get, create, update, delete
   - Aliases for common operations

5. **Delta Syncing Support**
   - Store server_knowledge in local cache
   - `--full-sync` flag to force complete refresh
   - Automatic incremental sync by default

6. **Error Handling**
   - Clear error messages with actionable advice
   - Exit codes: 0 (success), 1 (user error), 2 (API error), 3 (auth error)
   - Verbose mode: `--verbose` or `-v`

7. **Amount Handling**
   - Accept human-readable amounts: `12.45`, `-$50.99`
   - Auto-convert to milliunits internally
   - Display as currency in human output

8. **Date Handling**
   - Accept multiple formats: ISO, relative ("today", "yesterday", "last week")
   - Always convert to ISO for API

9. **Batch Operations**
   - Support bulk transaction creation from CSV/JSON
   - Bulk updates with import_id matching
   - Progress indicators for long operations

10. **Common Workflows**
    - Quick add transaction: `ynab tx add -a -12.45 -p "Starbucks" -c "Dining Out"`
    - Recent transactions: `ynab tx list --since="1 week ago"`
    - Budget status: `ynab budget status` (categories with amounts)
    - Account balance: `ynab accounts balance`

## Resource Hierarchy

```
User
└── Budgets
    ├── Settings
    ├── Accounts
    │   └── Transactions
    ├── Categories
    │   └── Transactions
    ├── Payees
    │   ├── Transactions
    │   └── Payee Locations
    ├── Months
    │   ├── Categories
    │   └── Transactions
    ├── Transactions
    └── Scheduled Transactions
```

## Key Fields Reference

### Transaction Fields
- `id`: UUID
- `date`: ISO 8601 (YYYY-MM-DD)
- `amount`: Integer milliunits
- `memo`: String (optional)
- `cleared`: Enum (cleared/uncleared/reconciled)
- `approved`: Boolean
- `flag_color`: Enum or null
- `account_id`: UUID
- `payee_id`: UUID (optional)
- `category_id`: UUID (optional, null for split)
- `transfer_account_id`: UUID (for transfers)
- `transfer_transaction_id`: UUID (for transfers)
- `matched_transaction_id`: UUID (for imports)
- `import_id`: String (optional, for deduplication)
- `deleted`: Boolean
- `account_name`: String (read-only)
- `payee_name`: String (read-only)
- `category_name`: String (read-only)
- `subtransactions`: Array (for splits)

### Account Fields
- `id`: UUID
- `name`: String
- `type`: Enum (account types)
- `on_budget`: Boolean
- `closed`: Boolean
- `note`: String
- `balance`: Integer milliunits
- `cleared_balance`: Integer milliunits
- `uncleared_balance`: Integer milliunits
- `transfer_payee_id`: UUID
- `deleted`: Boolean

### Category Fields
- `id`: UUID
- `category_group_id`: UUID
- `category_group_name`: String
- `name`: String
- `hidden`: Boolean
- `note`: String
- `budgeted`: Integer milliunits (month-specific)
- `activity`: Integer milliunits (month-specific)
- `balance`: Integer milliunits (month-specific)
- `deleted`: Boolean

## Implementation Priority

### Phase 1: Core Functionality
1. Authentication setup
2. Budget listing and selection
3. Account listing and balances
4. Transaction listing (basic)
5. Transaction creation (simple)

### Phase 2: Essential Features
1. Category listing and budgeted amounts
2. Payee listing
3. Transaction filtering (date, payee, category)
4. Transaction updates and deletion
5. Human-readable output formats

### Phase 3: Advanced Features
1. Delta syncing with local cache
2. Split transaction support
3. Transfer handling
4. Scheduled transactions
5. Bulk operations (CSV import/export)

### Phase 4: Power Features
1. Month/budget analysis
2. Reporting and summaries
3. Category budget updates
4. Account creation
5. Import from bank files

## OpenAPI Spec Location
Local: `./openapi_spec.yaml` (3,430 lines)
Remote: `https://api.ynab.com/papi/open_api_spec.yaml`

## Sources
- [YNAB API](https://api.ynab.com/)
- [YNAB API Documentation](https://publicapi.dev/ynab-api)
- [The YNAB API](https://support.ynab.com/en_us/the-ynab-api-an-overview-BJMgQ3zAq)
- [YNAB API Endpoints | New Year's Wellness](https://www.postman.com/devrel/workspace/new-year-s-wellness/documentation/14272639-794bcf59-0677-42bd-8caa-b592996cc9bb)
- [GitHub - dmlerner/ynab-api: Generated Python API for YNAB](https://github.com/dmlerner/ynab-api)
- [ynab v1.0.0 — Documentation](https://hexdocs.pm/ynab/)
- [Ynab OpenAPI Spec](https://api.ynab.com/papi/open_api_spec.yaml)
- [How we use OpenAPI / Swagger for the YNAB API - DEV Community](https://dev.to/ynab/how-we-use-openapi-swagger-for-the-ynab-api-5453)
