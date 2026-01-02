# Session Coordination

Track and coordinate parallel Claude Code sessions across projects.

## Overview

When running multiple Claude Code sessions simultaneously, aiterm provides automatic session tracking via Claude Code hooks. This helps you:

- **See all active sessions** at a glance
- **Detect conflicts** when multiple sessions work on the same project
- **Track task context** for each session
- **Review session history** for past work

## Quick Start

```bash
# Install the hooks (one-time setup)
ait hooks install session-register
ait hooks install session-cleanup

# View all active sessions
ait sessions live

# Check for conflicts
ait sessions conflicts

# Set task for current session
ait sessions task "Implementing user auth"
```

## How It Works

### Automatic Registration

When Claude Code starts in a project, the `session-register.sh` hook:

1. Creates a manifest file in `~/.claude/sessions/active/`
2. Records: session ID, project path, git branch, start time
3. Detects if another session is already working on the same project

### Automatic Cleanup

When Claude Code exits, the `session-cleanup.sh` hook:

1. Moves the manifest to `~/.claude/sessions/history/YYYY-MM-DD/`
2. Records end time and final status
3. Preserves task description for history

## Commands

### `ait sessions live`

Show all currently active Claude Code sessions.

```bash
$ ait sessions live

╭─────────────────────────────────────────────────────────╮
│ Active Claude Code Sessions                             │
├─────────────────────────────────────────────────────────┤
│ 1. aiterm (main) - 45m                                  │
│    /Users/dt/projects/dev-tools/aiterm                  │
│    Task: Implementing session coordination              │
│                                                         │
│ 2. atlas (feature/auth) - 12m                           │
│    /Users/dt/projects/apps/atlas                        │
│    Task: Adding OAuth support                           │
╰─────────────────────────────────────────────────────────╯
```

### `ait sessions current`

Show the session for the current directory (if any).

```bash
$ ait sessions current

Session: abc123
Project: aiterm
Branch:  main (dirty)
Started: 45 minutes ago
Task:    Implementing session coordination
```

### `ait sessions task`

Set or view the task description for the current session.

```bash
# Set task
ait sessions task "Fixing login bug"

# View current task
ait sessions task
```

### `ait sessions conflicts`

Detect when multiple sessions are working on the same project.

```bash
$ ait sessions conflicts

⚠️  Conflict Detected!
Project: aiterm
Sessions:
  - abc123 (main) started 2h ago
  - def456 (dev) started 15m ago

Risk: Parallel edits may cause merge conflicts.
Recommendation: Coordinate work or close one session.
```

### `ait sessions history`

Browse archived sessions by date.

```bash
# Today's sessions
ait sessions history

# Specific date
ait sessions history --date 2025-12-25

# Last 7 days
ait sessions history --days 7
```

### `ait sessions prune`

Archive stale sessions whose processes are no longer running.

```bash
# Preview what would be archived
ait sessions prune --dry-run

# Archive stale sessions
ait sessions prune
```

This is useful when Claude Code exits unexpectedly (crash, force quit, terminal
close) and the cleanup hook doesn't fire. Stale sessions are moved to history
with status "pruned".

## Session Manifest Format

Manifests are stored as JSON in `~/.claude/sessions/active/`:

```json
{
  "session_id": "abc123",
  "project": "aiterm",
  "path": "/Users/dt/projects/dev-tools/aiterm",
  "git_branch": "main",
  "git_dirty": true,
  "started": "2025-12-26T14:30:00Z",
  "pid": 12345,
  "task": "Implementing session coordination"
}
```

## Hook Installation

The session hooks are installed via aiterm:

```bash
# Install both hooks
ait hooks install session-register
ait hooks install session-cleanup

# Verify installation
ait hooks list
```

Or manually add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "~/.claude/hooks/session-register.sh"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "~/.claude/hooks/session-cleanup.sh"
      }
    ]
  }
}
```

## Directory Structure

```
~/.claude/sessions/
├── active/                    # Currently running sessions
│   ├── abc123.json
│   └── def456.json
└── history/                   # Archived sessions by date
    ├── 2025-12-25/
    │   ├── session1.json
    │   └── session2.json
    └── 2025-12-26/
        └── session3.json
```

## Use Cases

### Multi-Project Development

When working on related projects (e.g., backend + frontend), session coordination helps you:

- Track which projects have active sessions
- Quickly switch context between projects
- Review what you worked on across projects

### Team Coordination

If multiple team members use aiterm, session history provides:

- Record of who worked on what
- Timeline of project activity
- Context for code review discussions

### ADHD-Friendly Workflow

Session tracking supports focus by:

- Showing your current task prominently
- Reminding you of active work when switching projects
- Providing history when you need to remember "what was I doing?"

## Troubleshooting

### Sessions not appearing

1. Verify hooks are installed: `ait hooks list`
2. Check hook execution: `cat ~/.claude/sessions/active/*.json`
3. Ensure directory exists: `mkdir -p ~/.claude/sessions/{active,history}`

### Stale sessions

If sessions aren't cleaned up (e.g., Claude Code crashed, force quit, terminal closed):

```bash
# Preview stale sessions (checks PIDs)
ait sessions prune --dry-run

# Archive stale sessions to history
ait sessions prune
```

The `prune` command checks each active session's process ID (PID) and archives
any sessions whose processes are no longer running.

### Permission errors

Ensure write permissions:

```bash
chmod 755 ~/.claude/sessions
chmod 755 ~/.claude/sessions/active
chmod 755 ~/.claude/sessions/history
```
