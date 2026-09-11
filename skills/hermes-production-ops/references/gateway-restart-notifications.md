# Gateway Restart Notification Suppression — Source Detail

Reference for the `gateway_restart_notification` config flag. Captures the
exact source locations and logic discovered by reading
`~/.hermes/hermes-agent/` source.

## Config Definition

**File:** `gateway/config.py` (~line 332)

```python
# Whether the gateway is allowed to send "♻️ Gateway online" /
# "♻ Gateway restarted" lifecycle notifications on this platform.
# Default True preserves prior behavior. Set False on platforms used
# by end users (e.g. Slack) where operator-flavored restart pings are
# noise; keep True for back-channels where the operator wants them.
gateway_restart_notification: bool = True
```

Part of the `PlatformConfig` dataclass. Serialized to config.yaml as
`<platform>.gateway_restart_notification` (e.g.,
`telegram.gateway_restart_notification`).

## Check Site 1: Shutdown Notification

**File:** `gateway/run.py`, method `_notify_active_sessions_of_shutdown()` (~line 4702)

Called at the very start of `stop()` — before draining. Adapters are still
connected so messages can be delivered. The check at ~line 4767:

```python
platform_cfg = self.config.platforms.get(platform)
if platform_cfg is not None and not platform_cfg.gateway_restart_notification:
    logger.info(
        "Shutdown notification suppressed for active session: %s has gateway_restart_notification=false",
        platform_str,
    )
    continue
```

This skips sending the "⚠️ Gateway restarting — Your current task will be
interrupted..." message to active sessions on platforms where the flag is
false.

**Important:** This notification only goes to sessions that are *actively
running* at shutdown time. Idle sessions don't get it regardless.

## Check Site 2: Home Channel Startup Notification

**File:** `gateway/run.py`, method `_send_home_channel_startup_notifications()` (~line 12909)

Called during startup after platform adapters connect. Sends "♻️ Gateway
online — Hermes is back and ready." to configured home channels. The check
at ~line 12930:

```python
platform_cfg = self.config.platforms.get(platform)
if platform_cfg is not None and not platform_cfg.gateway_restart_notification:
    logger.info(
        "Home-channel startup notification suppressed: %s has gateway_restart_notification=false",
        platform.value,
    )
    continue
```

## When the Startup Notification Fires

The startup notification only fires for **non-chat planned restarts** —
i.e., restarts triggered via terminal, SIGUSR1, or systemd service restart.
Chat-originated `/restart` commands use `.restart_notify.json` for a precise
reply to the originating chat instead.

The flow (line ~6041):

```python
planned_restart_notification_pending = _planned_restart_notification_pending()
await self._send_restart_notification()

if planned_restart_notification_pending:
    try:
        await self._send_home_channel_startup_notifications(skip_targets=None)
    finally:
        _clear_planned_restart_notification()
```

The `.restart_pending.json` marker is written at ~line 7084 when
`self._restart_requested` is true and `self._restart_command_source` is None
(non-chat restart):

```python
if self._restart_requested and self._restart_command_source is None:
    atomic_json_write(
        _planned_restart_notification_path(),
        {"requested_at": time.time(), "via_service": ..., "detached": ...},
    )
```

## Config YAML Example

```yaml
telegram:
  gateway_restart_notification: false
```

Set via CLI:

```bash
hermes config set telegram.gateway_restart_notification false
```

Or edit `~/.hermes/config.yaml` directly. Requires gateway restart to take
effect (config is read at startup).