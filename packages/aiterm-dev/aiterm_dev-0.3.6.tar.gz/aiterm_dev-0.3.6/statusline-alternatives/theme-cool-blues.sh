#!/bin/bash
# ALTERNATIVE 1: Cool Blues & Grays Theme
# Replace these color definitions in ~/.claude/statusline-p10k.sh (lines 299-314)

# Powerline separators (Unicode - literal characters)
SEP_LEFT=""        # Powerline left arrow (U+E0B4)
SEP_SAME=""        # Powerline thin separator (U+E0B5)
EDGE_START="░▒▓"
EDGE_END="▓▒░"

# COOL BLUES & GRAYS COLOR SCHEME
# Directory segment (steel blue background)
DIR_BG="48;5;67"      # Steel blue background (was 48;5;4 bright blue)
DIR_FG="38;5;254"     # White foreground
DIR_SHORT="38;5;250"  # Light gray for shortened
DIR_ANCHOR="38;5;255;1" # Bright white bold for anchor

# VCS segment colors (muted blues)
VCS_CLEAN_BG="48;5;24"     # Slate blue background (was 48;5;2 green)
VCS_MODIFIED_BG="48;5;60"  # Blue-gray background (was 48;5;3 yellow)
VCS_FG="38;5;254"          # White foreground (was 38;5;0 black)

# Meta colors
META_FG="38;5;7"           # White for symbols
PROMPT_OK="38;5;117"       # Ice blue prompt (was 38;5;76 green)
PROMPT_ERROR="38;5;147"    # Lavender prompt (was 38;5;196 red)

# Reset
RESET="\033[0m"

# QUOTA COLOR ADJUSTMENTS (lines 210-228)
# Replace quota color logic:
get_quota_display_colors() {
    local session="$1"
    local weekly="$2"

    # Cool blue spectrum for session percentage
    local session_color="38;5;117"   # Ice blue (was 38;5;82 green)
    if (( session >= 95 )); then
        session_color="38;5;147"     # Lavender (was 38;5;196 red)
    elif (( session >= 80 )); then
        session_color="38;5;111"     # Steel blue (was 38;5;208 orange)
    elif (( session >= 50 )); then
        session_color="38;5;74"      # Medium cyan (was 38;5;220 yellow)
    fi

    # Cool blue spectrum for weekly percentage
    local weekly_color="38;5;117"    # Ice blue (was 38;5;82 green)
    if (( weekly >= 95 )); then
        weekly_color="38;5;147"      # Lavender (was 38;5;196 red)
    elif (( weekly >= 80 )); then
        weekly_color="38;5;111"      # Steel blue (was 38;5;208 orange)
    elif (( weekly >= 50 )); then
        weekly_color="38;5;74"       # Medium cyan (was 38;5;220 yellow)
    fi

    echo "${session_color}|${weekly_color}"
}

# LINE 2 ADJUSTMENTS (line 485)
# Replace this line:
# line2_content="${line2_content} \033[38;5;240m│\033[0m \033[38;5;75m${current_time}\033[0m \033[38;5;240m│\033[0m \033[38;5;214m⏱ ${session_duration}\033[0m"

# With this:
line2_content="${line2_content} \033[38;5;240m│\033[0m \033[38;5;116m${current_time}\033[0m \033[38;5;240m│\033[0m \033[38;5;109m⏱ ${session_duration}\033[0m"
# Changed: time 38;5;75→38;5;116 (soft cyan), duration 38;5;214→38;5;109 (calm gray-blue)

# MODEL COLOR ADJUSTMENTS (lines 463-478)
get_model_display() {
    local model="$1"
    local model_short=$(echo "$model" | sed 's/Claude //')

    # Cool blue spectrum for models
    local model_color="38;5;117"  # Default ice blue (was 38;5;33)
    if [[ "$model" == *"Sonnet"* ]]; then
        model_color="38;5;111"    # Steel blue (was 38;5;69)
    elif [[ "$model" == *"Opus"* ]]; then
        model_color="38;5;147"    # Lavender (was 38;5;141 purple)
    elif [[ "$model" == *"Haiku"* ]]; then
        model_color="38;5;74"     # Cyan (was 38;5;114 green)
    fi

    echo "\033[${model_color}m${model_short}\033[0m"
}

# INSTALLATION:
# 1. Copy lines 7-21 to ~/.claude/statusline-p10k.sh (replace lines 293-314)
# 2. Copy get_quota_display_colors function (integrate into get_quota_display around line 210)
# 3. Replace line 485 with the new line2_content line
# 4. Replace get_model_display function (lines 463-478)
