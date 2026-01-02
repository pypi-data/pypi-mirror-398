#!/bin/bash
# ALTERNATIVE 2: Forest Greens & Dark Theme
# Replace these color definitions in ~/.claude/statusline-p10k.sh (lines 299-314)

# Powerline separators (Unicode - literal characters)
SEP_LEFT=""        # Powerline left arrow (U+E0B4)
SEP_SAME=""        # Powerline thin separator (U+E0B5)
EDGE_START="░▒▓"
EDGE_END="▓▒░"

# FOREST GREENS & DARK COLOR SCHEME
# Directory segment (forest green background)
DIR_BG="48;5;22"      # Forest green background (was 48;5;4 bright blue)
DIR_FG="38;5;230"     # Cream foreground (was 38;5;254 white)
DIR_SHORT="38;5;250"  # Light gray for shortened
DIR_ANCHOR="38;5;255;1" # Bright white bold for anchor

# VCS segment colors (green spectrum)
VCS_CLEAN_BG="48;5;28"     # Deep green background (was 48;5;2 bright green)
VCS_MODIFIED_BG="48;5;58"  # Olive green background (was 48;5;3 yellow)
VCS_FG="38;5;230"          # Cream foreground (was 38;5;0 black)

# Meta colors
META_FG="38;5;7"           # White for symbols
PROMPT_OK="38;5;121"       # Mint green prompt (was 38;5;76)
PROMPT_ERROR="38;5;167"    # Rusty red prompt (was 38;5;196)

# Reset
RESET="\033[0m"

# QUOTA COLOR ADJUSTMENTS (lines 210-228)
# Replace quota color logic:
get_quota_display_colors() {
    local session="$1"
    local weekly="$2"

    # Green to brown spectrum for session percentage
    local session_color="38;5;121"   # Mint green (was 38;5;82)
    if (( session >= 95 )); then
        session_color="38;5;130"     # Brown (was 38;5;196 red)
    elif (( session >= 80 )); then
        session_color="38;5;136"     # Dark tan (was 38;5;208 orange)
    elif (( session >= 50 )); then
        session_color="38;5;143"     # Khaki (was 38;5;220 yellow)
    fi

    # Green to brown spectrum for weekly percentage
    local weekly_color="38;5;121"    # Mint green (was 38;5;82)
    if (( weekly >= 95 )); then
        weekly_color="38;5;130"      # Brown (was 38;5;196 red)
    elif (( weekly >= 80 )); then
        weekly_color="38;5;136"      # Dark tan (was 38;5;208 orange)
    elif (( weekly >= 50 )); then
        weekly_color="38;5;143"      # Khaki (was 38;5;220 yellow)
    fi

    echo "${session_color}|${weekly_color}"
}

# LINE 2 ADJUSTMENTS (line 485)
# Replace this line:
# line2_content="${line2_content} \033[38;5;240m│\033[0m \033[38;5;75m${current_time}\033[0m \033[38;5;240m│\033[0m \033[38;5;214m⏱ ${session_duration}\033[0m"

# With this:
line2_content="${line2_content} \033[38;5;240m│\033[0m \033[38;5;108m${current_time}\033[0m \033[38;5;240m│\033[0m \033[38;5;143m⏱ ${session_duration}\033[0m"
# Changed: time 38;5;75→38;5;108 (sage green), duration 38;5;214→38;5;143 (muted olive)

# MODEL COLOR ADJUSTMENTS (lines 463-478)
get_model_display() {
    local model="$1"
    local model_short=$(echo "$model" | sed 's/Claude //')

    # Green spectrum for models
    local model_color="38;5;121"  # Default mint green (was 38;5;33)
    if [[ "$model" == *"Sonnet"* ]]; then
        model_color="38;5;114"    # Sage green (was 38;5;69)
    elif [[ "$model" == *"Opus"* ]]; then
        model_color="38;5;140"    # Purple-green (was 38;5;141)
    elif [[ "$model" == *"Haiku"* ]]; then
        model_color="38;5;108"    # Light sage (was 38;5;114)
    fi

    echo "\033[${model_color}m${model_short}\033[0m"
}

# LINES DISPLAY ADJUSTMENTS (lines 273-291)
get_lines_display() {
    # Skip if no lines data
    if [[ "$lines_added" == "0" && "$lines_removed" == "0" ]]; then
        echo ""
        return
    fi
    if [[ "$lines_added" == "null" || "$lines_removed" == "null" ]]; then
        echo ""
        return
    fi

    # Format: +123/-45 with forest green/rusty red
    local display="\033[38;5;121m+${lines_added}\033[0m"  # Mint green (was 38;5;82)
    if [[ "$lines_removed" != "0" ]]; then
        display="${display}\033[38;5;167m/-${lines_removed}\033[0m"  # Rusty red (was 38;5;196)
    fi

    echo "$display"
}

# INSTALLATION:
# 1. Copy lines 7-21 to ~/.claude/statusline-p10k.sh (replace lines 293-314)
# 2. Copy get_quota_display_colors function (integrate into get_quota_display around line 210)
# 3. Replace line 485 with the new line2_content line
# 4. Replace get_model_display function (lines 463-478)
# 5. Replace get_lines_display function (lines 273-291)
