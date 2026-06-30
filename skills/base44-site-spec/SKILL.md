---
name: base44-site-spec
description: "Architecture and content spec for rebuilding a small business website on Base44. NOT a deploy tool — Base44 is a no-code drag-and-drop builder with no agent-accessible CLI. Use this as a planning reference for page structure, copy, estimator widget HTML, SEO requirements, and DNS pitfalls when rebuilding a site on Base44."
---

# Base44 Site Specification

> ⚠️ **This is a planning/specification document, not a deployable skill.**
> Base44 is a no-code website builder (app.base44.com). There is no CLI the
> agent can call to build or deploy. This skill exists as a reference for the
> human building the site in the Base44 web interface. The agent's role in the
> Base44 flow was paying for the subscription (via stripe-link-cli), not
> deploying the site.

## When to Use
- Planning a website rebuild on Base44 (no-code platform)
- Reference for page structure, copy, estimator widget HTML, SEO requirements
- DNS migration notes (GoDaddy → Base44)
- NOT for automated deployment — Base44 has no agent-accessible CLI

## Prerequisites
- Base44 account (app.base44.com) — manual signup, manual site building
- GoDaddy DNS access for domain connection
- Payment via stripe-link-cli skill (agent handles the spend, human handles the build)

## Example Website Status
- Domain: yourdomain.com
- Platform: WordPress (broken — Services page 404s, blog dead since 2024)
- DNS: GoDaddy
- Hosting: Unknown (likely GoDaddy shared hosting)
- Action needed: Full rebuild on Base44 (manual, in web interface)

## Subscription & Pricing
- Pricing tiers and plan details: see `references/base44-pricing.md` (retrieved June 2026)
- Base44 does NOT support MPP — to purchase a subscription, use the Link CLI virtual card flow (`--credential-type card`) and complete checkout at app.base44.com via browser automation
- Recommended plan: **Pro ($80/mo)** for domain connection, GitHub integration, and sufficient credits for active development
- See the `stripe-link-cli` skill for the full spend-request → virtual card → checkout flow

## Website Architecture

> **Build prompt:** The full Base44 site build prompt with design system, page-by-page specs,
> real estimator pricing logic, and SEO requirements is saved at a local path.
> Use it as the source of truth when building or updating the site — it carries the
> current region mapping, rate-card logic, copy tone, and all page specs.

### Pages Needed
1. **Home** — Hero image, value proposition, CTA "Get Free Estimate"
2. **Services** — Service process explained
3. **Service Area** — Regions served (config-driven)
4. **Estimator** — Interactive form: sqft, region, property type -> instant quote
5. **About** — Owner story, technology explanation
6. **Contact** — Form that creates CRM lead, or phone/email direct
7. **Blog** — SEO content (service tips, referral resources)
8. **Thank You** — After estimate form submission

### Estimator Tool Integration
The estimator page should call the estimator-engine pricing logic:
- Input: square footage, region (Standard vs Premium), property type (Res/Comm/Apartment)
- Optional add-ons: Pet/Trauma, Surface Defense, Cigarette >5yrs, High Rise
- Output: Price range and "Schedule Service" CTA
- On submit: Create lead in CRM, send notification email to the owner

## Manual Deployment (Base44 Web Interface)

1. Log in to app.base44.com
2. Open your project
3. Build pages using drag-and-drop editor
4. Connect custom domain (yourdomain.com) in Settings > Domains
5. Click "Publish"

### DNS Configuration (GoDaddy)
```
Type: CNAME
Name: www
Value: sites.base44.com (or as specified by Base44)

Type: A
Name: @
Value: [Base44-provided IP]

Type: CNAME
Name: estimator
Value: sites.base44.com
```

## Estimator Form (Embedded Widget)

If Base44 supports custom code blocks, embed this HTML for the estimator:

