# QuickBooks Financial Data Analysis for Small Service Businesses

## When to Use

When the user can provide an actual financial data export (QuickBooks, bank statements, Stripe, etc.) instead of just answering qualitative questions about the business. This replaces/augments Step 2 (Business Model Discovery) with hard numbers. The analysis surfaces concrete cost-cutting opportunities, money-losing jobs, and structural issues that inform the agent design (e.g., minimum job size enforcement, travel surcharge calculation, pricing model validation).

## QuickBooks CSV Parsing

QuickBooks "Transaction List by Date" exports have a specific structure that breaks naive CSV parsing:

```
Row 1: Company Name (e.g., "a service business")
Row 2: Report title ("Transaction List by Date")
Row 3: Date range (e.g., "January 1, 2024-June 23, 2026")
Row 4: (blank)
Row 5: Headers: Date, Transaction type, Num, Posting (Y/N), Name, Memo, Account name, Split, Amount
Row 6+: Data rows
...
Row N-5: TOTAL row — Amount column contains "$1,543,669.53" (with $ sign!)
Row N-4: (blank)
Row N-3: (blank)
Row N-2: (blank)
Row N-1: Timestamp (e.g., "Tuesday, June 23, 2026 02:22 PM GMTZ")
Row N: (blank)
```

### Working Parse Pattern (Python + pandas)

```python
import pandas as pd

df = pd.read_csv(CSV_PATH, skiprows=4, skipfooter=6, engine='python', on_bad_lines='skip')
df.columns = df.columns.str.strip()

# Drop rows where Date isn't parseable (catches stray TOTAL/footer rows)
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
df = df[df['Date'].notna()].copy()

# Amount column may contain $ signs and commas from the TOTAL row
df['Amount'] = (df['Amount'].astype(str)
    .str.replace('$', '').str.replace(',', '')
    .str.replace('"', '').str.strip().astype(float))

df['YearMonth'] = df['Date'].dt.to_period('M')
df['Year'] = df['Date'].dt.year

for col in ['Transaction type', 'Name', 'Memo', 'Account name', 'Split']:
    df[col] = df[col].fillna('').astype(str).str.strip()
```

**Key pitfalls:**
- `skipfooter=4` is NOT enough — the TOTAL row + blank rows + timestamp + trailing blank = 6 footer rows
- The TOTAL row's Amount value starts with `$` which breaks `.astype(float)` if not stripped
- Use `on_bad_lines='skip'` because QuickBooks sometimes has rows with unescaped commas in Memo fields
- Always validate by checking row count against the report's stated total

## Transaction Type Taxonomy

QuickBooks transaction types you'll encounter:

| Type | What it is | Signed? |
|---|---|---|
| `Invoice` | Revenue — billed to customer | Positive (income) |
| `Payment` | Revenue — collected from customer | Positive (income) |
| `Estimate` | Quote sent, NOT posted (Posting = N) | Positive but NOT real revenue |
| `Bill` | Expense — vendor invoice entered | Positive (expense amount) |
| `Bill Payment (Check)` | AP payment — transfer, NOT a real expense | Negative (cash out) |
| `Expense` | Expense — credit card/bank charge | May be negative (bank account) or positive (credit card) |
| `Credit Card Payment` | Transfer between accounts | NOT a real expense |
| `Credit Card Credit` | Refund to credit card | NOT a real expense |
| `Deposit` | Owner investment or other | NOT revenue |
| `Check` | Manual check payment | May be expense |
| `Credit Memo` | Refund to customer | Reduces revenue |

## Separating Real Expenses from Internal Transfers

The `Split` column in QuickBooks is the key to filtering. Internal transfers use these split values — exclude them:

```python
non_expense_splits = [
    'Accounts Payable (A/P)',
    'Accounts Receivable (A/R)',
    "Owner's Investment",
    'Chase Business Ink',      # credit card account name
    'LMCU 6952',               # bank account name
    'Undeposited Funds',
    ''                         # blank = transfer
]
real_expenses = all_expenses[~all_expenses['Split'].isin(non_expense_splits)]
```

Use absolute values for expense amounts since Bills post positive and Expense transactions may post negative depending on the account.

## Analysis Framework

### 1. Revenue Analysis
- Total invoiced vs total collected (collection rate)
- Outstanding AR
- Average invoice size
- Top 20 customers (concentration risk — any customer >20% is a risk)
- Monthly invoiced trend
- Estimate count and conversion rate (invoices/estimates)

