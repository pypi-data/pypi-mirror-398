#!/usr/bin/env zsh
# ══════════════════════════════════════════════════════════════════════════════
# ITERM2 CONTEXT SWITCHER - SETUP VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════
#
# Run this script to verify your setup is complete and working.
#
# Usage: ./scripts/verify-setup.sh
#        zsh scripts/verify-setup.sh
#
# ══════════════════════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Counters
PASS=0
FAIL=0
WARN=0

# ─── Helper Functions ─────────────────────────────────────────────────────────

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARN++))
}

section() {
    echo ""
    echo -e "${BOLD}$1${NC}"
    echo "─────────────────────────────────────────"
}

# ══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}🔍 iTerm2 Context Switcher - Setup Verification${NC}"
echo "════════════════════════════════════════════════════"

# ─── Check 1: Running in iTerm2 ───────────────────────────────────────────────

section "1. Environment"

if [[ "$TERM_PROGRAM" == "iTerm.app" ]]; then
    check_pass "Running in iTerm2"
else
    check_fail "Not running in iTerm2 (TERM_PROGRAM=$TERM_PROGRAM)"
    echo "       Please run this script from iTerm2"
fi

# ─── Check 2: iTerm2 Utilities ────────────────────────────────────────────────

section "2. iTerm2 Utilities"

if [[ -d "$HOME/.iterm2" ]]; then
    check_pass "~/.iterm2/ directory exists"
else
    check_fail "~/.iterm2/ directory not found"
    echo "       Install: iTerm2 → Install Shell Integration"
fi

if command -v it2profile &>/dev/null; then
    check_pass "it2profile command available"
else
    check_fail "it2profile command not found"
    echo "       Install: iTerm2 → Install Shell Integration"
fi

# ─── Check 3: Integration File ────────────────────────────────────────────────

section "3. Integration File"

INTEGRATION_FILE="$HOME/projects/dev-tools/aiterm/zsh/iterm2-integration.zsh"

if [[ -f "$INTEGRATION_FILE" ]]; then
    check_pass "Integration file exists"
else
    check_fail "Integration file not found at:"
    echo "       $INTEGRATION_FILE"
fi

# ─── Check 4: Sourced in .zshrc ───────────────────────────────────────────────

section "4. Shell Configuration"

ZSHRC="$HOME/.config/zsh/.zshrc"
if [[ ! -f "$ZSHRC" ]]; then
    ZSHRC="$HOME/.zshrc"
fi

if [[ -f "$ZSHRC" ]]; then
    if grep -q "aiterm" "$ZSHRC" 2>/dev/null; then
        check_pass "Integration sourced in $(basename $ZSHRC)"
    else
        check_fail "Integration not sourced in $ZSHRC"
        echo "       Add: source ~/projects/dev-tools/aiterm/zsh/iterm2-integration.zsh"
    fi
else
    check_warn "Could not find .zshrc"
fi

# ─── Check 5: Function Loaded ─────────────────────────────────────────────────

section "5. Functions Loaded"

# Source integration file directly to test if it works
if [[ -f "$INTEGRATION_FILE" ]]; then
    source "$INTEGRATION_FILE" 2>/dev/null
fi

if typeset -f chpwd_iterm_profile > /dev/null 2>&1; then
    check_pass "chpwd_iterm_profile function loaded"
else
    check_fail "chpwd_iterm_profile function not loaded"
    echo "       Run: source ~/.config/zsh/.zshrc"
fi

if typeset -f _iterm_badge > /dev/null 2>&1; then
    check_pass "_iterm_badge helper loaded"
else
    check_warn "_iterm_badge helper not loaded (may be older version)"
fi

if typeset -f _git_dirty > /dev/null 2>&1; then
    check_pass "_git_dirty helper loaded"
else
    check_warn "_git_dirty helper not loaded (may be older version)"
fi

# ─── Check 6: Hook Registered ─────────────────────────────────────────────────

section "6. Hook Registration"

if [[ -n "${chpwd_functions[(r)chpwd_iterm_profile]}" ]]; then
    check_pass "chpwd hook registered"
else
    check_warn "chpwd hook may not be registered"
    echo "       The function should auto-register when sourced"
fi

# ─── Check 7: iTerm2 Profiles ─────────────────────────────────────────────────

section "7. iTerm2 Profiles (Manual Check Required)"

echo -e "  ${BLUE}ℹ${NC}  Check these profiles exist in iTerm2 Preferences → Profiles:"
echo ""
echo "      Required (core):"
echo "        □ R-Dev        (blue theme, 📦 badge)"
echo "        □ AI-Session   (purple theme, 🤖 badge)"
echo "        □ Focus        (minimal dark, 🎯 badge)"
echo "        □ Production   (red theme, 🔴 badge)"
echo ""
echo "      Optional (new contexts):"
echo "        □ Python-Dev   (for Python projects)"
echo "        □ Node-Dev     (for Node.js/MCP projects)"
echo ""
echo "      Note: Missing profiles will fall back to Default"

# ─── Check 8: AI Session Directories ──────────────────────────────────────────

section "8. AI Session Directories"

if [[ -d "$HOME/claude-sessions" ]]; then
    check_pass "~/claude-sessions/ exists"
else
    check_warn "~/claude-sessions/ not found"
    echo "       Create: mkdir -p ~/claude-sessions"
fi

if [[ -d "$HOME/gemini-sessions" ]]; then
    check_pass "~/gemini-sessions/ exists"
else
    check_warn "~/gemini-sessions/ not found"
    echo "       Create: mkdir -p ~/gemini-sessions"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════"
echo -e "${BOLD}Summary${NC}"
echo "────────────────────────────────────────────────────"
echo -e "  ${GREEN}✓ Passed:${NC}  $PASS"
echo -e "  ${YELLOW}⚠ Warnings:${NC} $WARN"
echo -e "  ${RED}✗ Failed:${NC}  $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✅ Setup looks good!${NC}"
    echo ""
    echo "Test it:"
    echo "  cd ~/projects/r-packages/active/medfit  # Should show 📦 medfit"
    echo "  cd ~/claude-sessions                    # Should show 🤖 Claude"
    echo "  cd ~                                    # Should clear badge"
else
    echo -e "${RED}${BOLD}❌ Some issues need attention${NC}"
    echo ""
    echo "Fix the failed checks above, then run this script again."
fi

echo ""
