#!/bin/bash
# Run interactive CLI tests in a new terminal pane/window
#
# Usage:
#   ./scripts/run-interactive-tests.sh              # Auto-detect (run here if in terminal)
#   ./scripts/run-interactive-tests.sh here         # Run in current terminal (no spawn)
#   ./scripts/run-interactive-tests.sh right        # Split right (vertical)
#   ./scripts/run-interactive-tests.sh below        # Split below (horizontal)
#   ./scripts/run-interactive-tests.sh tab          # New tab
#   ./scripts/run-interactive-tests.sh window       # New window (force spawn)
#   TERMINAL=iterm2 ./scripts/run-interactive-tests.sh right  # Force iTerm2
#
# Supported terminals:
#   - Ghostty (default if available)
#   - iTerm2
#   - Terminal.app (fallback)

set -euo pipefail

# ============================================
# Configuration
# ============================================

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_SCRIPT="tests/cli/interactive-tests.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# Interactive Terminal Detection
# ============================================

# Check if we're running inside an interactive terminal
# Returns 0 (true) if in terminal, 1 (false) if spawned from Claude Code or non-interactive
is_interactive_terminal() {
    # Must have a tty
    if [[ ! -t 0 ]] || [[ ! -t 1 ]]; then
        return 1
    fi

    # Check for Claude Code environment (should spawn new window)
    if [[ "${CLAUDECODE:-}" == "1" ]]; then
        return 1
    fi

    # Check for known terminal programs
    case "${TERM_PROGRAM:-}" in
        ghostty|iTerm.app|Apple_Terminal)
            return 0
            ;;
        *)
            # Unknown terminal - assume not interactive
            return 1
            ;;
    esac
}

# Determine default split mode based on context
get_default_split() {
    if is_interactive_terminal; then
        echo "here"  # Run in current terminal
    else
        echo "window"  # Spawn new window
    fi
}

# ============================================
# Terminal Detection
# ============================================

detect_terminal() {
    # Allow override via environment variable
    if [[ -n "${TERMINAL:-}" ]]; then
        echo "$TERMINAL"
        return
    fi

    # When running from Claude Code, TERM_PROGRAM is inherited and unreliable
    # Use fallback detection instead
    if [[ "${CLAUDECODE:-}" == "1" ]]; then
        if command -v ghostty &> /dev/null || [[ -d "/Applications/Ghostty.app" ]]; then
            echo "ghostty"
        elif [[ -d "/Applications/iTerm.app" ]]; then
            echo "iterm2"
        else
            echo "terminal"
        fi
        return
    fi

    # Detect from TERM_PROGRAM (reliable when in actual terminal)
    case "${TERM_PROGRAM:-}" in
        ghostty)
            echo "ghostty"
            ;;
        iTerm.app)
            echo "iterm2"
            ;;
        Apple_Terminal)
            echo "terminal"
            ;;
        *)
            # Fallback: check installed apps
            if command -v ghostty &> /dev/null || [[ -d "/Applications/Ghostty.app" ]]; then
                echo "ghostty"
            elif [[ -d "/Applications/iTerm.app" ]]; then
                echo "iterm2"
            else
                echo "terminal"
            fi
            ;;
    esac
}

# ============================================
# Ghostty Implementation
# ============================================

run_ghostty() {
    local split="$1"
    local cmd="cd '$PROJECT_DIR' && bash '$TEST_SCRIPT'"

    case "$split" in
        right|below)
            # Ghostty splits via keybindings - send keystroke to current window
            # ctrl+shift+enter = vertical split, ctrl+shift+o = horizontal split
            if [[ "$split" == "right" ]]; then
                # Send ctrl+shift+enter for vertical split, then run command
                osascript -e 'tell application "System Events"
                    tell process "ghostty"
                        keystroke return using {control down, shift down}
                        delay 0.3
                    end tell
                end tell'
            else
                # Send ctrl+shift+o for horizontal split (if configured)
                # Fallback: use ctrl+shift+d which is common for horizontal
                osascript -e 'tell application "System Events"
                    tell process "ghostty"
                        keystroke "d" using {control down, shift down}
                        delay 0.3
                    end tell
                end tell'
            fi
            # Type the command in the new split
            osascript -e "tell application \"System Events\"
                tell process \"ghostty\"
                    keystroke \"$cmd\"
                    keystroke return
                end tell
            end tell"
            ;;
        tab)
            # Ghostty new tab: ctrl+shift+t or cmd+t depending on config
            osascript -e 'tell application "System Events"
                tell process "ghostty"
                    keystroke "t" using {command down}
                    delay 0.3
                end tell
            end tell'
            osascript -e "tell application \"System Events\"
                tell process \"ghostty\"
                    keystroke \"$cmd\"
                    keystroke return
                end tell
            end tell"
            ;;
        window|*)
            # New Ghostty window - use AppleScript for reliability on macOS
            if [[ -d "/Applications/Ghostty.app" ]]; then
                osascript -e 'tell application "Ghostty"
                    activate
                    tell application "System Events"
                        keystroke "n" using {command down}
                    end tell
                end tell'
                sleep 0.5
                osascript -e "tell application \"System Events\"
                    tell process \"ghostty\"
                        keystroke \"cd '$PROJECT_DIR' && bash '$TEST_SCRIPT'\"
                        keystroke return
                    end tell
                end tell"
            else
                echo "Error: Ghostty.app not found"
                exit 1
            fi
            ;;
    esac
}

