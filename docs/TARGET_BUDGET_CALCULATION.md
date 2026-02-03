# Calculating Target Monthly Budget from Goals

## The Question
"What is my target monthly budget based on my category goals?"

This is NOT what was actually budgeted, but what SHOULD be budgeted based on goal targets.

## Goal Types and Monthly Targets

### MF (Monthly Funding) - Direct Monthly Target
For categories like Groceries with a Monthly Funding goal:
- **Use `goal_target` directly** - this IS the monthly target amount
- Example: Groceries goal_target = 500000 → Target: $500/month

### NEED (Plan Your Spending) - Recurring Expenses
For irregular expenses (quarterly insurance, annual subscriptions):
- The goal spreads the cost across months
- **Use `budgeted + goal_under_funded`** for this month's target
- This represents what should be fully funded this month
- Example: $600 quarterly insurance
  - Month 1: Set aside $200
  - Month 2: Set aside $200
  - Month 3: Set aside $200 (then spend $600)

### TBD (Target Balance by Date) - Savings with Deadline
For savings goals with a target date:
- **Use `budgeted + goal_under_funded`** for this month's contribution
- Or calculate: `goal_overall_left / goal_months_to_budget`
- Example: Save $3,000 for vacation by June (4 months)
  - Monthly target: $3,000 / 4 = $750/month

### TB (Target Category Balance) - One-Time Savings Goal
For emergency fund, large purchases:
- **Use `budgeted + goal_under_funded`** for monthly contribution
- Example: Build $5,000 emergency fund
  - If you want it in 10 months: $500/month
  - YNAB doesn't enforce a timeline, so monthly amount is flexible

### DEBT (Debt Payoff)
For paying down debt by a date:
- **Use `budgeted + goal_under_funded`** for this month's payment
- Example: Pay off $8,000 by December (8 months)
  - Monthly target: $1,000/month

## Universal Formula

For any category with a goal, the **target for this month**:

```
monthly_target = budgeted + goal_under_funded
```

This represents "what this category should have fully funded this month to stay on track."

**But wait** - if you want the "ideal recurring budget" (ignoring what's been budgeted):
- For **MF goals only**: Use `goal_target` (the pure monthly amount)
- For **other goal types**: Use `budgeted + goal_under_funded` (monthly contribution needed)

## API Calls

### Single API Call for Everything

```bash
GET /budgets/{budget_id}/months/current
# or
GET /budgets/last-used/months/current
```

This returns the month with all categories, including:
- `goal_type` - which type of goal
- `goal_target` - the target amount (monthly for MF goals)
- `budgeted` - what's been assigned this month
- `goal_under_funded` - what's still needed this month
- `goal_overall_left` - total remaining to complete goal
- `goal_months_to_budget` - months left in goal period

### Calculation Logic

```python
def get_monthly_target(category):
    """Calculate the target monthly budget for a category."""

    if category['goal_type'] is None:
        # No goal set - could use 'budgeted' as the target or 0
        return category.get('budgeted', 0)

    goal_type = category['goal_type']

    if goal_type == 'MF':  # Monthly Funding
        # This IS the monthly target amount
        return category['goal_target']

    elif goal_type in ['NEED', 'TBD', 'TB', 'DEBT']:
        # Monthly contribution = what should be funded this month
        # This is: what's already budgeted + what's still needed
        return category['budgeted'] + category['goal_under_funded']

    else:
        # Unknown goal type, use budgeted + under_funded
        return category['budgeted'] + category['goal_under_funded']

# Calculate total target monthly budget
total_target_budget = sum(
    get_monthly_target(cat)
    for cat in month['categories']
    if not cat.get('deleted', False)
)
```

## Alternative: Pure Goal Targets Only

If you want ONLY the goal target amounts (for MF goals) and ignore non-monthly goals:

```python
def get_pure_monthly_target(category):
    """Get monthly target only for MF (Monthly Funding) goals."""

    if category['goal_type'] == 'MF':
        return category['goal_target']
    else:
        return 0  # Not a monthly spending goal

total_monthly_spending_target = sum(
    get_pure_monthly_target(cat)
    for cat in month['categories']
    if not cat.get('deleted', False)
)
```

This would give you the sum of all "true monthly budget" goals, excluding savings goals and irregular expenses.

## Example Scenario

Your categories:

| Category | Goal Type | goal_target | budgeted | goal_under_funded | Monthly Target |
|----------|-----------|-------------|----------|-------------------|----------------|
| Groceries | MF | $500 | $600 | $0 | **$500** (goal_target) |
| Rent | MF | $1,500 | $1,500 | $0 | **$1,500** (goal_target) |
| Car Insurance | NEED | $600 (quarterly) | $200 | $0 | **$200** (budgeted + under_funded) |
| Vacation | TBD | $3,000 (4 months) | $700 | $50 | **$750** (budgeted + under_funded) |
| Emergency Fund | TB | $5,000 (total) | $300 | $200 | **$500** (budgeted + under_funded) |

**Total Target Monthly Budget: $3,450**

But if you want ONLY "true monthly expenses" (MF goals only):
- Groceries: $500
- Rent: $1,500
- **Total: $2,000**

## CLI Design

```bash
# Show target monthly budget (based on goals)
ynab budget target
# Output: Target Monthly Budget: $3,450.00
#         Actual Budgeted: $3,300.00
#         Variance: -$150.00 (under-budgeted)

# Show category targets
ynab budget targets
# Output:
#   Category          Type    Target      Actual      Variance
#   Groceries         MF      $500.00     $600.00     +$100.00 (over)
#   Rent              MF      $1,500.00   $1,500.00   $0.00 ✓
#   Car Insurance     NEED    $200.00     $200.00     $0.00 ✓
#   Vacation          TBD     $750.00     $700.00     -$50.00 (under)
#   Emergency Fund    TB      $500.00     $300.00     -$200.00 (under)

# Show only monthly spending targets (MF goals)
ynab budget monthly-targets
# Output: Monthly Spending Budget: $2,000.00
#         (Groceries $500 + Rent $1,500)
```

## Summary

**One API call:** `GET /budgets/last-used/months/current`

**For your "target monthly budget" based on goals:**
1. For MF (Monthly Funding) goals: Use `goal_target`
2. For all other goals: Use `budgeted + goal_under_funded` (monthly contribution)
3. Sum them up

**The key insight:**
- `goal_target` for MF goals = the monthly budget you're aiming for
- `budgeted + goal_under_funded` = what should be funded this month for other goal types
