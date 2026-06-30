---
name: financial-analysis
description: "Analyze business financials from a QuickBooks CSV export. Identifies cost categories, drills down on areas to cut costs, flags low-margin jobs, and spots revenue opportunities. CSV import now, QuickBooks API wiring optional later. Designed for small business owners who don't read spreadsheets — agent translates the numbers into plain English."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [finance, quickbooks, cost-analysis, revenue, csv, small-business]
    related_skills: [quickbooks-online, crm-lite, estimator-engine]
---

# Financial Analysis Skill

## Overview
Takes a QuickBooks CSV export (Profit & Loss, Transaction List, or Sales by Item)
and produces a plain-English financial analysis for a non-technical business owner.
The agent identifies cost categories, flags problem areas, and suggests specific
actions — all delivered in Telegram as a readable summary, not a spreadsheet.

**Two modes:**
1. **CSV import** (works now) — owner exports from QuickBooks, sends to agent
2. **QuickBooks API** (optional) — agent pulls financials directly (requires
   `quickbooks-online` skill to be wired with OAuth tokens)

## When to Use
- "Analyze my QuickBooks export" (after sending a CSV)
- "Where am I losing money?"
- "Which jobs had the worst margins last quarter?"
- "What are my biggest cost categories?"
- "Give me a financial summary for the owner meeting"
- Monthly/quarterly financial review

## Prerequisites

### CSV Mode (current)
- CSV file exported from QuickBooks Online or QuickBooks Desktop
- File placed on the VPS (or content pasted — see formats below)

### QuickBooks API Mode (optional, post-hackathon)
- `quickbooks-online` skill installed + OAuth tokens wired
- Not required for CSV mode

## Supported CSV Formats

### Format 1: Profit & Loss (Standard QuickBooks Export)
```csv
Date,Transaction Type,Num,Name,Memo/Description,Account,Income,Expense
2026-01-15,Invoice,101,Smith Residence,Odor removal service,Service Income,2800,
2026-01-18,Bill,,Home Depot,Chemicals,COGS - Chemicals,,150
```

### Format 2: Transaction List (All Transactions)
```csv
Date,Transaction Type,Num,Name,Split,Amount,Status
2026-01-15,Invoice,101,Smith Residence,Service Income,2800,Cleared
2026-01-18,Bill,,Home Depot,COGS - Chemicals,-150,Cleared
```

### Format 3: Sales by Item/Job
```csv
Item/Job,Qty,Amount,COGS,Margin,Margin %
Odor Removal - Residential,1,2800,350,2450,87.5%
Odor Removal - Commercial,2,4500,800,3700,82.2%
```

**The agent auto-detects the format** by reading the header row and matching
column names. If columns are ambiguous, the agent asks the owner to clarify.

## The Flow

### Step 1: Owner Sends CSV
Owner sends file to agent (via Telegram document upload or places on VPS).
Agent confirms receipt and reads the file.

### Step 2: Agent Parses + Categorizes
```python
import csv
import json
from collections import defaultdict

def analyze_csv(filepath):
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Auto-detect format from headers
    headers = set(rows[0].keys())

    if 'Income' in headers or 'Expense' in headers:
        return analyze_pnl(rows)
    elif 'Amount' in headers:
        return analyze_transactions(rows)
    elif 'COGS' in headers or 'Margin' in headers:
        return analyze_sales_by_job(rows)
    else:
        return {"error": "Unknown CSV format", "headers": list(headers)}
```

### Step 3: Agent Runs Analysis

#### A. Revenue Summary
- Total revenue (period)
- Revenue by job/customer
- Revenue by service type (if identifiable)
- Month-over-month trend
- Average job size

#### B. Cost Analysis
- Total costs (period)
- Cost categories (ranked by size):
  - COGS (chemicals, equipment, supplies)
  - Labor (subcontractors, wages)
  - Travel/fuel
  - Marketing
  - Software/subscriptions
  - Insurance
  - Other
- Cost as % of revenue (overall)
- Cost trend (increasing? decreasing?)

#### C. Job-Level Profitability
- Each job with revenue, cost, and margin
- **Flag: jobs with margin < 30%** (or negative margin)
- **Flag: jobs where cost > revenue** (loss-making)
- Best performing job (highest margin)
- Worst performing job (biggest loss or lowest margin)

#### D. Opportunity Analysis
- Most profitable service type → "do more of these"
- Least profitable → "consider raising prices or declining"
- Customer concentration risk (if >X% from one source)
- Seasonal patterns (which months are strongest)
- Cost categories growing faster than revenue