# ============================================
# iTerm2 Implementation
# ============================================

run_iterm2() {
    local split="$1"
    local cmd="cd '$PROJECT_DIR' && bash '$TEST_SCRIPT'"

    case "$split" in
        right)
            osascript -e "tell application \"iTerm2\"
                tell current session of current window
                    split vertically with default profile
                    tell last session of current tab of current window
                        write text \"$cmd\"
                    end tell
                end tell
            end tell"
            ;;
        below)
            osascript -e "tell application \"iTerm2\"
                tell current session of current window
                    split horizontally with default profile
                    tell last session of current tab of current window
                        write text \"$cmd\"
                    end tell
                end tell
            end tell"
            ;;
        tab)
            osascript -e "tell application \"iTerm2\"
                tell current window
                    create tab with default profile
                    tell current session
                        write text \"$cmd\"
                    end tell
                end tell
            end tell"
            ;;
        window|*)
            osascript -e "tell application \"iTerm2\"
                create window with default profile
                tell current session of current window
                    write text \"$cmd\"
                end tell
            end tell"
            ;;
    esac
}

# ============================================
# Terminal.app Implementation (Fallback)
# ============================================

run_terminal() {
    local split="$1"
    local cmd="cd '$PROJECT_DIR' && bash '$TEST_SCRIPT'"

    # Terminal.app doesn't support splits, always use new tab/window
    case "$split" in
        tab)
            osascript -e "tell application \"Terminal\"
                activate
                tell application \"System Events\"
                    keystroke \"t\" using {command down}
                end tell
                delay 0.5
                do script \"$cmd\" in front window
            end tell"
            ;;
        *)
            osascript -e "tell application \"Terminal\"
                activate
                do script \"$cmd\"
            end tell"
            ;;
    esac
}

# ============================================
# Main
# ============================================

# Determine split mode (use arg if provided, otherwise auto-detect)
SPLIT="${1:-$(get_default_split)}"
DETECTED_TERMINAL=$(detect_terminal)

# Handle "here" mode - run directly in current terminal
if [[ "$SPLIT" == "here" ]]; then
    echo -e "${BLUE}Terminal:${NC} $DETECTED_TERMINAL (current)"
    echo -e "${BLUE}Mode:${NC} Running in current terminal"
    echo -e "${BLUE}Project:${NC} $PROJECT_DIR"
    echo ""

    # Run tests directly
    cd "$PROJECT_DIR"
    exec bash "$TEST_SCRIPT"
fi

# Spawning new window/tab/split
echo -e "${BLUE}Terminal:${NC} $DETECTED_TERMINAL"
echo -e "${BLUE}Split:${NC} $SPLIT"
echo -e "${BLUE}Project:${NC} $PROJECT_DIR"
echo ""

case "$DETECTED_TERMINAL" in
    ghostty)
        run_ghostty "$SPLIT"
        echo -e "${GREEN}✅ Interactive tests running in Ghostty ($SPLIT)${NC}"
        ;;
    iterm2)
        run_iterm2 "$SPLIT"
        echo -e "${GREEN}✅ Interactive tests running in iTerm2 ($SPLIT)${NC}"
        ;;
    terminal)
        run_terminal "$SPLIT"
        echo -e "${GREEN}✅ Interactive tests running in Terminal.app ($SPLIT)${NC}"
        ;;
    *)
        echo -e "${YELLOW}⚠️  Unknown terminal: $DETECTED_TERMINAL${NC}"
        echo "Falling back to Terminal.app"
        run_terminal "$SPLIT"
        ;;
esac

echo ""
echo "You can continue working in Claude Code while tests run."
