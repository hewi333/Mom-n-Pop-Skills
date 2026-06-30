---
name: marketing-campaign-builder
description: "Draft and run Mailchimp email campaigns with AI-generated content, subject line A/B testing, and optimal send timing. Agent drafts the email + subject variants, owner approves in Telegram, agent creates the campaign in Mailchimp. Turns a dormant contact list into an active marketing channel."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mailchimp, marketing, ab-testing, campaigns, email, small-business]
    related_skills: [mailchimp-integration, crm-lite, lead-to-payment]
---

# Marketing Campaign Builder

## Overview
Most small businesses have a Mailchimp list they never use. They sent a few
campaigns years ago, got busy, and stopped. This skill fixes that by making
campaign creation **fast and owner-gated**:

1. Owner texts a campaign idea in Telegram
2. Agent drafts the email content + 2-3 subject line options
3. Owner picks a subject line (or suggests their own)
4. Agent creates an A/B test campaign in Mailchimp
5. Agent sends a test email to the owner
6. Owner approves → agent schedules the send at optimal time

**The owner never writes HTML, never logs into Mailchimp, never touches a
template editor.** They just describe what they want and approve the draft.

## When to Use
- "Send a summer special to all partners"
- "We haven't emailed the list in 3 months — draft a re-engagement campaign"
- "Send a seasonal reminder to all contacts in our service area"
- "Create a campaign about our new website estimator tool"
- "Send a holiday thank you to all customers"

## Prerequisites
- `mailchimp-integration` skill installed + API key wired
- MAILCHIMP_AUDIENCE_ID set in environment
- Owner available in Telegram to approve drafts

## The Flow

### Step 1: Owner Describes the Campaign
Owner sends a message in Telegram:
> "Send a summer special to all partners — mention our partner pricing
> and that we do free estimates."

Agent extracts:
- **Audience segment:** "partners" (or "all contacts" if not specified)
- **Topic:** summer special
- **Key points to include:** partner pricing, free estimates
- **Tone:** matches the business (confident, professional, not salesy)

### Step 2: Agent Drafts Content + Subject Lines
Agent generates:
- **2-3 subject line options** (short, punchy, under 50 chars for mobile)
- **Preview text** (the snippet recipients see next to subject)
- **Email body** in HTML, matching the business brand voice
- **Plain text version** (for accessibility + spam filters)

Example output to owner in Telegram:
```
📧 Campaign Draft — Summer Partner Special

Subject line options:
A) "Summer Listings? Don't Let Odors Kill the Sale"
B) "Free Estimates for Your Summer Listings"
C) "Partner Special: Summer Service Discount"

Preview text: "[BUSINESS_NAME] — professional service for your
listings. Free estimates, partner pricing."

Body: [shows first few lines or summary]

Which subject line do you prefer? (A, B, or C — or type your own)
```

### Step 3: Owner Picks Subject Line
Owner replies: "A" or "B" or "C" or types their own:
> "Make it 'Protect Your Summer Listings from Odors'"

Agent updates the draft with the chosen subject line.

### Step 4: Agent Creates Campaign in Mailchimp

#### Regular (single variant) Campaign
```bash
source ~/.hermes/.env

# Create campaign
CAMPAIGN=$(curl -s -X POST "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/campaigns" \
  --user "anystring:$MAILCHIMP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "regular",
    "recipients": {
      "list_id": "'"$MAILCHIMP_AUDIENCE_ID"'",
      "segment_opts": {
        "saved_segment_id": SEGMENT_ID
      }
    },
    "settings": {
      "subject_line": "Summer Listings? Don'"'"'t Let Odors Kill the Sale",
      "preview_text": "[BUSINESS_NAME] — professional service for your listings.",
      "title": "Summer Partner Special - June 2026",
      "from_name": "[BUSINESS_NAME]",
      "reply_to": "owner@yourdomain.com",
      "to_name": "*|FNAME|*"
    },
    "tracking": {
      "opens": true,
      "html_clicks": true
    }
  }')

CAMPAIGN_ID=$(echo "$CAMPAIGN" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

#### A/B Test (Variate) Campaign
```bash
# Create A/B test campaign testing two subject lines
CAMPAIGN=$(curl -s -X POST "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/campaigns" \
  --user "anystring:$MAILCHIMP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "variate",
    "recipients": {
      "list_id": "'"$MAILCHIMP_AUDIENCE_ID"'"
    },
    "variate_settings": {
      "winning_combination": "opens",
      "wait_time": 6,
      "test_size": 50,
      "test_segments": [
        {"segment_text": "Subject A"},
        {"segment_text": "Subject B"}
      ],
      "subject_lines": [
        "Summer Listings? Don'"'"'t Let Odors Kill the Sale",
        "Protect Your Summer Listings from Odors"
      ]
    },
    "settings": {
      "title": "Summer Partner Special A/B - June 2026",
      "from_name": "[BUSINESS_NAME]",
      "reply_to": "owner@yourdomain.com",
      "to_name": "*|FNAME|*"
    }
  }')
