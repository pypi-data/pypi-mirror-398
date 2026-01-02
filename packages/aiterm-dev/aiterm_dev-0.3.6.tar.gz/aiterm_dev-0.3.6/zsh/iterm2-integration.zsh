#!/usr/bin/env zsh
# ITERM2 CONTEXT SWITCHER - Profile + Title
# Switches profile colors AND sets tab title with icon
# Integrates with shared project-detector when available

# Cache to avoid redundant switches
typeset -g _ITERM_CURRENT_PROFILE=""
typeset -g _ITERM_CURRENT_TITLE=""

# Try to load shared project detector (from zsh-claude-workflow)
typeset -g _ITERM_HAS_DETECTOR=0
if [[ -f "$HOME/.config/zsh/functions/project-detector.zsh" ]]; then
    source "$HOME/.config/zsh/functions/project-detector.zsh" 2>/dev/null && _ITERM_HAS_DETECTOR=1
fi

_iterm_switch_profile() {
    local new_profile="$1"
    [[ "$_ITERM_CURRENT_PROFILE" == "$new_profile" ]] && return
    _ITERM_CURRENT_PROFILE="$new_profile"
    printf '\033]1337;SetProfile=%s\007' "$new_profile"
}

_iterm_set_title() {
    local new_title="$1"
    [[ "$_ITERM_CURRENT_TITLE" == "$new_title" ]] && return
    _ITERM_CURRENT_TITLE="$new_title"
    printf '\033]2;%s\007' "$new_title"  # Window title (OSC 2)
}

# Set iTerm2 user variable (for status bar)
# Usage: _iterm_set_user_var "name" "value"
_iterm_set_user_var() {
    printf '\033]1337;SetUserVar=%s=%s\007' "$1" "$(echo -n "$2" | base64)"
}

# Set all context variables for status bar
# Usage: _iterm_set_status_vars "icon" "name" "branch" "profile"
_iterm_set_status_vars() {
    _iterm_set_user_var "ctxIcon" "$1"
    _iterm_set_user_var "ctxName" "$2"
    _iterm_set_user_var "ctxBranch" "$3"
    _iterm_set_user_var "ctxProfile" "$4"
}

# Get git branch and dirty status
_iterm_git_info() {
    [[ -d ".git" ]] || git rev-parse --git-dir &>/dev/null || return

    local branch=$(git branch --show-current 2>/dev/null)
    [[ -z "$branch" ]] && branch=$(git describe --tags --exact-match 2>/dev/null || echo "detached")

    # Truncate long branch names
    (( ${#branch} > 20 )) && branch="${branch:0:8}…${branch: -8}"

    # Check for uncommitted changes
    local dirty=""
    git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null || dirty="*"

    echo "($branch)$dirty"
}

# Map project types to iTerm2 profiles
_iterm_type_to_profile() {
    case "$1" in
        rpkg) echo "R-Dev" ;;
        python) echo "Python-Dev" ;;
        node) echo "Node-Dev" ;;
        *) echo "Default" ;;
    esac
}

_iterm_detect_context() {
    [[ "$TERM_PROGRAM" != "iTerm.app" ]] && return

    local profile="Default"
    local icon=""
    local name="${PWD:t}"  # Current directory name

    # Get git info (branch + dirty)
    local git_info=$(_iterm_git_info)
    local branch="${git_info//[\(\)*]/}"  # Strip parens and asterisk for status bar

    # Priority overrides (Safety > AI sessions)
    if [[ $PWD == */production/* || $PWD == */prod/* ]]; then
        profile="Production"
        icon="🚨"
    elif [[ $PWD == */claude-sessions/* || $PWD == */gemini-sessions/* ]]; then
        profile="AI-Session"
        icon="🤖"
    # Use shared detector if available (for specific types only)
    elif (( _ITERM_HAS_DETECTOR )); then
        local proj_type=$(get_project_type 2>/dev/null)
        # Only use shared detector for specific types, not generic "project"
        if [[ -n "$proj_type" && "$proj_type" != "unknown" && "$proj_type" != "project" ]]; then
            icon=$(get_project_icon "$proj_type" 2>/dev/null)
            name=$(get_project_name 2>/dev/null || echo "$name")
            profile=$(_iterm_type_to_profile "$proj_type")
        fi
    fi

    # Fallback detection (fast, built-in) - only if not already detected
    if [[ "$profile" == "Default" ]]; then
        if [[ -f "DESCRIPTION" ]]; then
            profile="R-Dev"
            icon="📦"
            name=$(grep "^Package:" DESCRIPTION 2>/dev/null | cut -d' ' -f2 || echo "$name")
        elif [[ -f "pyproject.toml" ]]; then
            profile="Python-Dev"
            icon="🐍"
        elif [[ -f "package.json" ]]; then
            profile="Node-Dev"
            icon="📦"
            name=$(grep '"name"' package.json 2>/dev/null | head -1 | cut -d'"' -f4 || echo "$name")
        elif [[ -f "_quarto.yml" ]]; then
            profile="R-Dev"
            icon="📊"
            name=$(grep "^title:" _quarto.yml 2>/dev/null | head -1 | cut -d'"' -f2 || echo "$name")
        elif [[ -d "mcp-server" ]] || [[ "$PWD" == *"mcp"* && -f "package.json" ]]; then
            profile="AI-Session"
            icon="🔌"
        elif [[ -f "Cask" ]] || [[ -f ".dir-locals.el" ]] || [[ -f "init.el" ]] || [[ -f "early-init.el" ]]; then
            profile="Emacs"
            icon="⚡"
        elif [[ -d ".git" ]] && { [[ -d "commands" ]] || [[ -d "scripts" ]] || [[ -d "bin" && -f "Makefile" ]]; }; then
            profile="Dev-Tools"
            icon="🔧"
        fi
    fi

    # Apply changes
    _iterm_switch_profile "$profile"

    # Set title: icon + name + git info
    if [[ -n "$icon" ]]; then
        _iterm_set_title "$icon $name $git_info"
    else
        _iterm_set_title "$name $git_info"
    fi

    # Set status bar variables
    _iterm_set_status_vars "$icon" "$name" "$branch" "$profile"
}

# ─── Session-Aware Profile Switching ─────────────────────────────

# Store the profile before session started
typeset -g _ITERM_PRE_SESSION_PROFILE=""

# Called when a focus session starts
iterm_session_start() {
    local session_name="${1:-Focus}"

    # Save current profile
    _ITERM_PRE_SESSION_PROFILE="$_ITERM_CURRENT_PROFILE"

    # Switch to Focus profile and update title
    _iterm_switch_profile "Focus"
    _iterm_set_title "🎯 $session_name"

    echo "🎯 iTerm2: Focus mode activated"
}

# Called when a focus session ends
iterm_session_end() {
    if [[ -n "$_ITERM_PRE_SESSION_PROFILE" ]]; then
        # Restore previous profile
        _iterm_switch_profile "$_ITERM_PRE_SESSION_PROFILE"
        _ITERM_PRE_SESSION_PROFILE=""

        # Re-detect context for title
        _iterm_detect_context

        echo "✅ iTerm2: Focus mode ended"
    fi
}

# Register hook (only once)
if (( ! ${+_ITERM_HOOK_REGISTERED} )); then
    typeset -g _ITERM_HOOK_REGISTERED=1
    autoload -U add-zsh-hook
    add-zsh-hook chpwd _iterm_detect_context
fi

# Set initial profile for current directory
_iterm_detect_context
