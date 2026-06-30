# GoDaddy Workspace Email — Himalaya IMAP/SMTP Setup

## Background
Business email (`owner@yourdomain.com`) is hosted through **GoDaddy Workspace
Email** (GoDaddy's own IMAP/SMTP hosting), NOT Microsoft 365. The owner uses the Outlook
desktop app as an IMAP client, but the mailbox lives on GoDaddy's servers.

Diagnostic: Try signing in at portal.azure.com with the business email — if it
returns "account not found," the email is NOT on M365. GoDaddy webmail shows
the mailboxes under My Products > Email.

## GoDaddy IMAP/SMTP Settings

| Protocol | Host | Port | Encryption |
|----------|------|------|------------|
| IMAP (incoming) | `imap.secureserver.net` | 993 | TLS |
| SMTP (outgoing) | `smtpout.secureserver.net` | 465 | TLS |

## Himalaya CLI Setup

### Install
```bash
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh
```

### Config: `~/.config/himalaya/config.toml`
```toml
[accounts.business]
email = "owner@yourdomain.com"
display-name = "[OWNER_NAME] - [BUSINESS_NAME]"
default = true

backend.type = "imap"
backend.host = "imap.secureserver.net"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "owner@yourdomain.com"
backend.auth.type = "password"
backend.auth.cmd = "cat ~/.config/himalaya/.email-pw"

message.send.backend.type = "smtp"
message.send.backend.host = "smtpout.secureserver.net"
message.send.backend.port = 465
message.send.backend.encryption.type = "tls"
message.send.backend.login = "owner@yourdomain.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "cat ~/.config/himalaya/.email-pw"

folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

### Password
Store in `~/.config/himalaya/.email-pw` (chmod 600). GoDaddy webmail login uses a
numeric login ID, but IMAP/SMTP auth uses the full email address as the login.

## Verified Commands

### Read inbox
```bash
export PATH="$HOME/.local/bin:$PATH"
himalaya envelope list --page 1 --page-size 20
himalaya envelope list --output json  # structured for agent parsing
```

### Read a specific email
```bash
himalaya message read 29047
```

### Save draft to Drafts folder (DO NOT SEND)
```bash
cat << 'EOF' | himalaya message save --folder Drafts
From: owner@yourdomain.com
To: customer@example.com
Subject: Your [BUSINESS_NAME] Estimate

Email body here.
EOF
```

**IMPORTANT:** The command is `himalaya message save --folder Drafts`, NOT
`himalaya template save`. The `template save` subcommand does not exist. Using
it will fail silently or error.

### Send email (ONLY after owner approval)
```bash
cat << 'EOF' | himalaya template send
From: owner@yourdomain.com
To: customer@example.com
Subject: Your [BUSINESS_NAME] Estimate

Email body here.
EOF
```

### Reply to an existing thread (preserve headers)
```bash
# Generate reply template from original message
himalaya template reply 29047 > /tmp/reply.tpl
# Edit /tmp/reply.tpl to add your reply body
# Then save as draft:
cat /tmp/reply.tpl | himalaya message save --folder Drafts
# Or send after approval:
cat /tmp/reply.tpl | himalaya template send
```

Do NOT compose a fresh email for a thread reply — it breaks `In-Reply-To` and
`References` headers, and the customer won't see it as part of the conversation.

### List drafts (verify draft was saved)
```bash
himalaya envelope list --folder Drafts
```

## Why Not Microsoft Graph / outlook-graph Skill

- Business email hosted on GoDaddy Workspace Email, not M365
- Microsoft login returns "account not found" for the business email
- The `outlook-graph` skill (Azure AD app registration, client credentials flow) does
  not apply for GoDaddy-hosted email
- `outlook-graph` is kept as a separate skill for businesses
  with real M365 tenants that will need it

## What's NOT Available via IMAP

- **Calendar** — No Microsoft Graph calendar API. Would need a separate integration
  (Google Calendar, CalDAV, or manual)
- **Contacts** — No Microsoft Graph contacts API. Would need a separate solution
- Email is the core path; calendar/contacts are optional extensions