```

### Step 5: Set Campaign Content
```bash
curl -s -X PUT "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/campaigns/$CAMPAIGN_ID/content" \
  --user "anystring:$MAILCHIMP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<html><body>...campaign HTML...</body></html>",
    "plain_text": " plain text version..."
  }'
```

### Step 6: Send Test to Owner
```bash
curl -s -X POST "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/campaigns/$CAMPAIGN_ID/actions/test" \
  --user "anystring:$MAILCHIMP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "test_emails": ["owner@yourdomain.com"],
    "send_type": "html"
  }'
```

Agent tells owner: "Test email sent — check your inbox. Reply 'send' to send
to the full list, or tell me what to change."

### Step 7: Owner Approves → Send or Schedule

**Send immediately:**
```bash
curl -s -X POST "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/campaigns/$CAMPAIGN_ID/actions/send" \
  --user "anystring:$MAILCHIMP_API_KEY"
```

**Schedule for optimal time:**
```bash
# Schedule for Tuesday 10am ET (best open rate for B2B per industry data)
curl -s -X PATCH "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/campaigns/$CAMPAIGN_ID" \
  --user "anystring:$MAILCHIMP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": {
      "schedule_time": "2026-07-07T14:00:00+00:00"
    }
  }'
```

## Email Content Guidelines

### Brand Voice
- **Confident, not salesy** — "This works. Here's why." not "BUY NOW!!!"
- **Professional but warm** — like a trusted local business, not a corporation
- **Short paragraphs** — 2-3 sentences max, lots of white space
- **One clear CTA** — "Get a Free Estimate" or "Call [PHONE]"
- **Mobile-first** — 60%+ of recipients read on phones

### Email Structure Template
```html
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">

<!-- Header with logo -->
<img src="LOGO_URL" alt="[BUSINESS_NAME]" style="max-width: 200px; margin-bottom: 20px;">

<!-- Headline -->
<h1 style="color: #0C71C3; font-size: 24px;">HEADLINE HERE</h1>

<!-- Body copy -->
<p style="font-size: 16px; line-height: 1.6; color: #1A1A1A;">
BODY COPY HERE — 2-3 short paragraphs
</p>

<!-- CTA button -->
<a href="CTA_URL" style="display: inline-block; background: #0C71C3; color: white;
   padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;
   margin: 20px 0;">Get Your Free Estimate</a>

<!-- Footer -->
<hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
<p style="font-size: 12px; color: #888;">
[BUSINESS_NAME] | [SERVICE_DESCRIPTION] | [PHONE]<br>
Serving [SERVICE_AREA]<br>
<a href="*|UNSUB|*">Unsubscribe</a> | <a href="*|UPDATE_PROFILE|*">Update Preferences</a>
</p>

</body>
</html>
```

### Subject Line Best Practices
- Under 50 characters (mobile cuts off longer)
- Create curiosity or urgency without being clickbait
- Personalization with *|FNAME|* works but don't overuse
- Test questions vs statements vs benefits
- Examples that work:
  - "Summer Listings? Don't Let Odors Kill the Sale"
  - "*|FNAME|*, Free Estimates for Your Spring Listings"
  - "Seasonal Prep: Is Your Property Protected?"
  - "The Guarantee Real Estate Agents Trust"

## A/B Testing Strategy

### What to Test (in priority order)
1. **Subject lines** — biggest impact on open rates
2. **Send time** — Tuesday/Wednesday 10am-12pm ET typically wins for B2B
3. **From name** — "[OWNER_NAME] @ [BUSINESS_NAME]" vs "[BUSINESS_NAME]" vs a campaign name
4. **Preview text** — the snippet next to subject in inbox
5. **CTA** — "Get Free Estimate" vs "See Pricing" vs "Call Now"

### Mailchimp A/B Test Setup
- Test size: 50% (send to 50% of list, 25% each variant, winner goes to remaining 50%)
- Winning condition: opens (for subject line tests), clicks (for content tests)
- Wait time: 6 hours (enough for a meaningful pattern, not so long it delays)
- Don't over-test — 2 variants is plenty for a small business list

### Campaign Timing Recommendations
| Day | Time (ET) | Why |
|-----|-----------|-----|
| Tuesday | 10:00am | Best overall open rate for B2B |
| Wednesday | 10:00am | Second best, avoids Monday noise |
| Thursday | 2:00pm | Good for consumer-focused campaigns |
| Avoid | Monday/Friday | Buried in weekend cleanup or pre-weekend rush |
| Avoid | Weekends | B2B recipients don't check |

## Segmentation Strategy

### Before Sending, Agent Checks Available Segments
```bash
# List existing segments
curl -s --user "anystring:$MAILCHIMP_API_KEY" \
  "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/lists/$MAILCHIMP_AUDIENCE_ID/segments"
