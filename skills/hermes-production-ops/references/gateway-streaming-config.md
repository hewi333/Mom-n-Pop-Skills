# Gateway Streaming Config — End-User Message Flooding Diagnostics

Reference for diagnosing the "the agent keeps sending the same message over
and over" report from a non-technical end-user.

## Problem

The agent runs 30+ consecutive tool calls in a single turn — legitimate
work (building a monitor integration, debugging a config) — but each tool
call triggers a streaming progress message to the chat because of
`tool_progress: all`. The user sees 30 messages that each look like the
agent restarting from scratch.

## Root Cause

Three config settings combine to create the flood:

1. `gateway.tool_progress: all` — sends a progress message for EVERY tool call
2. `gateway.streaming: true` (per-platform, e.g. platforms.telegram.streaming) — streams intermediate text
3. `agent.max_turns: 150` (default) — generous budget allowing very long turns

## Contributing Factor: Cascading Delegation Re-entry

When the agent dispatches a background `delegate_task`, the delegation result
re-enters the session as a new inbound message when it completes. This
triggers a new turn, which can dispatch another delegation, creating a chain:

```
Turn 1: 30 tool calls → response delivered
  ↓ delegation_1 completes → injected as new inbound message
Turn 2: dispatches delegation_2 → short response delivered
  ↓ delegation_2 completes → injected as new inbound message
Turn 3: 5 more tool calls → another response delivered
```

The user gets 3 responses when they sent 1 message.

## Recommended Fixes

- `gateway.tool_progress: final` — the chat gets only the end result, not
  every intermediate tool call. Apply via `hermes config set gateway.tool_progress final`.
- `agent.max_turns: 75` (lowered from the 150 default).
- Don't dispatch background delegations from messaging sessions unless the
  user explicitly asked for background work — do the work inline.

## Recommended Config for Messaging-Heavy Deployments

```yaml
# In config.yaml, under gateway:
tool_progress: final              # or 'summary' — NOT 'all'
long_running_notifications: true  # keep — useful for genuine long tasks
busy_ack_detail: true             # keep — fires once per turn

# Under agent:
max_turns: 40-75                  # 150 (default) is too generous for messaging
```

## Why Some Deployments Don't Have This Problem

If a deployment has `tool_progress: summary` or `final`, or streaming
disabled for the platform, or a lower `max_turns`, it won't flood. The
default combination of `tool_progress: all` + `max_turns: 150` is the
problematic one.

## Diagnosis Steps

1. Check `~/.hermes/logs/gateway.log` for "Flushing text batch" entries — count
   how many fire per user message. More than 1-2 per turn = flooding.
2. Check `~/.hermes/logs/agent.log` for the session ID — count API calls and
   tool turns. If tool_turns > 20, the agent is doing too much in one turn.
3. Check `~/.hermes/config.yaml` for `tool_progress`, `streaming`, and
   `max_turns` / `max_iterations`.
4. Grep agent.log for `deleg_` IDs to see if cascading delegation re-entry is
   occurring (multiple turns triggered by delegation completion injections).

## Gateway Stop Under Systemd

The gateway typically runs as `hermes-gateway.service` with `Restart=always` +
`RestartSec=5`. Killing the process PID is futile — systemd revives it in
5 seconds. You MUST stop the service:

```bash
sudo systemctl stop hermes-gateway.service
```

If the agent has no sudo access (no `SUDO_PASSWORD` in `~/.hermes/.env`, no
passwordless sudoers entry), it cannot stop the gateway. Ask the operator to
run the command from an SSH terminal.

To enable agent-managed sudo:

```
# In ~/.hermes/.env:
SUDO_PASSWORD=<password>
```

This is a security tradeoff — only enable on trusted, single-purpose VPS hosts.