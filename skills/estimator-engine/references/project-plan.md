# Project Plan — Reference for Estimator Engine

> ⚠️ **SUPERSEDED PRICING:** The pricing model in this file is the *original rough estimate*
> and is NO LONGER VALID. The confirmed rate card lives directly in `SKILL.md` under
> "Pricing Model" / "Configuration" — use that for all calculations. This file is kept only
> for historical context about the business profile, lead sources, and integration points.
>
> **Canonical pricing source:** `SKILL.md` → Configuration section — Standard and Premium
> Region tables, add-on surcharges, apartment flat rates, minimums. Do NOT use the rates below.

This reference captures the business context, original pricing approximation, and
integration requirements. Pricing has since been confirmed and updated in SKILL.md.

## Business Profile (Example)

- **Company**: [BUSINESS_NAME] — service business
- **Owners**: [OWNER_NAME] (ops/field) & [OWNER_NAME] (marketing/relationships) — non-technical
- **Service Area**: Multiple regions: [REGION_1], [REGION_2] (Standard) +
  [PREMIUM_REGION_1] (Premium / further travel)
- **Avg Job**: $2,000–3,000 (priced by sqft)
- **Lead Sources**: ~80% referrals (seasonal turnover), some Google, insurance = unreliable
- **Current Stack**: Microsoft Outlook, QuickBooks invoicing, **no CRM**, no Stripe
- **Website**: yourdomain.com — WordPress (being rebuilt on Base44)
- **Contact List**: ~2,000 contacts in Mailchimp, unused

## Travel Surcharges (historical — confirmed rates now in SKILL.md)
| Zone | Regions | Surcharge |
|------|----------|-----------|
| Zone 1 (local) | [REGION_1], [REGION_2] | $0 |
| Zone 2 | [REGION_3] | TBD |
| Zone 3 | [PREMIUM_REGION_1] | TBD |
| Zone 4 | [PREMIUM_REGION_2] | TBD + mileage + hotel |

Note: Travel surcharges are now baked into the Standard vs Premium pricing differential
in SKILL.md.

## Integration Points

### With CRM-Lite
- Estimator creates estimate records in CRM
- CRM stores: estimate_number, line_items, status, sent_date, accepted_date
- Weekly report cron queries estimator data

### With QuickBooks Online
- Estimator outputs QB-ready line items
- QB skill creates estimate in QuickBooks
- QB skill syncs estimate status back to CRM

### With Stripe
- Estimator total → Stripe Payment Link for deposit
- Stripe webhook → updates CRM estimate status

### With Website (Base44)
- Web form POST → estimator → returns ±15% range
- Form captures lead info → CRM lead record
- Full build prompt at a local path (see your project documentation)

## Key Files & Links
- Website: https://yourdomain.com/
- Build prompt: see your project documentation
- Game plan: see your project documentation
- Blocker log: see your project documentation