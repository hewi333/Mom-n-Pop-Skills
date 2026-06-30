---
name: stripe-link-cli
description: Agent payments via Stripe Link — cards, SPT, approvals.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Payments, Stripe, Link, Checkout, MPP]
    related_skills: [mpp-agent, stripe-projects]
---

# Stripe Link CLI Skill

Wraps [@stripe/link-cli](https://github.com/stripe/link-cli) so Hermes can complete purchases on the user's behalf using one-time-use virtual cards or Shared Payment Tokens (SPT). Every spend is gated by an in-app approval in the Link mobile/web app — Hermes cannot self-approve.

US-only at the moment (Link account requirement). Windows is not supported by the upstream CLI — this skill is gated `[linux, macos]`.

## When to Use

Trigger phrases:

- "buy X", "pay for X", "make a purchase", "complete checkout"
- "get me a card", "I need a payment method"
- "log in to Link", "connect my Link wallet"
- HTTP 402 response from a merchant API with `www-authenticate: ... method="stripe"`

If the user wants a paid API call (HTTP 402, no checkout form), the `card` path is wrong — use SPT via this same skill, or hand off to the `mpp-agent` skill.

## Prerequisites

- Node.js 20+ available on `PATH` (`node --version`)
- US-based (Link account requirement)

The Link account, payment method, and spend-approval app do NOT need to be set up before Hermes attempts to pay — the CLI walks the user through them on first run:

- A Link account at https://app.link.com — created/linked during first `link-cli` auth
- At least one payment method — added during first run at https://app.link.com/wallet
- The Link mobile/web app — opened to approve the first spend request when it's made

No env vars required — auth state is stored locally by the CLI under its own config directory.

## Install

Install once, globally:

```
npm install -g @stripe/link-cli
```

Or invoke ad-hoc via `npx @stripe/link-cli`. The skill below uses the installed `link-cli` form.

## How to Run

All commands run through the `terminal` tool. The CLI auto-detects non-TTY callers and emits compact `toon` output by default — fine for the model. Pass `--format json` if a step needs structured fields.

Discover commands: `link-cli --llms-full`.
Get a command's schema before invoking: `link-cli <command> --schema`.

## Procedure

### 1. Check / establish auth

```
link-cli auth status
```

If not authenticated, log in with a clear client name (this label shows in the user's Link app):

```
link-cli auth login --client-name "Hermes" --interval 5 --timeout 300
```

The `--interval`/`--timeout` form polls inline so the agent doesn't need to manage a `_next` step. Print the verification URL + phrase to the user and wait for the CLI to return.

**Background-polling pattern (when not using inline flags):** If you run `auth login` without `--interval`/`--timeout` (or with `pty=true`), it returns immediately with a `verification_url`, `phrase`, and a `_next.command` like `auth status --interval 5 --max-attempts 60`. Start that poll as a **background terminal process** with `notify_on_complete=true` so you get notified when the user approves:

```
link-cli auth status --interval 5 --max-attempts 60
# → run with: background=true, notify_on_complete=true, timeout=330
```

Print the verification URL and phrase to the user immediately — don't wait for them to ask. The background poll will notify you when auth succeeds.

**Do not proceed past this step until `auth status` confirms login.**

### 2. Evaluate the merchant before creating a spend request

Decide the credential type:

| Merchant surface | `--credential-type` |
|---|---|
| Standard web checkout form / Stripe Elements | `card` (default) |
| Returns HTTP 402 with `method="stripe"` in `www-authenticate` | `shared_payment_token` |
| Returns HTTP 402 without `method="stripe"` | unsupported — stop |

For 402 responses, do NOT decode the challenge manually. Pass the raw header:

```
link-cli mpp decode --challenge '<full WWW-Authenticate header>'
```

This validates the challenge and extracts the network ID + decoded request body.

### 3. List payment methods + shipping

```
link-cli payment-methods list
link-cli shipping-address list
```

Use the first entry unless the user specifies otherwise. The `id` from `payment-methods list` is the `--payment-method-id` in the next step.

### 4. Create the spend request

Confirm the final total with the user before issuing this command. Amounts are in cents.

```
link-cli spend-request create \
  --payment-method-id <pm_id> \
  --merchant-name "<name>" \
  --merchant-url "<url>" \
  --context "<what is being purchased and why — MUST be ≥100 characters or the CLI returns VALIDATION_ERROR too_small>" \
  --amount <cents> \
  --line-item "name:<item>,unit_amount:<cents>,quantity:1" \
  --total "type:total,display_text:Total,amount:<cents>" \
  --request-approval
```

For MPP merchants add `--credential-type shared_payment_token`.

`--request-approval` sends the approval push notification to the user's Link app and returns immediately with `status: "pending_approval"`. It does **NOT** poll — the response includes a `_next.command` (`spend-request retrieve <id> --interval 2 --max-attempts 300`) that you must run separately to poll for approval.

**Best pattern:** After `create --request-approval` returns, immediately start a **background** `retrieve` call that combines polling + card retrieval in one shot (see Section 5). This eliminates the gap between approval and retrieval that causes card expiry.

### 5. Retrieve the credential — SECURELY

**Do not print card details to stdout.** Use `--output-file` so the PAN never enters the agent's transcript or logs.

**All five options are required by the schema** even though they appear to have defaults — omitting any of `--timeout`, `--interval`, `--max-attempts`, `--force`, or `--include` can cause a `terminated` error. Always pass all five explicitly:

**Combined poll + retrieve (preferred):** Combines approval polling and card retrieval in one background call. Run this immediately after `create --request-approval` returns — it polls until the user approves, then retrieves the card in the same process, eliminating the approval-to-retrieval gap:

```
link-cli spend-request retrieve <lsrq_id> \
  --include card \
  --output-file /tmp/link-card.json \
  --timeout 600 \
  --interval 2 \
  --max-attempts 0 \
  --force \
  --format json
# → run with: background=true, notify_on_complete=true, timeout=660
```

**Post-approval retrieve (only when poll already confirmed approval):** If you already polled separately (e.g. via a background process) and confirmed `status: "approved"`, retrieve the card with zero interval:

```
link-cli spend-request retrieve <lsrq_id> \
  --include card \
  --output-file /tmp/link-card.json \
  --timeout 30 \
  --interval 0 \
  --max-attempts 0 \
  --force \
  --format json
```

The file is written with `0600` perms; stdout shows only redacted fields (brand, last4, expiry) plus a `card_output_file` path.

### 6. Use the credential

- For web checkout: hand the file path to the user, OR pass it to a browser-driving tool that fills the form directly from disk. Never `read_file` or `cat` the card file into the agent's reasoning context.
- For MPP merchants:

  ```
  link-cli mpp pay <merchant-url> \
    --spend-request-id <lsrq_id> \
    --method POST \
    --data '<json body>'
  ```

### 7. Clean up

Delete the card file as soon as the purchase is done:

```
rm -f /tmp/link-card.json
```

## Optional: run as an MCP server instead

`@stripe/link-cli --mcp` exposes the same commands as MCP tools over stdio. To register it with Hermes' native MCP:

```
hermes mcp add stripe-link --command "npx" --args "@stripe/link-cli --mcp"
```

Then `hermes mcp list` should show `stripe-link`. The same approval rules apply — MCP doesn't bypass the Link app approval step.

## Pitfalls

- **US-only.** Outside the US, `auth login` will fail. Tell the user, don't keep retrying.
- **`--context` must be ≥100 characters.** The CLI returns `VALIDATION_ERROR / too_small` if shorter. Write a detailed context string (what, why, who) — not a one-liner.
- **`--request-approval` does NOT poll.** It returns immediately with `pending_approval` and a `_next.command`. You must separately poll via `retrieve --interval 2 --max-attempts 300` (background, notify_on_complete). The previous skill text that said it "polls until they approve or deny" was wrong.
- **One-time cards expire ~90 seconds after approval.** The window between the user approving in the Link app and you retrieving the card is very short. If the card expires, you must recreate the entire spend request and get a new approval. To avoid this: (a) use the **combined poll+retrieve** pattern in Section 5 so there's no gap, or (b) if you polled separately, retrieve the card immediately after seeing `status: "approved"` — do not do any other work in between.
- **`retrieve` requires explicit options or it errors with `terminated`.** Even though the schema shows defaults, omitting `--timeout`, `--interval`, `--max-attempts`, `--force`, or `--include` can fail. Always pass all five. See Section 5 for exact flags.
- **Token refresh failures during retrieval.** If `retrieve` fails with `Token refresh failed (400)`, you need to re-auth (`auth login --interval 5 --timeout 300`) and retry. But the card may expire during re-auth — which means recreating the spend request. This is why the combined poll+retrieve pattern is strongly preferred: it retrieves the card as part of the same process that detects approval, so no token refresh gap exists.
- **Card PAN must never enter agent context.** Use `--output-file` every time. If you've already retrieved without it, immediately `link-cli auth logout` is not enough — the card is one-time-use but rotate hygiene matters.
- **`--request-approval` blocks until the user acts.** If the user is asleep, the CLI will hit its timeout. Set expectations.
- **Multi-step `_next` commands.** Some commands return `_next.command` that must be executed to continue. When in doubt, prefer the inline-polling flags (`--interval`/`--timeout`).
- **Output format defaults to `toon`** in non-TTY mode. Fine for prose, but if a downstream step needs to parse a specific field, pass `--format json`.
- **Don't default to `card`.** The merchant-evaluation step (Section 2) exists because picking the wrong credential type fails the purchase silently or leaks more data than needed.
- **`spend-request list` only shows active requests by default.** Use `--include-history` to see expired/denied/terminal-state requests. Useful for debugging.

## Verification

```
link-cli --version && link-cli auth status
```

Exit code 0 means installed and logged in.

## Reference

- `references/error-fixes.md` — Session-verified error→fix log with exact commands: context ≥100 chars, `terminated` error, token refresh failure, card expiry, and the full correct end-to-end sequence.
