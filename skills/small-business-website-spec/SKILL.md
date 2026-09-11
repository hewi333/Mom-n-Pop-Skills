---
name: small-business-website-spec
description: "Planning reference for rebuilding a small business website: page structure, copy voice, estimator widget, SEO requirements, form handling, DNS migration, and the no-code vs static-framework decision (Base44 vs Astro/Vercel vs WordPress). NOT a deploy tool for no-code platforms — no-code builders have no agent-accessible CLI. Includes the honest reasons we pivoted from no-code to a static framework."
version: "2.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [website, planning, base44, astro, vercel, no-code, seo, small-business]
    related_skills: [estimator-engine, grasshopper-voicemail-monitor, agent-cheatsheet-builder]
---

# Small Business Website Spec

> ⚠️ **This is a planning/specification reference, not a deployable skill for
> no-code platforms.** Base44 and similar builders have no CLI the agent can
> call — building there means dragging pages in a web editor, done by a human.
> A static framework (Astro/Hugo/Eleventy) on Vercel/Netlify/Cloudflare Pages
> *is* agent-workable: the agent can clone the repo, edit, run checks, and push.
> Either way, this skill is the spec: page structure, copy voice, estimator
> widget, SEO checklist, form handling, and the DNS cutover runbook.

## When to Use
- Planning a website rebuild for a small service business
- Choosing between no-code (Base44, Wix Studio, Squarespace) and a static framework (Astro on Vercel)
- Page structure, copy voice, estimator widget, SEO requirements
- DNS migration notes (registrar → new host)
- Wiring contact-form submissions into the agent (email → IMAP polling → CRM → Telegram)
- NOT for automated no-code deployment — no agent-accessible CLI exists there

## Platform Decision: No-Code vs Static Framework

Both paths are valid. Pick by workload, not by hype:

| Factor | No-code (Base44 etc.) | Static framework (Astro/Vercel etc.) |
|---|---|---|
| Who builds it | Human, in a web editor (drag-and-drop) | Human or AI coding agent, in a repo |
| Time to first draft | Hours | Days |
| Monthly cost | ~$50/mo for domain connection + GitHub sync on Builder-tier plans | $0 on Vercel/Netlify free tiers (or an existing plan) |
| SEO | Prerendering exists but is often a black box you can't control | Static HTML — fully crawlable, you own everything |
| Export/exit | Frontend only; backend (auth, DB, entities) stays on the platform SDK — you can't self-host by exporting | It's your repo. Portable by definition. |
| Site types that fit | Interactive apps, member areas, anything needing a real backend | Marketing sites: pages + one estimator widget + one contact form |
| Mutability | A living app on their platform — platform updates can change rendering without you touching anything | An immutable build artifact on CDN edge — it can't break while untouched |
| Agent's role | Paying for the subscription (via stripe-link-cli) and writing the spec — not the build | Full repo work: edit, test, verify, push, deploy |

**How to choose:** if the site needs user accounts, database writes, or complex
app behavior, no-code (or a real framework with a backend) earns its subscription.
If it's a marketing site — pages, photos, an estimator widget, a contact form —
a static build is cheaper, faster to load, better for SEO, and fully agent-workable.

We started on Base44 (for a hackathon "the agent bought the subscription" beat,
which is what `stripe-link-cli` is for), then pivoted to Astro-on-Vercel for the
production site because a static marketing site had zero backend needs. The
pivot itself was cheap **because the spec (this document) was written before
either build** — page inventory, copy voice, estimator logic, and SEO checklist
all carried over unchanged.

## Prerequisites
- Domain at a registrar (GoDaddy or similar) — keep DNS there, repoint records
- Static path: git repo, framework (Astro recommended), hosting account (Vercel/Netlify)
- No-code path: builder account, manual signup + build in the web interface
- Form delivery: an email API (Resend/Postmark/SES) or SMTP — forms should email the owner's inbox
- Payment for no-code subscriptions via the `stripe-link-cli` skill (agent handles the spend, human handles the build)

## Website Architecture

