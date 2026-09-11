# Base44 Pricing Tiers

Retrieved June 25, 2026 from https://base44.com/pricing.

**Note:** The pricing page is a Wix-rendered SPA — plain `curl` returns JS-rendered HTML without visible pricing. To extract prices, pipe the HTML through a text extractor (strip `<script>`/`<style>` tags, then regex for `$\d+` patterns). Prices may change; verify before purchasing.

## Plans (billed annually)

| Plan | Price/mo | Message Credits | Integration Credits | Key Features |
|------|----------|-----------------|---------------------|--------------|
| Free | $0 | 25/mo | 100/mo | Core features, auth, database, analytics |
| Starter | $16/mo | 100/mo | 2,000/mo | Unlimited apps, in-app code edits, backend functions |
| Builder | $40/mo | 250/mo | 10,000/mo | All Starter + AI model select, connect domain |
| Pro | $80/mo | 500/mo | 20,000/mo | All Builder + free domain 1yr, GitHub, beta access |
| Scale | $160/mo | 1,200/mo | 50,000/mo | All Pro + premium support |

## All paid plans include
- Unlimited number of apps
- In-app code edits
- Backend functions
- Connect a domain

## Pro+ additions
- Free domain for 1 year
- 25 credits to share with a friend
- GitHub integration
- Early access to beta features
- Premium support (Scale only)

## For a Small Business Website
- **Builder ($40/mo)** is the minimum viable plan — need domain connection for yourdomain.com
- **Pro ($80/mo)** recommended — free domain for 1yr, GitHub integration for version control, more credits for active development
- Base44 does NOT support MPP (Machine Payment Protocol) — purchases must use the Link CLI virtual card flow (`--credential-type card`), not SPT

## Purchasing via Link CLI
Base44 has a standard web checkout at app.base44.com — use the `card` credential type:
```
link-cli spend-request create \
  --credential-type card \
  --payment-method-id <pm_id> \
  --merchant-name "Base44" \
  --merchant-url "https://app.base44.com" \
  --amount <cents> \
  --context "<100+ chars: purchasing Base44 <plan> subscription for small business website rebuild>" \
  --line-item "name:Base44 <Plan> Annual,unit_amount:<cents>,quantity:1" \
  --total "type:total,display_text:Total,amount:<cents>" \
  --request-approval
```
After approval, retrieve the virtual card and use browser automation to complete checkout at app.base44.com. See `stripe-link-cli` skill for full flow.