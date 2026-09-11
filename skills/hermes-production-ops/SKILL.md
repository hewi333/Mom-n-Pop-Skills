---
name: hermes-production-ops
description: "Operate and maintain a live production Hermes gateway deployment: switch models/providers globally, manage gateway restarts, suppress operational notifications to end-users, tune streaming/progress config for messaging platforms, and recover from stuck states without sudo. Use when changing the global model, planning a gateway restart, or configuring platform behavior for end-user-facing deployments."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, production, operations, model-switching, notifications]
---

# Hermes Production Gateway Operations

Techniques for operating a live production Hermes gateway that serves
non-technical end-users via Telegram (or other messaging platforms). The
core constraint: **the gateway cannot go down** and **end-users should not
see operational noise** (restart pings, progress spam, error messages,
technical detail).

## When to Use

- Switching the global model or provider (e.g., GLM-5.2 → GLM-5.3)
- Suppressing gateway restart/startup notifications to end-users
- Tuning streaming/progress config for a messaging deployment
- Planning a gateway restart that minimizes disruption
- Any config change that requires a gateway restart to take effect

## Model/Provider Switching (Global)

### Workflow

1. **Verify the new model exists on the provider** before changing config.
   For Together AI, hit the models endpoint with the API key:
   ```bash
   curl -s "https://api.together.xyz/v1/models" \
        -H "Authorization: Bearer $TOGETHER_API_KEY" -o /tmp/models.json
   python3 -c "import json; [print(m['id']) for m in json.load(open('/tmp/models.json')) if 'glm' in m['id'].lower()]"
   ```
   **Pitfall:** Never blindly change the model string without confirming it's
   listed. A typo or unlisted model name will break all gateway sessions
   silently until rollback.

2. **Edit `config.yaml`** (at `~/.hermes/config.yaml`):
   - `model.default`: change the model string (e.g., `zai-org/GLM-5.2` → `zai-org/GLM-5.3`)
   - `custom_providers`: update the `model:` field in the matching provider entry
   - Both must match — `model.default` is what the agent uses; the
     `custom_providers` entry is the named provider definition.

3. **Restart the gateway** for changes to take effect:
   ```bash
   sudo systemctl restart hermes-gateway.service
   ```
   Config changes do NOT apply mid-conversation. The gateway must restart.

### No-Sudo Constraint

The agent process typically runs without sudo. It cannot stop or restart
`hermes-gateway.service` itself — the operator must do this via SSH.
`hermes gateway restart` from inside a tool call also requires elevated
privileges. This is a security feature, not a bug: recognize it after one
failed attempt and hand the action to the operator instead of trying five
workarounds in sequence (each failed attempt is a tool call, and under
`tool_progress: all` each one streams a message to end-users).

### Rollback

If the new model has issues (tool-calling failures, format incompatibility),
revert `model.default` and the `custom_providers` model field to the previous
value and restart again. Always note the previous model string before switching.

## Suppressing Gateway Restart Notifications

**Problem:** by default, every gateway restart sends two messages to every
connected home channel:
- Shutdown: "⚠️ Gateway restarting — Your current task will be interrupted..."
- Startup: "♻️ Gateway online — Hermes is back and ready."

For non-technical end-users these are confusing noise that prompts them to
text the operator asking what broke.

**Solution:** set `gateway_restart_notification: false` per platform in
`config.yaml`. This suppresses BOTH messages for that platform:

```yaml
telegram:
  gateway_restart_notification: false
```

Or via CLI: `hermes config set telegram.gateway_restart_notification false`
(requires a gateway restart — config is read at startup).

### What It Suppresses

| Message | When | Suppressed? |
|---------|------|-------------|
| "⚠️ Gateway restarting/shutting down..." | Before drain (active sessions only) | Yes |
| "♻️ Gateway online — Hermes is back and ready." | On startup (home channels) | Yes |

### What It Does NOT Suppress

- `/restart` initiated from within a chat still sends a reply to that
  specific chat. The flag only affects the broadcast to home channels and
  the shutdown notification to active sessions.
- Messages from the agent during normal operation are unaffected.

### Implementation Detail

The flag lives in `gateway/config.py` as `gateway_restart_notification: bool = True`
on the `PlatformConfig` dataclass, serialized as
`<platform>.gateway_restart_notification`. It's checked in two places in
`gateway/run.py`: `_notify_active_sessions_of_shutdown()` and
`_send_home_channel_startup_notifications()` — each skips platforms where
the flag is false. For source detail, see
`references/gateway-restart-notifications.md`.

## Streaming & Progress Config for End-User Deployments

The default progress settings are tuned for an operator watching a terminal,
not for a business owner reading Telegram. The problematic combination:

- `gateway.tool_progress: all` — sends a progress message for EVERY tool call
- generous `agent.max_turns` — allows long multi-tool turns
- streaming enabled on the platform

A 30-tool-call turn (legitimate work — building an integration, debugging)
produces 30 streaming progress messages. To end-users this looks like the
agent glitching or looping, and it fires the "what's wrong??" texts.

**Recommended config for messaging deployments:**

```yaml
# config.yaml
gateway:
  tool_progress: final           # or 'summary' — NOT 'all' for end-user platforms
  long_running_notifications: true   # keep — useful for genuinely long tasks
agent:
  max_turns: 40-75               # 150 (default) is too generous for messaging
```

For the full diagnostic — log signatures, config interactions, cascading
delegation re-entry, and what a flood looks like in the logs — see
`references/gateway-streaming-config.md`.

## Planning a Safe Restart

1. Check if any sessions are actively running (ask the operator or check logs)
2. Set `gateway_restart_notification: false` if not already done
3. Make config changes
4. Have the operator restart via SSH: `sudo systemctl restart hermes-gateway.service`
5. Verify the gateway came back: `hermes gateway status`
6. Verify the new model is active: `hermes config | grep -A2 Model`

## Key Config Locations

```
~/.hermes/config.yaml       Main config (model, providers, platform settings)
~/.hermes/.env              API keys and secrets
~/.hermes/logs/gateway.log  Gateway logs for debugging
```

## Pitfalls

- **Never change a model string without verifying it exists on the provider.**
  A bad model name breaks ALL sessions until rollback.
- **Config changes require a restart to take effect.** Do not tell the user
  the change is "done" until the gateway has been restarted.
- **The agent has no sudo.** It cannot restart the gateway. Plan for the
  operator to do this via SSH — and don't burn five tool calls rediscovering
  that fact.
- **Restart notifications confuse end-users.** Set
  `gateway_restart_notification: false` before any planned restart.
- **Cron jobs inherit the global model.** Switching the default model
  affects all cron jobs that don't have a per-job model override.
- **Background threads compound outages.** Auto skill-review threads and
  background delegations make their own API calls. During a provider outage
  or credit exhaustion, each thread retries independently — the session
  looks stuck while multiple retry loops burn wall-clock time. Know what
  runs concurrently on your deployment.
- **Killing the PID under systemd is futile.** `Restart=always` revives the
  gateway in seconds. Properly stopping it requires the service unit:
  `sudo systemctl stop hermes-gateway.service`.