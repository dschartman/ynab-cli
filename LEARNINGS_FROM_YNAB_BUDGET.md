# Learnings from ynab-budget Project

## Overview

The `ynab-budget` project at `../ynab-budget/` is a mature implementation with valuable patterns and code we should leverage for `ynab-cli`.

## Key Strengths to Adopt

### 1. **API Client Implementation** ✅ REUSABLE

**Location:** `src/ynab_budget/api/client.py`

**Features:**
- Async HTTP client using `httpx`
- Built-in rate limiting (0.5s between calls)
- Clean async context manager pattern
- Proper error handling with `raise_for_status()`
- Rate limit decorator to prevent API abuse (200 req/hour limit)

**Example:**
```python
class YNABClient:
    def __init__(self, api_token, budget_id):
        self.client = httpx.AsyncClient(
            base_url="https://api.ynab.com/v1",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    @rate_limit(0.5)
    async def get_transactions(self, ...):
        response = await self.client.get(f"/budgets/{bid}/transactions", ...)
        response.raise_for_status()
        return response.json()
```

**Why it's good:**
- Respects YNAB's 200 req/hour limit
- Clean separation of concerns
- Easy to test
- Works well with async/await

### 2. **Configuration Management** ✅ REUSABLE

**Location:** `src/ynab_budget/config.py`

**Features:**
- Pydantic Settings for type-safe config
- Automatic `.env` file loading
- Sensible defaults
- Validation built-in

**Example:**
```python
class Settings(BaseSettings):
    ynab_api_token: str = Field(..., description="Your YNAB API token")
    current_budget_id: str = Field(..., description="Default budget ID")
    base_url: str = Field(default="https://api.ynab.com/v1")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
```

**Why it's good:**
- Type safety
- Clear error messages when config missing
- Easy to extend
- Standard .env pattern

### 3. **CLI Structure with Click** ✅ REUSABLE

**Location:** `src/ynab_budget/cli/main.py`

**Features:**
- Click-based command groups
- Async command support
- Clear output formatting
- Proper error handling

**Example:**
```python
@click.group()
def cli():
    """YNAB Budget Management."""
    pass

@cli.command()
@click.option('--full', is_flag=True)
def sync(full):
    """Sync data from YNAB."""
    async def do_sync():
        db = DatabaseSync()
        result = await db.sync_from_api(full_sync=full)
    asyncio.run(do_sync())
```

**Why it's good:**
- Clean command structure
- Easy to add new commands
- Good UX with emojis and formatting
- Wraps async in sync for CLI

### 4. **Database Schema for Caching** ⚠️ OPTIONAL (But Valuable)

**Location:** `src/ynab_budget/database/schema.sql`

**Features:**
- SQLite for local caching
- Incremental sync support (delta syncing)
- Separate tables for analysis vs YNAB data
- Server knowledge tracking

**Why it's valuable:**
- Reduces API calls (respects rate limits)
- Enables offline analysis
- Historical data for trends
- Fast queries for Claude Code

**Why it's optional for CLI:**
- Adds complexity
- CLI might not need caching (direct API calls work)
- But very useful for power features

### 5. **Real-World Workflows** ✅ LEARN FROM

**Documented workflows:**
- Transaction review and categorization
- Budget status checking
- Paycheck analysis
- Tax withholding tracking

**Key insights:**
- Users need to review unapproved transactions regularly
- Budget variance analysis (target vs actual)
- Historical trend analysis
- Categorization suggestions

## What to Bring to ynab-cli

### Phase 1: Core CLI (Required)

1. **API Client** - Copy and adapt `client.py`
   - Already implements all endpoints
   - Rate limiting built-in
   - Async/await pattern

2. **Config Management** - Copy `config.py`
   - Pydantic Settings
   - .env support
   - Type safety

3. **CLI Framework** - Copy structure from `main.py`
   - Click-based
   - Command groups (budgets, accounts, transactions, etc.)
   - JSON output flag on all commands

4. **Project Structure** - Same layout
   ```
   src/ynab_cli/
   ├── api/          # API client
   ├── cli/          # Click commands
   ├── config.py     # Settings
   └── __init__.py
   ```

### Phase 2: Enhanced Features (Optional)

