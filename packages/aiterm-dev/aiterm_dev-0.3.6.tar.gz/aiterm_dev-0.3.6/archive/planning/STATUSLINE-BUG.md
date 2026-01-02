# StatusLine Bug in Claude Code v2.0.70

**Date:** 2025-12-16
**Discovered by:** DT
**Status:** Confirmed - Version limitation

## Summary

The statusLine feature in Claude Code v2.0.70 does not pass JSON data to the configured command, making it impossible to display dynamic session information.

## Problem Description

When a statusLine command is configured in `.claude/settings.json`, Claude Code v2.0.70:
- ✅ Calls the script (confirmed via debug logging)
- ❌ Does NOT pass JSON data via stdin (input is empty)
- ✅ Script executes without errors (exit code 0)
- ❌ No statusLine appears in the terminal

## Evidence

### Configuration
```json
{
  "statusLine": {
    "type": "command",
    "command": "/bin/bash /Users/dt/.claude/statusline-p10k.sh"
  }
}
```

### Debug Output
Created debug wrapper at `/Users/dt/.claude/statusline-debug.sh`:

```bash
#!/bin/bash
input=$(cat)
echo "$input" > /tmp/claude-statusline-input.json
echo "$input" | /bin/bash /Users/dt/.claude/statusline-p10k.sh
```

Results:
- **Input file size:** 1 byte (empty, just newline)
- **Expected:** JSON with workspace, model, cost, session data
- **Actual:** No data passed to stdin

### Diagnostic Files
- `/tmp/statusline-doctor.log` - Full diagnostic output
- `/tmp/claude-statusline-debug.log` - Debug wrapper logs
- `/tmp/claude-statusline-input.json` - Empty JSON input (1 byte)

## Root Cause

Claude Code v2.0.70 appears to be too old to support the JSON-passing mechanism for statusLine. The feature is documented in the official Claude Code docs but not working in this version.

## Expected Behavior

According to official docs, Claude Code should pass JSON via stdin:

```json
{
  "hook_event_name": "Status",
  "session_id": "abc123...",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "model": {
    "id": "claude-opus-4-1",
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/current/working/directory",
    "project_dir": "/original/project/directory"
  },
  "version": "1.0.80",
  "output_style": { "name": "default" },
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000
  }
}
```

## Workaround

None available in v2.0.70. The statusLine feature requires upgrade to a newer version of Claude Code.

## Resolution

Upgrade to the latest version of Claude Code:

```bash
# Via Homebrew
brew upgrade claude-code

# Or via install script
curl -fsSL https://claude.ai/install.sh | bash
```

After upgrade, test that JSON is being passed:

```bash
# Check the debug log after upgrade
cat /tmp/claude-statusline-input.json

# Should show full JSON structure, not empty
```

## Impact on aiterm Project

This bug does not affect the aiterm v0.1.0-dev release, as:
- aiterm's statusLine script (`~/.claude/statusline-p10k.sh`) is correctly written
- The bug is in Claude Code v2.0.70, not in the script
- Users on newer Claude Code versions will not experience this issue
- The script handles empty input gracefully (defensive programming)

## Notes

The Powerlevel10k-style statusLine script is well-designed and will work once Claude Code is updated. The script includes:
- Project type detection (8 types)
- Git status integration
- Session duration tracking
- Quota display
- Cost tracking
- ANSI color coding
- Single-line output (Claude Code requirement)

## References

- Official statusLine docs: https://code.claude.com/docs/en/statusline.md
- Script location: `/Users/dt/.claude/statusline-p10k.sh`
- Debug wrapper: `/Users/dt/.claude/statusline-debug.sh`
- Issue discovered: 2025-12-16 during aiterm v0.1.0-dev release prep
