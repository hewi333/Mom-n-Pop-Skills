---
name: crm-lite
description: "Use when tracking customer interactions, managing leads, or building a lightweight CRM for small businesses without dedicated CRM software. Stores contacts, leads, activities, estimates, and communications in local SQLite."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [crm, sqlite, small-business, customer-management]
    related_skills: [estimator-engine, quickbooks-online, mailchimp-integration, stripe-payments, outlook-graph, base44-deploy]
---

# CRM-Lite — Lightweight SQLite CRM for Small Business

## Overview
A minimal, file-based CRM built on SQLite for non-technical small business owners. No server, no external dependencies, no auth complexity. Designed for agent-mediated use: the owner interacts via text message with the agent, which reads/writes this database.

## When to Use
- **Small business** (1-10 employees) with no existing CRM
- **Agent-mediated access** — owners interact via chat/Telegram, not direct DB access
- **Lead tracking** from website forms, referrals, email inquiries
- **Pipeline visibility** — estimate sent → accepted/rejected → job scheduled → paid
- **Communication log** — every email, call, text logged automatically

## Don't Use For
- Multi-user concurrent access with role-based permissions
- Complex sales methodologies (MEDDIC, Challenger, etc.)
- Real-time collaboration features
- Integration with enterprise SSO/SCIM

## Core Features

### Data Model (SQLite: `crm.db`)
1. **customers** — Core customer records
   - `id` (PK), `name`, `email`, `phone`, `company`, `address`, `city`, `state`, `zip`
   - `lead_source`, `lead_status` (new/qualified/estimate_sent/won/lost)
   - `total_value`, `notes`, `created_at`, `updated_at`

2. **leads** — Inbound leads before qualification
   - `id`, `source` (website/referral/email/phone), `contact_name`
   - `contact_email`, `contact_phone`, `company`, `property_address`
   - `sqft`, `ceiling_height`, `service_type`, `urgency`
   - `status` (new/qualified/estimate_ready/scheduled/lost)
   - `assigned_to`, `created_at`, `updated_at`

3. **activities** — Every touchpoint
   - `id`, `customer_id` (FK), `lead_id` (FK), `activity_type` (call/email/text/meeting/estimate_sent/estimate_accepted/estimate_rejected/job_scheduled/job_completed/invoice_sent/payment_received)
   - `description`, `outcome`, `next_action`, `next_action_date`
   - `created_at`, `updated_at`

4. **estimates** — Estimate lifecycle
   - `id`, `customer_id`, `lead_id`, `estimate_number`, `amount`
   - `status` (draft/sent/accepted/rejected/expired)
   - `sent_date`, `accepted_date`, `rejected_date`, `expires_date`
   - `line_items` (JSON), `notes`, `created_at`, `updated_at`

5. **communications** — Message log
   - `id`, `customer_id`, `lead_id`, `direction` (inbound/outbound)
   - `channel` (email/sms/telegram/phone), `subject`, `body`
   - `sent_at`, `created_at`

6. **tasks** — Action items for owners
   - `id`, `customer_id`, `lead_id`, `title`, `description`
   - `due_date`, `priority` (low/medium/high/urgent), `status` (pending/in_progress/done)
   - `assigned_to`, `created_at`, `updated_at`

## Quick Start

```python
import sqlite3
from pathlib import Path

DB_PATH = Path("~/.hermes/crm/crm.db").expanduser()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT, phone TEXT,
            company TEXT, address TEXT, city TEXT, state TEXT, zip TEXT,
            lead_source TEXT, lead_status TEXT DEFAULT 'new',
            total_value REAL DEFAULT 0, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ... other tables
    conn.commit()
    return conn
```

## Agent Integration Patterns

### Create Lead from Website Form
```
User: "New lead from website: John Smith, john@email.com, 555-555-0123, 123 Main St [CITY] [STATE] [ZIP], 2500 sqft, service request"
Agent: Creates lead record, sets status=qualified, creates task for the owner to review
```

### Log Estimate Sent
```
User: "Sent estimate #EST-0001-0042 to John Smith for $2,850"
Agent: Updates estimate status=sent, creates activity, creates task for follow-up in 3 days
```

### Weekly Pipeline Report (Cron)
```
Agent: Queries all leads/customers, summarizes by stage, sends to the owner via Telegram
```

## End-to-End Demo Flow

This skill is the central hub for the demo flow. The full orchestration across all 7 skills is documented in `references/demo-flow.md` — read it before building or recording the demo. It covers: lead intake -> estimate -> Stripe payment link -> email -> payment confirmation -> calendar scheduling -> daily report, plus the 90-second demo script and credential checklist.

## Common Pitfalls

1. **Forgetting to create indexes** — Add indexes on `customers.email`, `leads.status`, `activities.customer_id` for query speed
2. **Not backing up** — SQLite file is the entire DB; copy to S3/Drive daily via cron
3. **Schema drift** — Use migrations (numbered SQL files) rather than ad-hoc ALTER TABLE
4. **Concurrent writes** — SQLite handles concurrent reads, but writes serialize; keep transactions short

## Verification Checklist

- [ ] `crm.db` created with all 6 tables
- [ ] Indexes on foreign keys and query columns
- [ ] Agent can: create lead, log activity, update estimate status, create task
- [ ] Weekly report cron outputs: new leads, estimates sent, conversion rate, pipeline value
- [ ] Backup script copies DB to offsite location daily

## One-Shot Recipes

### "New lead from referral"
```python
conn = init_db()
lead_id = conn.execute("""
    INSERT INTO leads (source, contact_name, contact_email, contact_phone, company, property_address, sqft, service_type, status)
    VALUES ('referral', 'Jane Doe', 'jane@example.com', '555-555-0199', 'Example Realty', '456 Palm Ave [CITY] [STATE] [ZIP]', 3200, 'service_request', 'qualified')
""").lastrowid
conn.commit()
```

### "Get pipeline summary for weekly report"
```python
summary = conn.execute("""
    SELECT
        COUNT(CASE WHEN lead_status='new' THEN 1 END) as new_leads,
        COUNT(CASE WHEN lead_status='estimate_sent' THEN 1 END) as estimates_out,
        COUNT(CASE WHEN lead_status='won' THEN 1 END) as won,
        SUM(CASE WHEN lead_status='won' THEN total_value ELSE 0 END) as revenue
    FROM customers
""").fetchone()
```