### Pages needed (marketing site for a service business)
1. **Home** — hero image, value proposition, primary CTA ("Get Free Estimate"), estimator above the fold
2. **Service pages** — one per service line (built from a template route; each names the reader's exact situation in the first two sentences)
3. **Service area / location pages** — one per market city (template route, real local copy, not doorway spam)
4. **Realtors & property managers** — the B2B repeat-revenue page, if referrals drive the business
5. **About / Why Us** — owner story, process steps, trust signals, real photos
6. **Gallery** — real job photos, captioned
7. **FAQ** — include a "what makes you different from everyone else?" answer
8. **Contact** — form with estimator pre-fill flow
9. **Reviews** — embedded review widget (or hold back until the widget is wired)
10. **Thank you** — `noindex`, conversion event fires here
11. **Terms** — warranty/terms as a proper page (not a PDF scan)
12. **404**, plus `robots.txt`, `llms.txt` (for AI/agentic search), `sitemap-index.xml`

### Estimator tool integration
The estimator is the conversion hook AND the differentiator. Pricing logic
lives in ONE place (see `estimator-engine` skill; a `rate-card.json` both the
website widget and the agent read is the cleanest split).
- Input: square footage, region tier, property type (residential/commercial/apartment), add-ons
- Output: a **±15% range, never a single number**, never internal line-item math
- Flow: result → one tap → contact form pre-filled with all inputs + quoted range
- Mobile-first: thumb-reachable controls, ≤60 seconds, ≤8 taps
- **The website widget, the agent's chat estimator, and the rate-card file
  must all read from the same rate card.** If a price changes, change the rate
  card first; both consumers pick it up. Canonical source: `estimator-engine`.

### Contact form handler
- Serverless function (or the host's form feature) receives the POST
- Email API (Resend etc.) delivers to the **owner's inbox** — reply-to set to
  the submitter so the owner can hit Reply
- Honeypot spam field (hidden "company" input — if filled, reject silently)
- Validate: required core fields, plus "at least one of phone or email"
- Carrying estimator data into the form? Keep it as structured fields in the
  submission email — the agent's inbox monitor parses them (see below)
- Optional webhook to the agent — but see "Lead intake" before exposing one

### Lead intake (agent integration)
Two ways to get form submissions to the agent:

**A. IMAP polling (recommended default).** The form emails the owner's inbox
with a stable subject prefix (`New website lead: ...`) and a structured
plain-text body. A `no_agent=True` cron script polls the inbox every 3 min,
parses the fields, logs to CRM, and texts the owner's Telegram. Latency ~3 min
— irrelevant for a few leads a week. No public endpoint, nothing to attack.
Full pattern: `grasshopper-voicemail-monitor` skill and its notification-email
reference.

**B. Webhook (faster, more surface).** The form handler POSTs straight to an
agent endpoint. You get instant delivery but you must expose, secure, rate-
limit, and monitor a public URL on the agent box. Only worth it at volume.

Choose A unless leads/minute is a real metric for you. The webhook code can
stay in the form handler, dormant, if you want the option open.

## Content guide

### Copy voice
- **Premium-because-[your real differentiator]** — never "affordable,"
  "budget-friendly," "cheap" (they attract price-shoppers, not your buyers)
- Lead with the outcome (it works, it's guaranteed, it's permanent) — not the chemistry
- Name the reader's exact situation in the first 2 sentences of every service page
- Specificity = trust: real cities, real timeframes, real guarantee terms
- ~7th-grade reading level, short sentences

### Banned-word check
Add a verify-script check for cheap-sounding words: *affordable,
budget-friendly, cheap, competitive pricing, "we work with many budgets,"
best-in-class, world-class, "look no further."* Ban list lives in the repo and
runs in CI — banned words slip back in with every copy edit otherwise.

### Guarantee
If you advertise a guarantee, state its exceptions wherever the guarantee
appears — exceptions buried on a distant page erode trust and invite disputes.

## Common Pitfalls

- **Contact-form cutover risk:** the OLD site's form probably works and goes
  to the owner's inbox. Do NOT repoint DNS until the new form is **verified
  delivering to that same inbox** on a staging domain. Breaking a working
  lead path is worse than keeping the old site live another week.
- **DNS propagation:** 24-48h. Save old DNS values for instant rollback.
- **Email routing:** changing A/CNAME records is fine, but **MX records stay
  pointed at the email host** (e.g. Workspace: `imap.secureserver.net` /
  `smtpout.secureserver.net`). Repointing MX silently breaks the business's email.
- **Mobile-first:** most service-business leads come from phones. Test at
  320px, 375px, 414px widths.
- **301 redirects:** map old (especially WordPress) URLs → new pages before
  cutover, or years of accumulated SEO equity 404s overnight.
- **Banned words:** enforce via the verify script, not vigilance.
- **Terms & conditions:** a scanned-image PDF has no extractable text —
  transcribe it into a real page.
- **Stock photos:** verify licensing before a live launch; "we scraped them
  from our old site" is not a license.
- **Browserless agent box:** no-code checkout and Lighthouse audits need a
  browser. The agent can't drive a web UI without Chromium
  (`npx playwright install --with-deps chromium`); run audits via web tools.
- **Region classification sync:** if you update region tiers in
  `estimator-engine`, update the estimator widget options AND the rate-card
  file. All three must match. Canonical source: `estimator-engine`.
- **No-code export is a one-way door:** the frontend exports; the backend
  doesn't. If you start on no-code, treat it as a prototype — don't wire
  business logic (auth, DB, entities) into it that you'll have to rebuild.
- **Agent pushes to `main`:** for a 1-2 person shop, direct-push with a
  quality gate (tests + verify script) is faster than PR review. Whatever
  you choose, make it a written convention — agents follow conventions,
  they don't infer them.
- **GitHub PATs expire:** if the clone URL embeds a PAT, pushes fail
  mysteriously ~30 days later. Check the token's expiry when setting up,
  and note the `git remote set-url` fix before it bites.

## DNS Configuration (registrar → Vercel example)

```
Type: CNAME
Name: www
Value: cname.vercel-dns.com

Type: A
Name: @
Value: 76.76.21.21 (Vercel default)
```
(No-code hosts give you their own CNAME/A targets — same idea.)

**Do NOT touch MX records** — email stays with the email host.

Cutover order:
1. New contact form verified delivering to the owner's inbox (staging domain)
2. Owner sign-off on content + design
3. THEN repoint DNS
4. Old DNS values saved for instant rollback

## Verification Checklist

### Quality gate (automated — run before every push)
- [ ] Every page renders static HTML with copy in the raw HTML (no client-only content)
- [ ] Unique title (≤60 chars) + meta description (≤155 chars) per indexable page
- [ ] Exactly one H1 + substantial body copy per page
- [ ] Zero banned words (enforced by script)
- [ ] Estimator output matches the agent's chat estimator (same rate card, test N quotes)
- [ ] Guarantee caveats reachable from every page mentioning "guarantee"
- [ ] Structured data (LocalBusiness, Service, FAQPage) + tap-to-call on every page
- [ ] robots.txt, llms.txt, sitemap-index.xml present; /thank-you is noindex
- [ ] Unit tests pass (pricing engine + form validation)

### Pre-cutover (manual)
- [ ] Owner sign-off on the site
- [ ] Form submissions verified delivering to the owner's inbox on the real domain
- [ ] Schema.org validates (Google Rich Results Test)
- [ ] Lighthouse mobile: Performance ≥90, SEO ≥95, Accessibility ≥90
- [ ] Real photos on the site (machines/equipment/jobs, not stock)

### Post-cutover
- [ ] DNS propagated (`dig yourdomain.com`) + HTTPS working
- [ ] 301 redirects from old URLs live
- [ ] Email MX records preserved (don't break email)
- [ ] Search Console + Bing Webmaster verified; sitemap submitted
- [ ] Analytics events firing (estimator_start, estimator_complete, form_submit, call_click)
- [ ] Mobile responsive verified on real devices
- [ ] Lead-intake monitor (if used) picking up form submissions → CRM → Telegram