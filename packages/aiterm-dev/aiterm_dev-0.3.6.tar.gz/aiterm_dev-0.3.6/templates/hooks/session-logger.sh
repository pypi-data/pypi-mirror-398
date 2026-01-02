#!/bin/bash
# Hook Type: SessionStart
# Description: Log session metadata to file for tracking

# Session logger hook - logs basic session info to ~/.claude/session.log
# Useful for tracking when sessions start and what model is being used

LOG_FILE="$HOME/.claude/session.log"

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Log session start
echo "$(date '+%Y-%m-%d %H:%M:%S') | Session started | Model: ${ANTHROPIC_MODEL:-unknown} | CWD: $PWD" >> "$LOG_FILE"

# Keep log file under 1000 lines (delete oldest entries)
if [ $(wc -l < "$LOG_FILE") -gt 1000 ]; then
    tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp"
    mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

# Exit successfully (required for hooks)
exit 0
