# Stripe Link CLI — Error → Fix Log

Session-verified errors and their fixes. Each entry is a real failure encountered during a live spend request, with the exact command that resolved it.

## 1. `VALIDATION_ERROR: too_small` on `--context`

**Error:**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Too small: expected string to have >=100 characters",
  "fieldErrors": [{ "path": ["context"], "code": "too_small", "minimum": 100 }]
}
```

**Cause:** `--context` string was under 100 characters.

**Fix:** Expand to a full sentence. Template:
```
"<Company> is purchasing <product> from <merchant> for <purpose>. This charge covers <specific scope — e.g. first month of the plan>."
```

## 2. `--request-approval` returns immediately with `pending_approval`

**Symptom:** `spend-request create --request-approval` exits 0 but status is `pending_approval`, not `approved`. The response includes `_next.command`.

**Cause:** `--request-approval` sends the push notification but does NOT poll. The skill's old text ("polls until they approve or deny") is incorrect.

**Fix:** After `create` returns, start a background `retrieve` with `--interval 2 --max-attempts 300` to poll for the approval, or better — use the combined poll+retrieve pattern (Section 5 of SKILL.md).

## 3. One-time card expired before retrieval (`status: "expired"`)

**Symptom:**
```
spend-request retrieve <id> --include card --output-file /tmp/link-card.json
→ { "code": "NOT_FOUND", "message": "Spend request <id> not found" }
```

Then `spend-request list --include-history` shows `status: "expired"` with `updated_at` ~90 seconds after `status: "approved"`.

**Cause:** The approved one-time card has a very short TTL (~90 seconds). A token refresh failure occurred between approval and retrieval, requiring re-auth, which consumed the entire window.

**Fix (recovery):** Create a new spend request with the same parameters. Get a new approval.

**Fix (prevention):** Use the **combined poll+retrieve** pattern — run a single background `retrieve` command with `--interval 2` immediately after `create --request-approval`. It polls for approval and retrieves the card in one process, eliminating the gap.

## 4. `retrieve` errors with `terminated`

**Error:**
```
{ "code": "UNKNOWN", "message": "terminated" }
```

**Cause:** The `retrieve` command's schema marks `timeout`, `interval`, `maxAttempts`, `include`, and `force` as required (`required[5]`). Even though defaults are shown, omitting them can cause failures.

**Fix:** Pass all five options explicitly:
```bash
link-cli spend-request retrieve <id> \
  --include card \
  --output-file /tmp/link-card.json \
  --timeout 30 \
  --interval 0 \
  --max-attempts 0 \
  --force \
  --format json
```

## 5. `Token refresh failed (400)` during `retrieve`

**Error:**
```
{ "code": "UNKNOWN", "message": "Token refresh failed (400): [object Object]" }
```

**Cause:** Auth token expired between the background poll completing and the foreground `retrieve` call.

**Fix:** Re-authenticate with `link-cli auth login --client-name "Hermes" --interval 5 --timeout 300`, then retry `retrieve`. **Warning:** The card may have expired during re-auth — check with `spend-request list --include-history` first. If `status: "expired"`, you must recreate the spend request from scratch.

## Correct end-to-end command sequence (verified working)

```bash
# 1. Check auth
link-cli auth status --format json

# 2. List payment methods
link-cli payment-methods list --format json

# 3. Create spend request (context MUST be ≥100 chars)
link-cli spend-request create \
  --payment-method-id "<pm_id>" \
  --merchant-name "<name>" \
  --merchant-url "<url>" \
  --context "<≥100 char context>" \
  --amount <cents> \
  --line-item "name:<item>,unit_amount:<cents>,quantity:1" \
  --total "type:total,display_text:Total,amount:<cents>" \
  --request-approval \
  --format json

# 4. Combined poll + retrieve (background, notify_on_complete=true)
link-cli spend-request retrieve <lsrq_id> \
  --include card \
  --output-file /tmp/link-card.json \
  --timeout 600 \
  --interval 2 \
  --max-attempts 0 \
  --force \
  --format json

# 5. If poll confirmed approval separately, retrieve immediately:
link-cli spend-request retrieve <lsrq_id> \
  --include card \
  --output-file /tmp/link-card.json \
  --timeout 30 \
  --interval 0 \
  --max-attempts 0 \
  --force \
  --format json

# 6. Clean up
rm -f /tmp/link-card.json
```