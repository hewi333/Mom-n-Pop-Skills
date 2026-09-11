# Cron Script Arguments — Platform Limitation & Workaround

## Problem
The Hermes cron `script` field treats the entire string as a filename. If you set
`script: "foo.py arg1"`, the scheduler looks for a file literally named
`foo.py arg1` (with the space and argument as part of the filename) and fails:

```
Script not found: /home/hermes/.hermes/scripts/foo.py arg1
```

The job goes to `last_status: "error"` and auto-disables.

## Root Cause
The cron scheduler resolves the `script` field as a single path under
`~/.hermes/scripts/`. It does not split on spaces or parse arguments — the
entire value is treated as the script filename.

## Workaround: Wrapper Scripts
Create a small shell script per argument variant that calls the Python script
with the correct argument:

```bash
#!/bin/bash
# ~/.hermes/scripts/foo_wrapper.sh
exec python3 "$(dirname "$0")/foo.py" --arg-value
```

Make it executable: `chmod +x ~/.hermes/scripts/foo_wrapper.sh`

Set the cron job's `script` field to just the wrapper filename:
```
script: "foo_wrapper.sh"
```

## Verification
1. Run the wrapper directly: `bash ~/.hermes/scripts/foo_wrapper.sh` — should exit 0
2. Create or update the cron job with `script: "foo_wrapper.sh"`
3. Wait one tick, then `cronjob(action='list')` — check `last_status: "ok"`

## Affected Pattern
Any `no_agent=True` cron job where the script needs a CLI argument (account name,
config file path, mode flag, etc.). If the script takes no arguments, the `script`
field works fine as-is.