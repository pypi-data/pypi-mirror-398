#!/bin/bash
# Preview StatusLine Color Themes
# Usage: bash preview-theme.sh [cool-blues|forest-greens|purple-charcoal]

THEME="${1:-cool-blues}"

# Color definitions for each theme
case "$THEME" in
    "cool-blues")
        THEME_NAME="Cool Blues & Grays"
        DIR_BG="48;5;67"
        DIR_FG="38;5;254"
        VCS_CLEAN_BG="48;5;24"
        VCS_MODIFIED_BG="48;5;60"
        VCS_FG="38;5;254"
        TIME_COLOR="38;5;116"
        DURATION_COLOR="38;5;109"
        MODEL_COLOR="38;5;111"
        QUOTA_SESSION_COLOR="38;5;117"
        QUOTA_WEEKLY_COLOR="38;5;74"
        LINES_ADDED_COLOR="38;5;117"
        LINES_REMOVED_COLOR="38;5;147"
        ;;
    "forest-greens")
        THEME_NAME="Forest Greens & Dark"
        DIR_BG="48;5;22"
        DIR_FG="38;5;230"
        VCS_CLEAN_BG="48;5;28"
        VCS_MODIFIED_BG="48;5;58"
        VCS_FG="38;5;230"
        TIME_COLOR="38;5;108"
        DURATION_COLOR="38;5;143"
        MODEL_COLOR="38;5;114"
        QUOTA_SESSION_COLOR="38;5;121"
        QUOTA_WEEKLY_COLOR="38;5;143"
        LINES_ADDED_COLOR="38;5;121"
        LINES_REMOVED_COLOR="38;5;167"
        ;;
    "purple-charcoal")
        THEME_NAME="Purple & Charcoal"
        DIR_BG="48;5;54"
        DIR_FG="38;5;250"
        VCS_CLEAN_BG="48;5;236"
        VCS_MODIFIED_BG="48;5;60"
        VCS_FG="38;5;250"
        TIME_COLOR="38;5;183"
        DURATION_COLOR="38;5;139"
        MODEL_COLOR="38;5;147"
        QUOTA_SESSION_COLOR="38;5;183"
        QUOTA_WEEKLY_COLOR="38;5;139"
        LINES_ADDED_COLOR="38;5;183"
        LINES_REMOVED_COLOR="38;5;168"
        ;;
    *)
        echo "Unknown theme: $THEME"
        echo "Usage: bash preview-theme.sh [cool-blues|forest-greens|purple-charcoal]"
        exit 1
        ;;
esac

# Powerline separators
SEP_LEFT=""
EDGE_START="░▒▓"
EDGE_END="▓▒░"

# Preview output
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Theme Preview: $THEME_NAME"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Line 1: Directory + Git Status (Clean)
dir_segment="\033[${DIR_BG};${DIR_FG}m ${EDGE_START} 📁 aiterm "
git_segment="\033[38;5;${DIR_BG##*;};${VCS_CLEAN_BG}m${SEP_LEFT}\033[${VCS_CLEAN_BG};${VCS_FG}m main \033[0m\033[38;5;${VCS_CLEAN_BG##*;}m${EDGE_END}\033[0m"
line1_clean="╭─${dir_segment}${git_segment}"

# Line 1: Directory + Git Status (Modified)
git_segment_mod="\033[38;5;${DIR_BG##*;};${VCS_MODIFIED_BG}m${SEP_LEFT}\033[${VCS_MODIFIED_BG};${VCS_FG}m dev* ⇡2 \033[0m\033[38;5;${VCS_MODIFIED_BG##*;}m${EDGE_END}\033[0m"
line1_modified="╭─${dir_segment}${git_segment_mod}"

# Line 2: Model + Time + Duration + Lines + Quota
model_display="\033[${MODEL_COLOR}mSonnet 4.5\033[0m"
time_display="\033[${TIME_COLOR}m14:30\033[0m"
duration_display="\033[${DURATION_COLOR}m⏱ 12m\033[0m"
lines_display="\033[${LINES_ADDED_COLOR}m+43\033[0m\033[${LINES_REMOVED_COLOR}m/-12\033[0m"
quota_display="\033[${QUOTA_SESSION_COLOR}m⚡84%\033[0m \033[${QUOTA_WEEKLY_COLOR}mW:11%\033[0m"

line2="╰─ ${model_display} \033[38;5;240m│\033[0m ${time_display} \033[38;5;240m│\033[0m ${duration_display} \033[38;5;240m│\033[0m ${lines_display} \033[38;5;240m│\033[0m ${quota_display}"

# Display examples
echo "Clean Repository:"
printf "%b\n%b\n" "$line1_clean" "$line2"
echo ""

echo "Modified Repository:"
printf "%b\n%b\n" "$line1_modified" "$line2"
echo ""

# Show key color changes
echo "─────────────────────────────────────────────────────────────"
echo "Key Color Changes from Default:"
echo "─────────────────────────────────────────────────────────────"
echo -e "  Directory BG:   \033[${DIR_BG};${DIR_FG}m Sample Text \033[0m"
echo -e "  Git Clean BG:   \033[${VCS_CLEAN_BG};${VCS_FG}m Sample Text \033[0m"
echo -e "  Git Modified:   \033[${VCS_MODIFIED_BG};${VCS_FG}m Sample Text \033[0m"
echo -e "  Time:           \033[${TIME_COLOR}m14:30\033[0m (was \033[38;5;75m14:30\033[0m)"
echo -e "  Duration:       \033[${DURATION_COLOR}m⏱ 12m\033[0m (was \033[38;5;214m⏱ 12m\033[0m) ← FIXED"
echo -e "  Model:          \033[${MODEL_COLOR}mSonnet 4.5\033[0m"
echo -e "  Quota Session:  \033[${QUOTA_SESSION_COLOR}m⚡84%\033[0m"
echo -e "  Quota Weekly:   \033[${QUOTA_WEEKLY_COLOR}mW:11%\033[0m"
echo -e "  Lines Added:    \033[${LINES_ADDED_COLOR}m+43\033[0m"
echo -e "  Lines Removed:  \033[${LINES_REMOVED_COLOR}m/-12\033[0m"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "To install this theme:"
echo "  bash install-theme.sh $THEME"
echo ""
