#!/bin/bash
# Hook Type: SessionEnd
# Description: Track API costs and session metrics

# Cost tracker hook - logs session costs and metrics to ~/.claude/costs.log
# Reads session data from Claude Code environment variables

COST_LOG="$HOME/.claude/costs.log"

# Create log file if it doesn't exist
touch "$COST_LOG"

# Extract session data from environment (provided by Claude Code)
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
MODEL="${ANTHROPIC_MODEL:-unknown}"
COST="${CLAUDE_TOTAL_COST_USD:-0.00}"
DURATION="${CLAUDE_DURATION_SECONDS:-0}"
LINES_ADDED="${CLAUDE_LINES_ADDED:-0}"
LINES_REMOVED="${CLAUDE_LINES_REMOVED:-0}"

# Calculate cost per minute if duration > 0
if [ "$DURATION" -gt 0 ]; then
    DURATION_MIN=$((DURATION / 60))
    COST_PER_MIN=$(awk "BEGIN {printf \"%.4f\", $COST / ($DURATION_MIN + 1)}")
else
    DURATION_MIN=0
    COST_PER_MIN="0.0000"
fi

# Log to CSV format
echo "$(date '+%Y-%m-%d %H:%M:%S'),$SESSION_ID,$MODEL,$COST,$DURATION_MIN,+$LINES_ADDED/-$LINES_REMOVED,$COST_PER_MIN" >> "$COST_LOG"

# Keep log file under 1000 lines
if [ $(wc -l < "$COST_LOG") -gt 1000 ]; then
    tail -n 1000 "$COST_LOG" > "$COST_LOG.tmp"
    mv "$COST_LOG.tmp" "$COST_LOG"
fi

# Optional: Show summary to user
if [ "$COST" != "0.00" ]; then
    echo "Session cost: \$$COST (${DURATION_MIN}m, +$LINES_ADDED/-$LINES_REMOVED lines)"
fi

exit 0