```html
<div id="estimate-calculator">
  <h3>Get Your Instant Quote</h3>
  <select id="region">
    <option value="standard">Standard Region</option>
    <option value="premium">Premium Region (travel surcharge applies)</option>
  </select>
  <select id="property_type">
    <option value="residential">Residential</option>
    <option value="commercial">Commercial</option>
    <option value="apartment">Apartment</option>
  </select>
  <input type="number" id="sqft" placeholder="Square footage" />
  <div id="addons">
    <label><input type="checkbox" id="pet_trauma" /> Pet/Trauma</label>
    <label><input type="checkbox" id="surface_defense" /> Surface Defense</label>
    <label><input type="checkbox" id="cigarette_5yr" /> Cigarette >5yrs</label>
  </div>
  <button onclick="calculateEstimate()">Get Quote</button>
  <div id="result"></div>
</div>
```

The form should POST to an API endpoint or Hermes webhook that:
1. Runs the estimator-engine pricing logic
2. Returns a price
3. Creates a lead in CRM
4. Sends email notification to the owner

## Content Guide

### Home Page Copy (example template)
```
[BUSINESS_NAME]
[Service Description] — Guaranteed

[Technology/process description]

Serving [SERVICE_AREA_COUNT] regions across [STATE/AREA].
Get your free estimate in 60 seconds.
```

### Services Page Copy (example template)
```
Our Process:
1. Inspection & Assessment — Identify issue and severity
2. Treatment — [Treatment process description]
3. Surface Defense — Optional protective coating for lasting results
4. Verification — We confirm results before leaving

Technology: [Describe the technology/approach your business uses]
```

### Service Area (example template)
```
Standard Region: [YOUR LOCAL AREA/CITIES]
Premium Region: [YOUR EXTENDED AREA/CITIES] (travel surcharge applies)
```

## Common Pitfalls
- **WordPress backup**: Export existing WordPress content before switching DNS
- **DNS propagation**: Can take 24-48 hours for DNS changes to take effect
- **SSL certificate**: Base44 should provide SSL — verify HTTPS works after deploy
- **Email routing**: Changing DNS/A records can break email if MX records aren't preserved
- **Mobile responsive**: Verify site looks good on phones (most leads come from mobile)
- **Form spam**: Add basic spam protection (honeypot field, rate limiting)
- **SEO redirects**: Set up 301 redirects from old WordPress URLs to new Base44 pages
- **GoDaddy DNS vs hosting**: DNS is at GoDaddy, but hosting moves to Base44 — don't cancel GoDaddy DNS
- **Region classification sync**: If you update regions in `estimator-engine`, update the region
  options in the embedded estimator HTML above AND in any Base44 site build prompt. All three
  must match: `estimator-engine/SKILL.md` Location Tiers → `base44-site-spec` estimator HTML →
  Base44 site estimator widget. The canonical source is `estimator-engine`.
- **Contact form cutover risk**: The current WordPress contact form goes to the owner's inbox
  and works. Do NOT cut over DNS to the new Base44 site until the new contact form is verified
  to deliver to the same inbox (or to the agent). Breaking a working lead path mid-sprint is
  worse than keeping the old site live.
- **Browserless box**: The agent box has no Chromium. The agent can issue a Link CLI virtual card
  and hand off the card details, but cannot drive a browser checkout at app.base44.com. Plan for
  manual checkout or install Chromium first (`npx playwright install --with-deps chromium`).
- **Server-rendered HTML**: Confirm Base44 outputs server-rendered/static HTML, not client-only JS.
  Search engines index server-rendered content better. If Base44 is SPA-only, that's a strike
  against it for SEO — flag for review before going live.

## Verification Checklist
- [ ] Base44 account created
- [ ] All 8 pages built and published
- [ ] Estimator form functional and calculating correct prices
- [ ] Form submissions create CRM leads
- [ ] Custom domain connected (yourdomain.com)
- [ ] DNS propagated (check with `dig yourdomain.com`)
- [ ] SSL/HTTPS working
- [ ] Mobile responsive verified
- [ ] Old WordPress URLs have 301 redirects
- [ ] Email MX records preserved (don't break email)
- [ ] Google Analytics or basic analytics connected
- [ ] Services page loads without 404 (the old broken page)