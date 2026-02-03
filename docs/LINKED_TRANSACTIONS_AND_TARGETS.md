# Linked Transactions & Category Targets in YNAB API

## Linked Transactions

The YNAB API has THREE types of "linked" transactions:

### 1. Transfer Transactions

Transfers move money between accounts in your budget. When you create a transfer, YNAB creates TWO linked transactions (one in each account).

**Key Fields:**
- `transfer_account_id`: UUID of the account being transferred to
- `transfer_transaction_id`: UUID of the corresponding transaction on the other side of the transfer
- `payee_id`: Set to the target account's `transfer_payee_id` (each account has a special transfer payee)

**How Transfers Work:**
1. Each account has a `transfer_payee_id` - a special payee representing that account
2. To create a transfer FROM Account A TO Account B:
   - Create a transaction in Account A
   - Set `payee_id` to Account B's `transfer_payee_id`
   - YNAB automatically creates the matching transaction in Account B
   - Both transactions are linked via `transfer_transaction_id`

**Example:**
```json
{
  "transaction": {
    "account_id": "checking-account-uuid",
    "date": "2024-01-15",
    "amount": -50000,  // -$50.00 (leaving checking)
    "payee_id": "savings-account-transfer-payee-uuid",
    "cleared": "cleared"
  }
}
```

This creates:
- Transaction in Checking: -$50.00
- Transaction in Savings: +$50.00 (automatically created)
- Both linked via `transfer_transaction_id`

**Split Transfers:**
Subtransactions can also be transfers using the same pattern:
- `transfer_account_id`: Account being transferred to
- `transfer_transaction_id`: ID of the transaction on the other side

### 2. Matched Transactions

When importing transactions from banks, YNAB can match them against manually entered transactions to prevent duplicates.

**Key Fields:**
- `matched_transaction_id`: UUID of the transaction this was matched with
- `import_id`: String used to prevent duplicates (format: `YNAB:[amount]:[date]:[occurrence]`)

**How Matching Works:**
1. You manually enter a transaction (no `import_id`)
2. Later, you import from your bank
3. YNAB detects a matching transaction (same amount, date, similar details)
4. Instead of creating a duplicate, YNAB "matches" them
5. The original transaction gets `matched_transaction_id` set

**Use Case:**
- Enter a transaction on your phone at the store
- Import from bank later
- YNAB recognizes it's the same transaction and links them

### 3. Direct Import Linked Accounts

Accounts can be linked to financial institutions for automatic transaction import.

**Key Fields (on Account):**
- `direct_import_linked`: Boolean - true if account is linked to a bank
- `direct_import_in_error`: Boolean - true if the bank connection is having issues

**Import Endpoint:**
```
POST /budgets/{budget_id}/transactions/import
```

This triggers import from all linked accounts. Equivalent to clicking "Import" in the web app.

**Import Process:**
1. Link your account to a financial institution (done in web/mobile app)
2. Call the import endpoint to fetch new transactions
3. Transactions are imported with `import_id` to prevent duplicates
4. YNAB may match them with manually entered transactions

---

## Category Targets (Goals)

Categories can have goals/targets to help you plan your spending and saving. This is a sophisticated system with multiple goal types and tracking fields.

### Goal Types

| Code | Name | Description |
|------|------|-------------|
| `TB` | Target Category Balance | Save up to a specific amount |
| `TBD` | Target Category Balance by Date | Save a specific amount by a target date |
| `MF` | Monthly Funding | Budget a specific amount every month |
| `NEED` | Plan Your Spending | Budget for irregular expenses |
| `DEBT` | Debt Payoff | Pay down debt by a target date |

### Goal Configuration Fields

**Basic Goal Setup:**
- `goal_type`: One of the types above (TB, TBD, MF, NEED, DEBT)
- `goal_target`: Target amount in milliunits (e.g., 500000 = $500.00)
- `goal_creation_month`: ISO date when goal was created

**Target Date (for TBD and DEBT):**
- `goal_target_month`: ISO date - when to complete the goal

**Recurring Goals (for MF and NEED):**
- `goal_cadence`: Integer 0-14 specifying how often the goal repeats
  - `0` = None
  - `1` = Monthly
  - `2` = Weekly
  - `13` = Yearly
  - `3-12` = Every 2-11 months
  - `14` = Every 2 years
- `goal_cadence_frequency`: Multiplier for cadence
  - Example: cadence=1, frequency=2 = every OTHER month
  - Only used when cadence is 0, 1, 2, or 13
- `goal_day`: Integer - day offset for due date
  - For weekly (cadence=2): 0=Sunday, 6=Saturday
  - For monthly: 1=1st day, 31=31st day, null=last day of month

**NEED Goal Behavior:**
- `goal_needs_whole_amount`: Boolean
  - `true` = "Set Aside" - always ask for full target amount
  - `false` = "Refill" - use previous month's funding, only ask for difference
  - `null` for other goal types

### Goal Progress Tracking Fields

