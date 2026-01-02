#!/bin/bash
# Hook Type: PreToolUse
# Description: Prevent dangerous git operations on protected branches

# Git safety hook - prevents force pushes and destructive git operations
# Protects main/master branches from accidents

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_ARGS="${CLAUDE_TOOL_ARGS:-}"

# Only check git-related tools
if [[ "$TOOL_NAME" != *"bash"* ]] && [[ "$TOOL_NAME" != *"git"* ]]; then
    exit 0
fi

# Protected branches
PROTECTED_BRANCHES=("main" "master" "production" "prod")

# Get current branch if in a git repo
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
else
    # Not in a git repo, nothing to protect
    exit 0
fi

# Check for dangerous operations on protected branches
for branch in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$CURRENT_BRANCH" = "$branch" ]; then

        # Block force push to protected branch
        if [[ "$TOOL_ARGS" == *"git push"*"--force"* ]] || \
           [[ "$TOOL_ARGS" == *"git push"*"-f"* ]]; then
            echo "🚨 BLOCKED: Force push to protected branch '$branch'"
            echo ""
            echo "Force pushing to $branch can cause serious issues."
            echo "If you must force push:"
            echo "  1. Switch to a feature branch"
            echo "  2. Or disable this hook temporarily"
            echo ""
            exit 1
        fi

        # Block destructive operations on protected branch
        if [[ "$TOOL_ARGS" == *"git reset --hard"* ]] || \
           [[ "$TOOL_ARGS" == *"git clean -fd"* ]]; then
            echo "⚠️  Warning: Destructive git operation on protected branch '$branch'"
            echo "Operation: git reset --hard / git clean -fd"
            echo ""
            echo "This will permanently delete uncommitted changes."
            echo "Consider stashing or committing first."
            echo ""
            # Warn but allow (user might have backups)
        fi

        # Warn on rebase of protected branch
        if [[ "$TOOL_ARGS" == *"git rebase"* ]]; then
            echo "⚠️  Warning: Rebasing protected branch '$branch'"
            echo ""
            echo "Rebasing $branch can rewrite history."
            echo "This is usually not recommended for shared branches."
            echo ""
            # Warn but allow
        fi
    fi
done

# Check for force push to any branch (warn, don't block)
if [[ "$TOOL_ARGS" == *"git push"*"--force"* ]] || \
   [[ "$TOOL_ARGS" == *"git push"*"-f"* ]]; then
    # Already blocked above if protected branch
    # Just warn for other branches
    if [[ ! " ${PROTECTED_BRANCHES[@]} " =~ " ${CURRENT_BRANCH} " ]]; then
        echo "⚠️  Force pushing to branch: $CURRENT_BRANCH"
    fi
fi

exit 0
