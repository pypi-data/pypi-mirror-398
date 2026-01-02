#!/bin/bash
# Hook Type: SessionStart
# Description: Auto-switch terminal context based on project type

# Context switcher hook - detects project and applies aiterm context
# Integrates with aiterm's context detection system

# Only run if aiterm is installed
if ! command -v aiterm &> /dev/null; then
    exit 0
fi

# Only run in iTerm2
if [ "$TERM_PROGRAM" != "iTerm.app" ]; then
    exit 0
fi

# Get current directory (from Claude Code session)
CWD="${CLAUDE_CWD:-$PWD}"

# Detect and apply context
if [ -d "$CWD" ]; then
    # Run aiterm switch silently
    aiterm switch "$CWD" 2>/dev/null

    # Show brief notification
    CONTEXT=$(aiterm detect "$CWD" 2>/dev/null | grep "Type" | awk '{print $2, $3}')
    if [ -n "$CONTEXT" ]; then
        echo "🎨 Context: $CONTEXT"
    fi
fi

exit 0
