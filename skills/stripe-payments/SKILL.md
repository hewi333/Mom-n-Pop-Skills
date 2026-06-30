---
name: stripe-payments
description: Create Stripe checkout sessions, payment links, invoices, and customers via Stripe REST API. Use when processing payments, sending invoices, or managing customer billing for a service business.
---

# Stripe Payments Skill

## When to Use
- Customer needs to pay for an estimate/job
- Creating an invoice for a service
- Setting up a customer in Stripe for recurring billing
- Generating a payment link to send to a client
- Checking payment status for a job
- Agent needs to pay for its own SaaS subscriptions (hackathon "earn and spend" angle)

## Prerequisites
- Stripe API key (secret key, starts with `sk_`)
- Stripe account in test mode for demos
- Stripe CLI installed for webhook testing (optional)
- Environment variable: `STRIPE_SECRET_KEY`

## Setup

### 1. Get API Key
1. Log in to Stripe Dashboard (dashboard.stripe.com)
2. Toggle "Test mode" on (top right)
3. Developers > API Keys > Copy "Secret key" (sk_test_...)

### 2. Store Key in Hermes Environment
Add to `~/.hermes/.env`:
```
STRIPE_SECRET_KEY=sk_tes...xxxx
```

### 3. Stripe CLI (optional, for local webhooks)
```bash
# Install
curl -sL https://github.com/stripe/stripe-cli/releases/latest/download/stripe_linux_x86_64.tar.gz | tar xz -C /usr/local/bin/
stripe login
stripe listen --forward-to localhost:8642/v1/stripe/webhook
```

## API Reference

All Stripe API calls use `https://api.stripe.com/v1/` with Bearer auth.

### Create Customer
```bash
curl -s https://api.stripe.com/v1/customers \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d name="John Smith" \
  -d email="john@example.com" \
  -d phone="555-555-1234" \
  -d "metadata[business]=[BUSINESS_NAME]" \
  -d "metadata[source]=Referral" \
  -d "metadata[address]=123 Main St, [CITY], [STATE]"
```

### Create Payment Link (simplest for demo)
```bash
curl -s https://api.stripe.com/v1/payment_links \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d "line_items[0][price_data][currency]=usd" \
  -d "line_items[0][price_data][unit_amount]=250000" \
  -d "line_items[0][price_data][product_data][name]=Service - Residential 2000sqft" \
  -d "line_items[0][quantity]=1" \
  -d "metadata[customer_name]=John Smith" \
  -d "metadata[service_type]=Residential" \
  -d "metadata[sqft]=2000"
```
Returns a URL like `https://buy.stripe.com/...` you can send to the customer.

### Create Checkout Session (more control)
```bash
curl -s https://api.stripe.com/v1/checkout/sessions \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d mode=payment \
  -d "success_url=https://yourdomain.com/success" \
  -d "cancel_url=https://yourdomain.com/cancel" \
  -d "customer_email=customer@example.com" \
  -d "line_items[0][price_data][currency]=usd" \
  -d "line_items[0][price_data][unit_amount]=250000" \
  -d "line_items[0][price_data][product_data][name]=Service - Residential" \
  -d "line_items[0][quantity]=1" \
  -d "metadata[job_id]=JOB-0001-001" \
  -d "metadata[estimate_amount]=2500"
```
Unit amount is in cents: $2,500.00 = 250000.

### Create Invoice (for NET-30 billing)
```bash
# Step 1: Create invoice
INVOICE=$(curl -s https://api.stripe.com/v1/invoices \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d customer=$CUSTOMER_ID \
  -d "description=Service - Residential")
INVOICE_ID=$(echo "$INVOICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Step 2: Add line item
curl -s https://api.stripe.com/v1/invoiceitems \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d customer=$CUSTOMER_ID \
  -d invoice=$INVOICE_ID \
  -d amount=250000 \
  -d currency=usd \
  -d "description=Service - Residential 2000sqft - Standard Region"

# Step 3: Finalize and send
curl -s https://api.stripe.com/v1/invoices/$INVOICE_ID/finalize \
  -H "Authorization: Bearer $STRIP...KEY"
curl -s https://api.stripe.com/v1/invoices/$INVOICE_ID/send \
  -H "Authorization: Bearer $STRIP...KEY"
```

### Check Payment Status
```bash
curl -s https://api.stripe.com/v1/checkout/sessions/$SESSION_ID \
  -H "Authorization: Bearer $STRIP...KEY" | python3 -m json.tool
# Look for "payment_status": "paid"
```

