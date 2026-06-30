---
name: quickbooks-online
description: "Use when integrating with QuickBooks Online for invoicing, estimates, customers, and payments. Handles OAuth 2.0 auth, token refresh, and sandbox/production environments."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [quickbooks, intuit, accounting, invoicing, small-business]
    related_skills: [crm-lite, estimator-engine, stripe-payments]
---

# QuickBooks Online Integration Skill

## Overview
Integrates a small business with QuickBooks Online for customer management, estimates, invoices, and payment tracking. Uses Intuit's OAuth 2.0 flow with automatic token refresh. Designed for agent-mediated use: owners text commands, agent executes QB API calls.

## When to Use
- **Create/send estimates** from estimator-engine output
- **Convert estimates to invoices** when job is booked
- **Record payments** (Stripe webhook → QB payment)
- **Sync customers** between CRM and QB
- **Pull reports** for weekly owner summary (AR aging, revenue, outstanding estimates)

## Don't Use For
- Complex inventory/assembly tracking
- Multi-currency or multi-entity accounting
- Payroll or tax filing

## Authentication (OAuth 2.0)

### Required Credentials (Environment Variables)
```
QBO_CLIENT_ID=*** From Intuit Developer Dashboard
QBO_CLIENT_SECRET= # From Intuit Developer Dashboard
QBO_REDIRECT_URI= # e.g., https://your-domain.com/qbo/callback
QBO_ENVIRONMENT= # "sandbox" or "production"
QBO_COMPANY_ID= # Realm ID (set after first auth)
```

### Token Storage
- Store access_token + refresh_token + realm_id in `~/.hermes/qbo_tokens.json`
- Auto-refresh: access_token expires in 1 hour; refresh_token expires in 101 days
- On 401: refresh token, retry once, then force re-auth if refresh fails

### Auth Flow
1. User visits: `https://appcenter.intuit.com/connect/oauth2?client_id={id}&redirect_uri={uri}&scope=com.intuit.quickbooks.accounting&response_type=code&state={random}`
2. Callback receives `code` + `realmId`
3. Exchange code for tokens: `POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer`
4. Store tokens + realm_id

## Core API Operations

### Customers
```python
# Create customer (from CRM lead)
POST /v3/company/{realmId}/customer
{
  "DisplayName": "John Smith",
  "PrimaryEmailAddr": {"Address": "john@email.com"},
  "PrimaryPhone": {"FreeFormNumber": "555-555-0123"},
  "BillAddr": {"Line1": "123 Main St", "City": "[CITY]", "CountrySubDivisionCode": "[STATE]", "PostalCode": "[ZIP]"},
  "Notes": "Lead from referral"
}

# Query customer
GET /v3/company/{realmId}/query?query=SELECT * FROM Customer WHERE DisplayName='John Smith'
```

### Estimates
```python
# Create estimate (from estimator-engine output)
POST /v3/company/{realmId}/estimate
{
  "CustomerRef": {"value": "123"},
  "TxnDate": "2026-01-15",
  "ExpirationDate": "2026-02-14",
  "Line": [
    {
      "DetailType": "SalesItemLineDetail",
      "Amount": 3125.00,
      "Description": "Service - 2500 sqft, vaulted ceilings, moderate tobacco",
      "SalesItemLineDetail": {"ItemRef": {"value": "1", "name": "Base Treatment"}, "Qty": 2500, "UnitPrice": 1.25}
    },
    {"DetailType": "SalesItemLineDetail", "Amount": 350.00, "Description": "Cigarette >5yrs extended treatment", "SalesItemLineDetail": {"ItemRef": {"value": "2"}, "Qty": 1, "UnitPrice": 350}},
    {"DetailType": "SalesItemLineDetail", "Amount": 75.00, "Description": "Travel surcharge - Premium Region", "SalesItemLineDetail": {"ItemRef": {"value": "3"}, "Qty": 1, "UnitPrice": 75}}
  ],
  "CustomerMemo": {"value": "Valid 30 days. 50% deposit to schedule."}
}

# Send estimate email
POST /v3/company/{realmId}/estimate/{estimateId}/send?sendTo={email}
```

