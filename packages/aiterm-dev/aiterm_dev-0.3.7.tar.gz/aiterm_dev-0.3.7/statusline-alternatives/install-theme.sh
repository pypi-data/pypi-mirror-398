#!/bin/bash
# Install StatusLine Color Theme
# Usage: bash install-theme.sh [cool-blues|forest-greens|purple-charcoal]

THEME="${1:-cool-blues}"
STATUSLINE_FILE="$HOME/.claude/statusline-p10k.sh"
BACKUP_FILE="$HOME/.claude/statusline-p10k.sh.backup-$(date +%Y%m%d-%H%M%S)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if statusline file exists
if [[ ! -f "$STATUSLINE_FILE" ]]; then
    echo "Error: StatusLine file not found at $STATUSLINE_FILE"
    exit 1
fi

# Validate theme
case "$THEME" in
    cool-blues|forest-greens|purple-charcoal)
        ;;
    *)
        echo "Error: Unknown theme '$THEME'"
        echo "Usage: bash install-theme.sh [cool-blues|forest-greens|purple-charcoal]"
        exit 1
        ;;
esac

THEME_FILE="$SCRIPT_DIR/theme-${THEME}.sh"

if [[ ! -f "$THEME_FILE" ]]; then
    echo "Error: Theme file not found at $THEME_FILE"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  Installing StatusLine Theme: ${THEME}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Backup current file
echo "Creating backup: $BACKUP_FILE"
cp "$STATUSLINE_FILE" "$BACKUP_FILE"

# Apply theme based on selection
echo "Applying theme..."