**Overall Progress:**
- `goal_percentage_complete`: Integer 0-100
- `goal_overall_funded`: Milliunits - total amount funded towards goal
- `goal_overall_left`: Milliunits - amount still needed to complete goal

**Monthly Progress:**
- `goal_months_to_budget`: Integer - months left in current goal period (including current month)
- `goal_under_funded`: Milliunits - amount needed THIS MONTH to stay on track
  - Corresponds to "Underfunded" in web/mobile clients
  - Special handling for NEED goals in future months

**Snoozing:**
- `goal_snoozed_at`: ISO datetime - when goal was snoozed, or null if not snoozed

### Updating Goal Targets

You can update the `goal_target` amount for a category that already has a goal:

```
PATCH /budgets/{budget_id}/categories/{category_id}
```

**Important:** You can only change `goal_target` if the category already has a goal (`goal_type != null`). Setting up a NEW goal requires using the web/mobile app.

### Example Goal Scenarios

**1. Emergency Fund (TB - Target Category Balance)**
```json
{
  "goal_type": "TB",
  "goal_target": 5000000,  // $5,000
  "goal_percentage_complete": 45,
  "goal_overall_funded": 2250000,  // $2,250
  "goal_overall_left": 2750000     // $2,750 remaining
}
```

**2. Vacation Fund (TBD - Target Balance by Date)**
```json
{
  "goal_type": "TBD",
  "goal_target": 3000000,  // $3,000
  "goal_target_month": "2024-06-01",
  "goal_months_to_budget": 4,
  "goal_under_funded": 750000  // Need $750 this month to stay on track
}
```

**3. Rent (MF - Monthly Funding)**
```json
{
  "goal_type": "MF",
  "goal_target": 1500000,  // $1,500/month
  "goal_cadence": 1,  // Monthly
  "goal_day": 1       // Due on the 1st
}
```

**4. Quarterly Insurance (NEED - Plan Your Spending)**
```json
{
  "goal_type": "NEED",
  "goal_target": 600000,  // $600
  "goal_cadence": 4,      // Every 3 months
  "goal_day": 15,         // Due on the 15th
  "goal_needs_whole_amount": true  // "Set Aside" behavior
}
```

**5. Credit Card Debt (DEBT)**
```json
{
  "goal_type": "DEBT",
  "goal_target": 8000000,  // $8,000 total debt
  "goal_target_month": "2024-12-01",
  "goal_percentage_complete": 25,
  "goal_overall_funded": 2000000,  // $2,000 paid so far
  "goal_overall_left": 6000000     // $6,000 remaining
}
```

---

## CLI Design Implications

### For Transfer Transactions

**CLI should make transfers easy:**
```bash
# Simple transfer command
ynab transfer --from checking --to savings --amount 50.00

# Under the hood:
# 1. Get savings account's transfer_payee_id
# 2. Create transaction in checking with that payee_id
# 3. YNAB creates matching transaction automatically

# List transfers
ynab transactions list --transfers-only

# Show linked transfer details
ynab transaction get {id} --show-transfer-link
```

### For Import/Matching

**CLI should support import workflows:**
```bash
# Trigger import from linked accounts
ynab import

# Show import status
ynab accounts list --show-import-status

# List matched transactions
ynab transactions list --matched-only

# Show what a transaction was matched with
ynab transaction get {id} --show-match
```

### For Category Goals

**CLI should display and manage goals:**
```bash
# List categories with their goals
ynab categories list --show-goals

# Show goal progress
ynab category goal-status "Emergency Fund"
# Output:
#   Goal Type: Target Category Balance
#   Target: $5,000.00
#   Funded: $2,250.00 (45%)
#   Remaining: $2,750.00

# Update goal target amount (for existing goals only)
ynab category update-goal "Emergency Fund" --target 6000.00

# Show underfunded categories
ynab budget status --underfunded
# Output:
#   Vacation Fund: Need $750.00 this month to stay on track
#   Car Repairs: Need $125.00 this month

# Show all goal progress
ynab goals progress
```

---

## Key Takeaways

### Transfers
- Transfers are TWO linked transactions
- Use account's `transfer_payee_id` to create transfers
- Both transactions have `transfer_transaction_id` pointing to each other
- Subtransactions can also be transfers

### Matched Transactions
- Prevents duplicates when importing from banks
- Manual transactions can be matched with imported ones
- Use `import_id` format to prevent duplicates: `YNAB:[amount]:[date]:[occurrence]`

### Direct Import
- Accounts can be linked to banks
- Import endpoint triggers fetch from all linked accounts
- Check `direct_import_in_error` for connection issues

### Goals
- 5 goal types: TB, TBD, MF, NEED, DEBT
- Rich progress tracking with multiple fields
- Complex cadence system for recurring goals
- Can only UPDATE `goal_target` via API (must create goals in web/mobile)
- Critical for budget planning and tracking

### For Claude Code
Goals are especially important for programmatic budget analysis:
- "How much do I need to budget this month?" → Check `goal_under_funded`
- "Am I on track for my savings goals?" → Check `goal_percentage_complete`
- "Which goals am I behind on?" → Filter by `goal_under_funded > 0`