### List All Payments
```bash
curl -s "https://api.stripe.com/v1/payment_intents?limit=10" \
  -H "Authorization: Bearer $STRIP...KEY" | python3 -m json.tool
```

### Refund (if needed)
```bash
curl -s https://api.stripe.com/v1/refunds \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d payment_intent=$PI_ID \
  -d amount=250000  # partial refund amount in cents, omit for full
```

## Integration Patterns

### Pattern 1: Estimate -> Payment Link (Quick Pay)
1. Agent runs estimator-engine skill to calculate price
2. Agent creates Stripe payment link for that amount
3. Agent stores payment link URL in CRM (crm-lite)
4. Agent emails link to customer via email skill
5. Agent monitors payment status and updates CRM when paid

### Pattern 2: Invoice -> Email -> Track (NET-30)
1. Agent creates Stripe customer
2. Agent creates invoice with line items
3. Agent finalizes and sends invoice (Stripe emails customer)
4. Agent logs invoice ID in CRM
5. Agent checks payment status daily via cron job

### Pattern 3: Agent Pays for Its Own SaaS (Hackathon Angle)
1. Agent has Stripe Connected Account
2. Agent creates payment link for a service
3. Customer pays -> funds land in business Stripe account
4. Agent uses Stripe to pay for Base44, Mailchimp, or other SaaS
5. Demonstrates "agent that earns and spends real money"

## Quick Start: Full Estimate-to-Payment Flow

```bash
# 1. Get customer info from CRM
CUSTOMER_NAME="John Smith"
CUSTOMER_EMAIL="john@example.com"
SQFT=2000
REGION="Standard"
# Price from estimator: 2000sf * $1.40/sf = $2,800 (example — use your configured rates)
AMOUNT=280000  # $2,800.00 in cents

# 2. Create Stripe customer
CUSTOMER=$(curl -s https://api.stripe.com/v1/customers \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d name="$CUSTOMER_NAME" \
  -d email="$CUSTOMER_EMAIL")
CUSTOMER_ID=$(echo "$CUSTOMER" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 3. Create payment link
LINK=$(curl -s https://api.stripe.com/v1/payment_links \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d "line_items[0][price_data][currency]=usd" \
  -d "line_items[0][price_data][unit_amount]=$AMOUNT" \
  -d "line_items[0][price_data][product_data][name]=Service - Residential $SQFT sqft" \
  -d "line_items[0][quantity]=1" \
  -d "metadata[customer_id]=$CUSTOMER_ID" \
  -d "metadata[sqft]=$SQFT" \
  -d "metadata[region]=$REGION")
PAYMENT_URL=$(echo "$LINK" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")

echo "Payment link: $PAYMENT_URL"
```

## Webhooks (for automated payment confirmation)
```bash
# Create webhook endpoint
curl -s https://api.stripe.com/v1/webhook_endpoints \
  -H "Authorization: Bearer $STRIP...KEY" \
  -d "url=https://yourdomain.com/webhook/stripe" \
  -d "enabled_events[]=checkout.session.completed" \
  -d "enabled_events[]=invoice.paid" \
  -d "enabled_events[]=payment_intent.payment_failed"
```

## Test Cards (for demo)
- Successful payment: `4242 4242 4242 4242` (Visa)
- Requires authentication: `4000 0027 6000 3184`
- Declined payment: `4000 0000 0000 0002`
- Any future date for expiry, any CVC, any ZIP

## Common Pitfalls
- **Amounts are in cents, not dollars**: $2,500 = 250000, not 2500
- **Test mode vs Live mode**: Always verify you're using sk_test_ keys for demo
- **Don't store customer card data**: Never log full card numbers; Stripe handles PCI compliance
- **Webhook signature verification**: For production, verify Stripe-Signature header
- **Rate limits**: Stripe allows ~100 read/sec and ~100 write/sec per key
- **Currency must be lowercase**: `usd` not `USD`
- **Price tiers from estimator**: Match the estimator-engine output exactly to avoid billing errors

## Verification Checklist
- [ ] STRIPE_SECRET_KEY set in environment
- [ ] Can create customer (test mode)
- [ ] Can create payment link and get URL
- [ ] Can create checkout session
- [ ] Can create and send invoice
- [ ] Can check payment status
- [ ] Test card payment succeeds with 4242 card
- [ ] Payment updates CRM record (integration with crm-lite)
- [ ] Invoice email reaches customer (integration with email skill)