case "$THEME" in
    "cool-blues")
        # Replace color definitions (lines 299-314)
        sed -i.tmp '299,314d' "$STATUSLINE_FILE"
        sed -i.tmp '298a\
# COOL BLUES & GRAYS COLOR SCHEME\
# Directory segment (steel blue background)\
DIR_BG="48;5;67"      # Steel blue background\
DIR_FG="38;5;254"     # White foreground\
DIR_SHORT="38;5;250"  # Light gray for shortened\
DIR_ANCHOR="38;5;255;1" # Bright white bold for anchor\
\
# VCS segment colors (muted blues)\
VCS_CLEAN_BG="48;5;24"     # Slate blue background\
VCS_MODIFIED_BG="48;5;60"  # Blue-gray background\
VCS_FG="38;5;254"          # White foreground\
\
# Meta colors\
META_FG="38;5;7"           # White for symbols\
PROMPT_OK="38;5;117"       # Ice blue prompt\
PROMPT_ERROR="38;5;147"    # Lavender prompt' "$STATUSLINE_FILE"

        # Replace line 485 (duration color)
        sed -i.tmp 's/38;5;214m⏱/38;5;109m⏱/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/38;5;75m\${current_time}/38;5;116m${current_time}/g' "$STATUSLINE_FILE"

        # Replace quota colors (lines 211-218, 221-228)
        sed -i.tmp 's/session_color="38;5;82"/session_color="38;5;117"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;196"/session_color="38;5;147"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;208"/session_color="38;5;111"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;220"/session_color="38;5;74"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;82"/weekly_color="38;5;117"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;196"/weekly_color="38;5;147"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;208"/weekly_color="38;5;111"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;220"/weekly_color="38;5;74"/g' "$STATUSLINE_FILE"

        # Replace model colors (lines 468-476)
        sed -i.tmp 's/model_color="38;5;33"/model_color="38;5;117"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;69"/model_color="38;5;111"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;141"/model_color="38;5;147"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;114"/model_color="38;5;74"/g' "$STATUSLINE_FILE"

        # Replace lines display colors (line 285, 287)
        sed -i.tmp 's/38;5;82m+\${lines_added}/38;5;117m+${lines_added}/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/38;5;196m\/-\${lines_removed}/38;5;147m\/-${lines_removed}/g' "$STATUSLINE_FILE"
        ;;

    "forest-greens")
        # Replace color definitions (lines 299-314)
        sed -i.tmp '299,314d' "$STATUSLINE_FILE"
        sed -i.tmp '298a\
# FOREST GREENS & DARK COLOR SCHEME\
# Directory segment (forest green background)\
DIR_BG="48;5;22"      # Forest green background\
DIR_FG="38;5;230"     # Cream foreground\
DIR_SHORT="38;5;250"  # Light gray for shortened\
DIR_ANCHOR="38;5;255;1" # Bright white bold for anchor\
\
# VCS segment colors (green spectrum)\
VCS_CLEAN_BG="48;5;28"     # Deep green background\
VCS_MODIFIED_BG="48;5;58"  # Olive green background\
VCS_FG="38;5;230"          # Cream foreground\
\
# Meta colors\
META_FG="38;5;7"           # White for symbols\
PROMPT_OK="38;5;121"       # Mint green prompt\
PROMPT_ERROR="38;5;167"    # Rusty red prompt' "$STATUSLINE_FILE"

        # Replace line 485 (duration color)
        sed -i.tmp 's/38;5;214m⏱/38;5;143m⏱/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/38;5;75m\${current_time}/38;5;108m${current_time}/g' "$STATUSLINE_FILE"

        # Replace quota colors
        sed -i.tmp 's/session_color="38;5;82"/session_color="38;5;121"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;196"/session_color="38;5;130"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;208"/session_color="38;5;136"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;220"/session_color="38;5;143"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;82"/weekly_color="38;5;121"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;196"/weekly_color="38;5;130"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;208"/weekly_color="38;5;136"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;220"/weekly_color="38;5;143"/g' "$STATUSLINE_FILE"

        # Replace model colors
        sed -i.tmp 's/model_color="38;5;33"/model_color="38;5;121"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;69"/model_color="38;5;114"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;141"/model_color="38;5;140"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;114"/model_color="38;5;108"/g' "$STATUSLINE_FILE"

        # Replace lines display colors
        sed -i.tmp 's/38;5;82m+\${lines_added}/38;5;121m+${lines_added}/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/38;5;196m\/-\${lines_removed}/38;5;167m\/-${lines_removed}/g' "$STATUSLINE_FILE"
        ;;

    "purple-charcoal")
        # Replace color definitions (lines 299-314)
        sed -i.tmp '299,314d' "$STATUSLINE_FILE"
        sed -i.tmp '298a\
# PURPLE & CHARCOAL COLOR SCHEME\
# Directory segment (deep purple background)\
DIR_BG="48;5;54"      # Deep purple background\
DIR_FG="38;5;250"     # Light gray foreground\
DIR_SHORT="38;5;245"  # Medium gray for shortened\
DIR_ANCHOR="38;5;255;1" # Bright white bold for anchor\
\
# VCS segment colors (charcoal and purple)\
VCS_CLEAN_BG="48;5;236"    # Charcoal background\
VCS_MODIFIED_BG="48;5;60"  # Slate purple background\
VCS_FG="38;5;250"          # Light gray foreground\
\
# Meta colors\
META_FG="38;5;7"           # White for symbols\
PROMPT_OK="38;5;141"       # Violet prompt\
PROMPT_ERROR="38;5;168"    # Rose prompt' "$STATUSLINE_FILE"

        # Replace line 485 (duration color)
        sed -i.tmp 's/38;5;214m⏱/38;5;139m⏱/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/38;5;75m\${current_time}/38;5;183m${current_time}/g' "$STATUSLINE_FILE"

        # Replace quota colors
        sed -i.tmp 's/session_color="38;5;82"/session_color="38;5;183"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;196"/session_color="38;5;125"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;208"/session_color="38;5;133"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/session_color="38;5;220"/session_color="38;5;139"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;82"/weekly_color="38;5;183"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;196"/weekly_color="38;5;125"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;208"/weekly_color="38;5;133"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/weekly_color="38;5;220"/weekly_color="38;5;139"/g' "$STATUSLINE_FILE"

        # Replace model colors
        sed -i.tmp 's/model_color="38;5;33"/model_color="38;5;141"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;69"/model_color="38;5;147"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;141"/model_color="38;5;177"/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/model_color="38;5;114"/model_color="38;5;183"/g' "$STATUSLINE_FILE"

        # Replace lines display colors
        sed -i.tmp 's/38;5;82m+\${lines_added}/38;5;183m+${lines_added}/g' "$STATUSLINE_FILE"
        sed -i.tmp 's/38;5;196m\/-\${lines_removed}/38;5;168m\/-${lines_removed}/g' "$STATUSLINE_FILE"
        ;;
esac

# Clean up temp file
rm -f "${STATUSLINE_FILE}.tmp"

echo "✅ Theme installed successfully!"
echo ""
echo "Backup saved to: $BACKUP_FILE"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "To see the changes:"
echo "  1. Start a new Claude Code session: claude"
echo "  2. The new colors will appear in the status line"
echo ""
echo "To restore original:"
echo "  cp $BACKUP_FILE $STATUSLINE_FILE"
echo ""
echo "To try a different theme:"
echo "  bash install-theme.sh [cool-blues|forest-greens|purple-charcoal]"
echo ""