1. **Database Layer** - Consider adding later
   - Caching for performance
   - Delta syncing
   - Historical analysis
   - Worth it if users need trends/reports

2. **Analysis Modules** - Transaction categorization, budget analysis
   - Useful for power users
   - Claude Code can analyze directly
   - Maybe not needed in CLI itself

### Phase 3: Advanced Features (Future)

1. **Financial Planning** - Goals, scenarios, runway
2. **Smart Categorization** - ML-based suggestions
3. **Budget Templates** - Import/export budget structures

## Key Design Patterns to Follow

### 1. Async API Client
```python
async with YNABClient() as client:
    transactions = await client.get_transactions()
```

### 2. CLI Wraps Async
```python
@cli.command()
def some_command():
    async def do_work():
        async with YNABClient() as client:
            return await client.get_transactions()
    result = asyncio.run(do_work())
    click.echo(json.dumps(result))
```

### 3. JSON Output for Claude Code
```python
@cli.command()
@click.option('--json', is_flag=True, help='Output as JSON')
def list_accounts(json_output):
    accounts = get_accounts()
    if json_output:
        click.echo(json.dumps(accounts))
    else:
        # Human-readable table
        for account in accounts:
            click.echo(f"{account['name']}: ${account['balance']}")
```

### 4. Environment Config
```bash
# .env
YNAB_API_TOKEN=your_token_here
YNAB_BUDGET_ID=last-used
```

```python
# Automatic loading
settings = Settings()  # Reads from .env
```

## Differences from ynab-budget

### ynab-budget Focus:
- **Personal budget management** for a specific user
- **Database-backed** with caching
- **Claude Code conversations** as primary interface
- **Transaction review** workflow
- **Financial planning** and analysis

### ynab-cli Focus:
- **General-purpose CLI tool** for any YNAB user
- **Direct API calls** without required database
- **CLI commands** as primary interface
- **Full API coverage** for all endpoints
- **Claude Code as a user** (not just conversation tool)

## Files Worth Copying

### Copy Directly (with minor adaptations):
1. `src/ynab_budget/api/client.py` → Our API client foundation
2. `src/ynab_budget/config.py` → Our config management
3. `pyproject.toml` → Dependencies and structure
4. `.env.example` → User setup template

### Learn From (don't copy wholesale):
1. `src/ynab_budget/cli/main.py` → CLI command patterns
2. `src/ynab_budget/database/sync.py` → Delta sync implementation (if we add caching)
3. `docs/` → Workflow documentation for README

### Skip (ynab-budget specific):
1. Analysis modules (transaction review, categorization)
2. Personal financial planning docs
3. Database schema (unless we add caching later)

## Implementation Strategy

### Step 1: Bootstrap Project (Today)
```bash
cd /Users/don/Repos/ynab-cli

# Copy project structure
cp ../ynab-budget/pyproject.toml .
# Edit: change name to ynab-cli, update description

# Copy API client
mkdir -p src/ynab_cli/api
cp ../ynab-budget/src/ynab_budget/api/client.py src/ynab_cli/api/
cp ../ynab-budget/src/ynab_budget/config.py src/ynab_cli/

# Copy config template
cp ../ynab-budget/.env.example .
```

### Step 2: Build CLI Commands (Next)
```bash
# Create CLI structure
mkdir -p src/ynab_cli/cli
# Build command groups: budgets, accounts, categories, transactions, etc.
```

### Step 3: Test & Document (Then)
```bash
# Add tests
# Write README
# Create examples
```

## Key Takeaways

1. **Don't reinvent the wheel** - The API client, config, and CLI structure are already proven
2. **Start simple** - Direct API calls, no database (can add later)
3. **Design for Claude Code** - JSON output, clear commands, good error messages
4. **Respect rate limits** - Built-in rate limiting is essential
5. **Use modern Python** - Async/await, Pydantic, Click, httpx

## Next Steps

1. Copy foundational code from ynab-budget
2. Adapt for general CLI use (not personal budget management)
3. Build out command structure for all API endpoints
4. Add comprehensive tests
5. Document for Claude Code usage
6. Consider adding database layer later if needed

---

**Bottom Line:** The ynab-budget project is a goldmine. We should absolutely reuse the API client, config management, and CLI patterns. This will save days of work and give us a proven foundation.