### 2. Expense Analysis by Category
- Group by `Split` column (QuickBooks expense category)
- Sort descending, show % of total
- Flag `Uncategorized Expense` — means bookkeeping is sloppy, needs cleanup
- Look for categories that seem too high for a service business (e.g., bank fees >3% of revenue)

### 3. P&L and Cumulative Loss
- Yearly revenue vs expenses vs net income
- Monthly net income (revenue - expenses)
- Cumulative running total — shows whether the business has EVER been profitable
- If cumulative is always negative, the business is funded by owner investment

### 4. Travel Cost Attribution (Service Business Specific)

For field service businesses, travel costs (fuel + meals) can make small jobs unprofitable:

```python
travel_cats = ['Meals & Entertainment', 'Car & Truck']
travel_exp = real_expenses[real_expenses['Split'].isin(travel_cats)]

for _, inv in invoices.iterrows():
    window = travel_exp[
        (travel_exp['Date'] >= inv['Date'] - pd.Timedelta(days=2)) &
        (travel_exp['Date'] <= inv['Date'] + pd.Timedelta(days=2))
    ]
    travel_cost = window['abs_amt'].sum()
    travel_pct = travel_cost / inv['Amount'] * 100
```

- Flag jobs where travel > 20% of invoice (questionable)
- Flag jobs where travel > 100% of invoice (definite loss)
- This directly informs minimum job size and travel surcharge pricing

### 5. Seasonality
- Average revenue and expenses by calendar month across all years
- Identify peak months, dead months
- Critical for marketing timing — spend when conversion is highest
- For Florida service businesses: snowbird season (Oct-Nov) is typically peak

### 6. Anomaly Detection
- Top 15 largest single expenses
- Recurring charges (same vendor + same amount, 3+ times) — subscriptions, retainers
- Bank fees broken down by vendor — $700+/month in bank fees is a leak
- Car maintenance total vs expected — 300+ transactions in "maintenance" likely miscategorized

### 7. Car & Truck Deep Dive
Split into sub-categories:
- **Fuel**: filter by gas station vendor names (7-Eleven, RaceTrac, Exxon, Shell, etc.)
- **Vehicle loan**: filter by credit union / financing company
- **Maintenance/other**: everything else — if this bucket is huge, likely miscategorized expenses

### 8. Hotels / Lodging
Search Name and Memo fields for hotel chain keywords. For one-time service businesses, hotel costs should be rare — flag if frequent.

## Chart Generation for Telegram Delivery

Generate PNG charts optimized for mobile viewing:

- **Dimensions**: 11-12" wide, 5-8" tall (landscape, readable on phone)
- **DPI**: 150 (sharp without huge file size)
- **Colors**: High contrast — green for revenue/profit, red for expenses/loss, orange for warnings
- **Font size**: 12pt minimum, titles 15pt bold
- **Axis labels**: Use `$XK` format (divide by 1000) to keep labels short
- **Annotations**: Add value labels at end of bars, percentage labels inside bars
- **File size**: Keep under 200KB for fast Telegram delivery

Chart types that work well:
1. Monthly Revenue vs Expenses (grouped bar) — the "are we profitable" chart
2. Expense breakdown (horizontal bar with %) — where the money goes
3. Top customers (horizontal bar with concentration %) — revenue risk
4. Cumulative P&L (area chart, green/red fill) — the "have we ever been profitable" chart
5. Seasonality (grouped bar by month) — when to market
6. Travel cost vs invoice (scatter) — which jobs lose money
7. Year-over-year comparison (small multiples) — trajectory

## Deliverables Format

Deliver to user via Telegram:
1. Charts as PNG images (sent as MEDIA: attachments)
2. Full detailed text report as .txt file
3. Concise written summary in message body covering:
   - Headline finding (profitable? losing money? by how much?)
   - Top 3-5 leaks with dollar amounts
   - What's working well (positive reinforcement)
   - Seasonality table
   - Actionable recommendations

## Key Findings Patterns in Service Businesses

Watch for these common small business issues:
- **Salaries exceeding revenue** — owner compensation isn't sustainable at current volume
- **Bank fees >3% of revenue** — needs account negotiation or switching
- **Travel costs >20% of small jobs** — minimum job size needed
- **Single customer >25% of revenue** — concentration risk
- **Uncategorized expenses** — sloppy bookkeeping, can't analyze what you can't categorize
- **Car maintenance with 100+ transactions** — likely miscategorized, needs cleanup
- **Cumulative net always negative** — business funded by owner investment, not sustainable
- **Seasonal dead months** — opportunity for targeted marketing or maintenance/off-season services