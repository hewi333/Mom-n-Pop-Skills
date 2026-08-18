# JobTread API Setup

## Overview
JobTread uses a custom query language called **Pave** (similar to GraphQL) for their API. This guide walks through getting access and setting up the integration.

If you use a different construction PM system (Procore, Buildertrend, CoConstruct), the pattern is the same — adapt the query language and endpoints to your system.

## API Details

- **Endpoint:** `POST https://api.jobtread.com/pave`
- **Auth:** Grant keys (not API keys — different system)
- **Query Language:** Pave (not GraphQL, but similar structure)
- **Content-Type:** application/json
- **Grant keys expire after 3 months of inactivity**

## Step 1: Get Your Grant Key

1. Log into JobTread: https://app.jobtread.com
2. Go to **Settings → Integrations → API** (or the "grant management page")
3. Either copy an existing grant key OR create a new one:
   - Click **Create Grant** (or similar)
   - Copy the grant key **immediately** — it's only shown once
4. Add to `~/.hermes/.env`:
   ```bash
   JOBTREAD_GRANT_KEY=your_grant_key_here
   ```

## Step 2: Get Your Organization ID

```bash
cd ~/.hermes/skills/construction-agent/scripts
python3 jobtread_pave.py org
```

This returns your organization ID. Add it to `.env`:
```bash
JOBTREAD_ORG_ID=your_org_id_here
```

## Step 3: Test the Connection

```bash
# List projects
python3 jobtread_pave.py projects

# List accounts (customers/vendors)
python3 jobtread_pave.py accounts
```

## Pave Query Language

Pave is NOT GraphQL, but it's similar. Key differences:

### Basic Structure
```yaml
# Inputs go after the $ symbol
createAccount:
  $:
    name: Test Name
    type: customer
  createdAccount:
    id: {}
    name: {}
```

### Querying
```yaml
# Query by ID
account:
  $:
    id: "ACCOUNT_ID"
  id: {}
  name: {}
  type: {}
```

### Connection Fields (lists)
```yaml
# List all accounts in an organization
organization:
  $:
    id: "ORG_ID"
  accounts:
    nodes:
      id: {}
      name: {}
      type: {}
```

### Empty braces = "give me this field"
`{}` means "return this field's value"

## File Uploads

File uploads to JobTread may require a two-step process:
1. Request a pre-signed upload URL
2. Upload the file to that URL
3. Confirm the upload

The exact mutation structure should be verified in the API Explorer:
https://app.jobtread.com/docs

## Webhooks

JobTread supports webhooks for real-time events:
- File uploads
- Task updates
- Customer creation
- Other significant actions

To configure:
1. Go to the **Webhooks page** in JobTread
2. Set the webhook URL to your agent's endpoint
3. Select events to monitor

**Note:** Webhooks require a publicly accessible endpoint. If using Tailscale-only, you'll need a Tailscale Funnel or a public proxy.

## Grant Key Expiration

- **Grant keys expire after 3 months of inactivity**
- The daily briefing cron job keeps the key active by making API calls
- If the key expires, create a new one in the JobTread settings
- Update `~/.hermes/.env` with the new key

## API Explorer

Interactive API Explorer: https://app.jobtread.com/docs

Use this to:
- Browse the full schema
- Test queries before putting them in scripts
- Discover available fields and operations
- Find the correct mutation names for file uploads

## Troubleshooting

**"Grant key invalid":** Key may have expired. Create a new one in JobTread settings.

**401 Unauthorized:** Check that the grant key is correctly set in environment.

**Empty results:** Verify your organization ID is correct. Run `org` command to confirm.