# Service Business → QuickBooks Online Field Mapping

## Overview
Maps service business job/estimate data to QuickBooks Online entities for seamless accounting integration.

## Customer Mapping

### CRM Lead → QB Customer
| Business Field | QB Field | Transform |
|----------------|----------|-----------|
| lead.first_name + " " + lead.last_name | DisplayName | Required |
| lead.email | PrimaryEmailAddr.Address | Optional |
| lead.phone | PrimaryPhone.FreeFormNumber | Optional |
| lead.address_line1 | BillAddr.Line1 | Optional |
| lead.address_city | BillAddr.City | Optional |
| lead.address_state | BillAddr.CountrySubDivisionCode | [STATE] |
| lead.address_zip | BillAddr.PostalCode | Optional |
| lead.notes | Notes | "Source: {lead.source}" |

### Duplicate Detection
- Match on: DisplayName + PrimaryEmailAddr
- If exists: Update BillAddr, Notes
- If not: Create new

## Estimate Mapping

### Estimator Output → QB Estimate Line Items
| Estimator Field | QB Line Field | Transform |
|-----------------|---------------|-----------|
| line_items[].description | Description | As-is |
| line_items[].quantity | SalesItemLineDetail.Qty | Number |
| line_items[].unit_price | SalesItemLineDetail.UnitPrice | Number |
| line_items[].total | Amount | qty × unit_price |

### Service Items (Pre-create in QB)
| Service | QB Item Name | Type | Unit | Taxable |
|---------|-------------|------|------|---------|
| Base Treatment | Base Treatment | Service | sqft | false |
| Cigarette >5yrs | Cigarette Extended Treatment | Service | each | false |
| Travel Surcharge | Travel Surcharge | Service | each | false |
| HVAC Duct Treatment | HVAC Duct Treatment | Service | each | false |
| High Rise Surcharge | High Rise Surcharge | Service | each | false |
| Region Surcharge | Region Surcharge | Service | each | false |

### Estimate Header
| Business Field | QB Field | Transform |
|----------------|----------|-----------|
| job.id | CustomField (DocNumber prefix) | "JOB-{id}" |
| estimator.txn_date | TxnDate | YYYY-MM-DD |
| estimator.expiration_date | ExpirationDate | YYYY-MM-DD |
| estimator.memo | CustomerMemo.value | As-is |
| estimator.deposit_pct | Deposit | total × pct |

## Invoice Mapping

### Accepted Estimate → QB Invoice
| Source | QB Field | Transform |
|--------|----------|-----------|
| Estimate.CustomerRef | CustomerRef | Copy |
| Estimate.Line[] | Line[] | Copy (adjust amounts if scope changed) |
| Estimate.TxnDate | TxnDate | Today |
| job.scheduled_date | DueDate | TxnDate + 14 days |
| job.deposit_paid | Deposit | Amount already paid |
| job.notes | CustomerMemo.value | "Balance due upon completion" |

### Partial Payments (Deposit)
- QB Invoice supports `Deposit` field for upfront payment
- Remaining balance = Total - Deposit
- Stripe webhook → QB Payment linked to Invoice

## Payment Mapping

### Stripe Webhook → QB Payment
| Stripe Field | QB Field | Transform |
|--------------|----------|-----------|
| payment_intent.id | PaymentRefNum | "pi_{id}" |
| amount / 100 | TotalAmt | Convert cents → dollars |
| customer.email | CustomerRef (lookup) | Find QB customer by email |
| payment_intent.metadata.invoice_id | LinkedTxn.TxnId | Link to QB Invoice |
| payment_method.type | PaymentMethodRef | Map: card→5 (Credit Card) |
| succeeded_at | TxnDate | ISO date |

### Payment Methods Mapping
| Stripe Type | QB PaymentMethodRef | QB Name |
|-------------|---------------------|---------|
| card | 5 | Credit Card |
| bank_transfer | 2 | Check |
| cash | 1 | Cash |

## Report Queries

### Weekly Owner Report
```sql
-- Outstanding Estimates (last 30 days)
SELECT DocNumber, CustomerRef, TxnDate, TotalAmt, ExpirationDate
FROM Estimate
WHERE TxnDate >= '2026-01-01' AND Status != 'Closed'

-- AR Aging
SELECT CustomerRef, SUM(Balance) as TotalDue
FROM Invoice
WHERE Balance > 0
GROUP BY CustomerRef

-- Revenue MTD
SELECT SUM(TotalAmt) as Revenue
FROM Invoice
WHERE TxnDate >= '2026-01-01' AND TxnDate <= '2026-01-31'

-- Payments This Week
SELECT PaymentRefNum, CustomerRef, TotalAmt, TxnDate
FROM Payment
WHERE TxnDate >= '2026-01-15' AND TxnDate <= '2026-01-21'
```

## Special Cases

### Multi-Location Jobs
- Create separate QB Customer per property address
- Link via ParentRef or Notes: "Property for {main customer}"

### Recurring Treatments
- Create RecurringInvoice in QB for monthly maintenance
- Link to parent job via Notes

### Change Orders
- Update existing Estimate (sparse update)
- Or create new Estimate with parent reference
- Track in CRM with parent_job_id

## Validation Rules
1. Every line item must have ItemRef (pre-created service items)
2. Amounts must match: Sum(Line.Amount) = TotalAmt
3. CustomerRef must exist (create if missing)
4. Deposit ≤ TotalAmt
5. DueDate ≥ TxnDate
6. ExpirationDate ≥ TxnDate (estimates)