#!/bin/bash
# Hook Type: PreToolUse
# Description: Validate dangerous tool operations before execution

# Tool validator hook - prevents dangerous operations
# Blocks destructive commands that could cause data loss

# Tool information from Claude Code (example: tool_name, tool_args)
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_ARGS="${CLAUDE_TOOL_ARGS:-}"

# Dangerous patterns to block
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "dd if=/dev/zero"
    "mkfs"
    "> /dev/sda"
    "chmod -R 777 /"
    "chown -R"
    "rm -rf ~"
    "rm -rf /home"
    "rm -rf /Users"
)

# Check if tool involves dangerous operations
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if [[ "$TOOL_ARGS" == *"$pattern"* ]]; then
        echo "⚠️  BLOCKED: Dangerous operation detected"
        echo "Pattern: $pattern"
        echo "Tool: $TOOL_NAME"
        echo ""
        echo "This operation could cause data loss."
        echo "If you're sure, disable this hook temporarily."
        exit 1  # Non-zero exit blocks the tool
    fi
done

# Warn on risky but not blocked operations
RISKY_PATTERNS=(
    "rm -rf"
    "git push --force"
    "DROP DATABASE"
    "DELETE FROM"
    "TRUNCATE"
)

for pattern in "${RISKY_PATTERNS[@]}"; do
    if [[ "$TOOL_ARGS" == *"$pattern"* ]]; then
        echo "⚠️  Warning: Potentially destructive operation"
        echo "Tool: $TOOL_NAME"
        echo "Pattern: $pattern"
        echo ""
        # Allow but warn
        break
    fi
done

# Exit 0 = allow the tool to run
exit 0