```

### If No Segments Exist, Agent Creates Them
Useful default segments for small businesses:
- **Active subscribers** — opened an email in the last 90 days
- **Partners/Referrers** — tagged "partner" (if tags exist)
- **By region** — merge field REGION = specific region
- **Engaged** — clicked a link in the last 60 days
- **Cold** — no opens in 180 days (re-engagement target)

## Campaign Report (Post-Send)
After a campaign sends (wait 48 hours), agent can pull the report:
```bash
curl -s --user "anystring:$MAILCHIMP_API_KEY" \
  "https://$MAILCHIMP_SERVER_PREFIX.api.mailchimp.com/3.0/reports/$CAMPAIGN_ID" | python3 -m json.tool
```

Agent summarizes for owner in Telegram:
```
📊 Campaign Report — "Summer Partner Special"
Sent to: 1,500 contacts
Opens: 542 (30%) — above industry avg (21%)
Clicks: 28 (1.5%)
Unsubscribes: 3
Best segment: Standard Region (42% open rate)
```

## Agent Integration Patterns

### Pattern 1: Seasonal Campaign
Owner: "Send a seasonal campaign to all contacts"
Agent: Drafts content about seasonal prep + prevention → subject lines →
owner picks → test send → owner approves → scheduled for Tuesday 10am

### Pattern 2: Partner Re-engagement
Agent detects (via CRM) that 12 partners haven't sent a lead in 6 months.
Agent: Drafts a "We miss you" campaign targeted to cold partner segment →
owner approves → send → track who re-engages → update CRM

### Pattern 3: Post-Job Review Request
Job completes. Agent: Drafts a campaign asking the customer for a Google review
with a direct link → owner approves → send to that one customer (not a bulk send)

### Pattern 4: Content from CRM Data
Agent: "You booked 8 jobs from Standard Region partners this quarter — want me to
draft a 'Standard Region Partner Thank You' campaign?" Owner: "Yes" → agent drafts.

## Common Pitfalls

1. **Don't send without a test.** Always send a test to the owner first.
   One wrong link or typo to 1,800 people can't be undone.
2. **Don't forget the unsubscribe footer.** CAN-SPAM requires it. Mailchimp
   adds it automatically with `*|UNSUB|*` merge tag.
3. **Don't use too many images.** Many email clients block images by default.
   Text should carry the message; images are enhancement.
4. **Don't send on Friday afternoon.** Opens tank. Schedule for Tuesday-Wednesday.
5. **Don't A/B test everything at once.** Test one variable per campaign.
   Subject lines first. Then timing. Then content.
6. **Merge tags need exact match.** `*|FNAME|*` works only if the merge field
   tag is exactly FNAME. Check merge fields before using.
7. **From name consistency.** Don't change from "[BUSINESS_NAME]" to "[OWNER_NAME]"
   across campaigns — it hurts recognition. Pick one and stick to it.

## Verification Checklist
- [ ] Can create a regular campaign via API
- [ ] Can create a variate (A/B test) campaign via API
- [ ] Can set campaign content (HTML + plain text)
- [ ] Can send a test email to owner
- [ ] Can send or schedule a campaign
- [ ] Can pull campaign report (opens, clicks, unsubscribes)
- [ ] Can create segments by tag/region/engagement
- [ ] Owner approval workflow tested end-to-end

## One-Shot Recipes

### "Quick campaign: seasonal reminder"
```python
# Owner says: "Send a seasonal prevention tip to all contacts for summer"
# Agent drafts 3 short tips + CTA → creates campaign → test → owner approves → send
```

### "Re-engagement: cold contacts"
```python
# Agent identifies contacts with no opens in 180 days
# Creates segment "Cold - 180 days"
# Drafts "We miss you" campaign with special offer
# Owner approves → send → track re-engagement → update CRM
```

### "Monthly newsletter from CRM data"
```python
# Agent pulls: new leads, jobs booked, revenue this month
# Drafts "[BUSINESS_NAME] Monthly" newsletter with stats + customer spotlight
# Owner approves → send → track engagement
# Schedule as monthly cron job
```