### Invoices
```python
# Create invoice from accepted estimate
POST /v3/company/{realmId}/invoice
{
  "CustomerRef": {"value": "123"},
  "TxnDate": "2026-01-20",
  "DueDate": "2026-02-03",
  "Line": [...same line items...],
  "Deposit": 1562.50,  # 50% deposit collected via Stripe
  "CustomerMemo": {"value": "Balance due upon completion"}
}

# Get invoice PDF
GET /v3/company/{realmId}/invoice/{invoiceId}/pdf
```

### Payments
```python
# Record payment (from Stripe webhook)
POST /v3/company/{realmId}/payment
{
  "CustomerRef": {"value": "123"},
  "TotalAmt": 1562.50,
  "PaymentRefNum": "pi_3StripePaymentIntentId",
  "PaymentMethodRef": {"value": "5"},  # Credit Card
  "DepositToAccountRef": {"value": "35"},  # Undeposited Funds
  "Line": [{"Amount": 1562.50, "LinkedTxn": [{"TxnId": "456", "TxnType": "Invoice"}]}]
}
```

### Items (Products/Services)
```python
# Ensure service items exist (run once on setup)
# Base Treatment (per sqft)
# Cigarette Extended Treatment (each)
# Travel Surcharge (each)
# HVAC Duct Treatment (each)
# High Rise Surcharge (each)
# Region Surcharge (each)
```

## Agent Integration Patterns

### "Create estimate for John Smith at 123 Main St..."
```python
# 1. Look up or create customer in QB
# 2. Call estimator-engine with property details
# 3. Transform estimator output → QB estimate line items
# 4. Create estimate in QB
# 5. Email PDF to customer
# 6. Create CRM estimate record (status=sent)
# 7. Create follow-up task (3 days)
```

### "Customer accepted estimate #EST-0001-0042"
```python
# 1. Update CRM estimate status=accepted
# 2. Create invoice in QB (copy line items)
# 3. Generate Stripe Payment Link for 50% deposit
# 4. Text customer deposit link
# 5. Create job scheduled task for the owner
```

### "Record payment from Stripe webhook"
```python
# 1. Verify webhook signature
# 2. Find invoice by payment_intent metadata
# 3. Create QB Payment linked to invoice
# 4. Update CRM invoice status=paid
# 5. Notify owners via Telegram
```

## Common Pitfalls

1. **Token expiry** — Always wrap API calls in try/except 401 → refresh → retry
2. **Sandbox vs production** — Different base URLs, different realm IDs, different client credentials
3. **Minor version** — Always send `minorversion=75` header for latest API
4. **Idempotency** — Use `RequestId` header for estimate/invoice creation to avoid duplicates
5. **Rate limits** — 500 requests/minute; implement exponential backoff
6. **Custom fields** — QB custom fields need definition before use; use `Notes` field for flexibility
7. **Tax** — Many services are non-taxable; ensure items are marked non-taxable per your local tax rules

## Verification Checklist
- [ ] OAuth flow completes and stores tokens
- [ ] Token refresh works (wait 1hr or force expiry)
- [ ] Create customer → appears in QB UI
- [ ] Create estimate with line items → PDF renders correctly
- [ ] Send estimate email → customer receives it
- [ ] Convert estimate to invoice → amounts match
- [ ] Record payment → invoice shows paid
- [ ] Weekly report pulls: outstanding estimates, AR aging, revenue MTD

## One-Shot Recipes

### "Sync new CRM lead to QuickBooks"
```python
customer = qbo.upsert_customer(
    name="Jane Doe",
    email="jane@email.com",
    phone="555-555-0199",
    address="456 Palm Ave, [CITY], [STATE] [ZIP]",
    notes="Referral - Example Realty"
)
```

### "Push estimator output to QB estimate"
```python
estimate = qbo.create_estimate(
    customer_id=customer.id,
    line_items=estimator_output.line_items,  # [{desc, qty, unit_price, total}]
    txn_date="2026-01-15",
    expiration_date="2026-02-14",
    memo="Valid 30 days. 50% deposit to schedule."
)
qbo.send_estimate(estimate.id, customer.email)
```

### "Weekly owner report data"
```python
report = qbo.get_weekly_report(realm_id)
# Returns: {outstanding_estimates: [...], ar_aging: {...}, revenue_mtd: 45000, payments_this_week: [...]}
```