### Step 4: Agent Delivers Plain-English Report
```
📊 [BUSINESS_NAME] Financial Analysis — Jan-Jun 2026

TOTALS:
- Revenue: $48,200 across 22 jobs
- Costs: $14,800 (30.7% of revenue)
- Net profit: $33,400 (69.3% margin — healthy)

YOUR BIGGEST COST CATEGORIES:
1. Chemicals & Supplies: $4,200 (28% of costs)
2. Fuel/Travel: $3,100 (21% of costs)
3. Insurance: $2,400 (16% of costs)
4. Software/Subscriptions: $890 (6% of costs)

⚠️ JOBS THAT NEED ATTENTION:
- Job #1018 ([CITY], small apartment): Revenue $650,
  Costs $580 → Margin only 8.6%. This job cost almost
  as much as it made. Consider a minimum job size of
  $1,000 or raise the small-job rate.

💰 YOUR BEST JOBS:
- Job #1003 ([CITY], 3200 sqft residential): Revenue
  $3,800, Costs $290 → Margin 92.4%. Large residential
  jobs are your sweet spot.

📈 OPPORTUNITIES:
- Your [CITY]/[REGION] jobs average 88% margin vs
  72% in other regions. Consider targeting more [REGION]
  partners.
- Your commercial jobs average $4,500 vs $2,400 for
  residential. But you only did 3 commercial jobs vs 19
  residential. More commercial outreach could boost revenue.
- Fuel costs are 21% of total costs. Premium Region trips
  have higher fuel — the Premium Region
  surcharge should be reviewed to ensure it covers actual
  travel cost.

NEXT STEPS:
- Set a minimum job size? (Your smallest jobs have
  the worst margins)
- Raise the Premium Region travel surcharge?
- Target more commercial jobs?
- More marketing to [REGION] partners?

Want me to dig deeper into any of these?
```

### Step 5: Owner Can Ask Follow-Ups
- "Show me all jobs under $1,000"
- "What's my average margin by region?"
- "Break down the chemical costs month by month"
- "Which months had the highest revenue?"
- "Compare my margins last year vs this year"

## QuickBooks API Integration (Optional, Post-Hackathon)

When `quickbooks-online` skill is wired with OAuth tokens, the agent can
pull financials directly without CSV export:

```python
# Pseudocode — requires quickbooks-online skill to be wired
from intuitlib.client import AuthClient

# Pull Profit & Loss report
pnl = quickbooks.get_report('ProfitAndLoss', start_date='2026-01-01',
                            end_date='2026-06-30')

# Pull Sales by Customer
sales = quickbooks.get_report('SalesByCustomer', start_date='2026-01-01',
                               end_date='2026-06-30')

# Run same analysis as CSV mode but from live data
```

## Agent Integration Patterns

### Pattern 1: Monthly Financial Review
```
Owner: "Analyze my June financials"
Agent: [reads CSV / pulls from QBO] → produces report → sends in Telegram
Owner: "Why were chemical costs so high in June?"
Agent: [drills into chemical line items] → "3 large commercial jobs in
       June required extra treatments — $1,200 of the $1,800 total"
```

### Pattern 2: Job Profitability Audit
```
Agent: "I noticed 3 jobs last quarter had margins under 20% — want a
       breakdown?"
Owner: "Yes"
Agent: [lists jobs with revenue, costs, margin] → "All three were
       small apartments under 1,000 sqft. Your minimum job rate of
       $1,500 would have prevented two of these from being unprofitable."
```

### Pattern 3: CRM Cross-Reference
```
Agent: "Your CRM shows 8 jobs booked from Standard Region partners this
       quarter, averaging $2,100 revenue. But your financials show
       Standard Region jobs average 72% margin vs 88% in Premium Region. Want me
       to draft a targeted Premium Region partner campaign?"
```

### Pattern 4: Estimator Sanity Check
```
Agent: "Your financials show actual job costs averaging 30% of revenue.
       Your estimator-engine assumes 25% cost ratio. The gap is mostly
       fuel costs on Premium Region jobs. Want me to update the estimator
       to include a fuel surcharge for Premium Region?"
```

## Common Pitfalls

1. **CSV format varies** — QuickBooks Online, Desktop, and different
   report types all export differently. The agent must auto-detect and
   ask if unsure. Don't assume column names.
2. **Cost allocation** — Some costs (insurance, software) aren't tied
   to specific jobs. The agent should separate direct job costs from
   overhead and be clear about the difference.
3. **Time periods** — Always confirm the date range with the owner
   before analyzing. "This shows Jan-Jun 2026 — is that right?"
4. **Negative numbers** — QuickBooks sometimes exports expenses as
   positive, sometimes as negative. The agent should detect the
   convention and normalize.
5. **Missing data** — If COGS isn't broken out by job, the agent should
   say so rather than guessing. "Chemical costs are lumped — I can't
   tie them to specific jobs without more detail."
6. **Don't give financial advice.** The agent identifies patterns and
   asks questions. The owner makes decisions. The agent is a tool, not
   a CPA.
7. **Privacy** — Financial data stays on the VPS. Don't send raw numbers
   to external services. Summary in Telegram is fine; raw CSV is not.

## Verification Checklist
- [ ] Can read CSV file from disk
- [ ] Auto-detects CSV format from headers
- [ ] Parses income/expense transactions correctly
- [ ] Identifies cost categories and ranks by size
- [ ] Calculates job-level margins
- [ ] Flags jobs with margin < 30%
- [ ] Flags jobs where cost > revenue
- [ | Produces plain-English summary in Telegram
- [ ] Owner can ask follow-up questions
- [ ] QuickBooks API integration (optional, post-hackathon)

## One-Shot Recipes

### "Quick financial health check"
```python
# Reads CSV → returns: total revenue, total costs, margin %,
# top 3 cost categories, worst job, best job, 2-3 recommendations
```

### "Cost breakdown by category"
```python
# Groups all expenses by account/category → ranks by total →
# calculates each as % of revenue → flags any category growing
# faster than revenue
```

### "Job profitability ranking"
```python
# For each job: revenue, direct costs, margin, margin %
# Sorted by margin % ascending (worst first)
# Flags any job with margin < 30% or cost > revenue
```