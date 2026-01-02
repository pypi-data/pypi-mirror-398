# Session Commands Reference

Quick reference for aiterm session coordination commands.

## Commands

| Command | Description |
|---------|-------------|
| `ait sessions live` | List all active Claude Code sessions |
| `ait sessions current` | Show session for current directory |
| `ait sessions task "desc"` | Set/view task for current session |
| `ait sessions conflicts` | Detect parallel session conflicts |
| `ait sessions history` | Browse archived sessions |
| `ait sessions prune` | Archive stale sessions (PID check) |

## Live Sessions

```bash
# Show all active sessions
ait sessions live

# With details
ait sessions live --verbose

# JSON output
ait sessions live --json
```

## Task Tracking

```bash
# Set task description
ait sessions task "Implementing feature X"

# View current task
ait sessions task

# Clear task
ait sessions task ""
```

## Conflict Detection

```bash
# Check for conflicts
ait sessions conflicts

# Exit with error code if conflicts found
ait sessions conflicts --strict
```

## History

```bash
# Today's sessions
ait sessions history

# Specific date
ait sessions history --date 2025-12-25

# Last N days
ait sessions history --days 7

# Filter by project
ait sessions history --project aiterm
```

## Stale Session Cleanup

When Claude Code exits unexpectedly (crash, force quit, terminal close), the
cleanup hook may not run. Use `prune` to archive orphaned sessions:

```bash
# Preview stale sessions (dry run)
ait sessions prune --dry-run

# Archive stale sessions
ait sessions prune
```

**How it works:**

1. Checks each active session's PID
2. If process is no longer running → session is stale
3. Moves stale sessions to `history/YYYY-MM-DD/` with status "pruned"

## File Locations

| Path | Purpose |
|------|---------|
| `~/.claude/sessions/active/` | Active session manifests |
| `~/.claude/sessions/history/` | Archived sessions by date |
| `~/.claude/hooks/session-register.sh` | SessionStart hook |
| `~/.claude/hooks/session-cleanup.sh` | Stop hook |

## Manifest Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `project` | string | Project name (directory name) |
| `path` | string | Full project path |
| `git_branch` | string | Current git branch |
| `git_dirty` | bool | Uncommitted changes |
| `started` | datetime | Session start time (ISO 8601) |
| `ended` | datetime | Session end time (if archived) |
| `pid` | int | Process ID |
| `task` | string | Current task description |
| `status` | string | Session status (active/completed/pruned) |

## Hook Events

| Event | Hook | Trigger |
|-------|------|---------|
| `SessionStart` | session-register.sh | Claude Code starts |
| `Stop` | session-cleanup.sh | Claude Code exits |

## Environment Variables

The hooks receive these from Claude Code:

| Variable | Description |
|----------|-------------|
| `CLAUDE_SESSION_ID` | Unique session ID |
| `CLAUDE_CWD` | Working directory |
| `CLAUDE_MODEL` | Model being used |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No active sessions / No conflicts |
| 2 | Session not found |
| 3 | Conflicts detected (with --strict) |
