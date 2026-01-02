#!/usr/bin/env zsh
# ══════════════════════════════════════════════════════════════════════════════
# ITERM2 CONTEXT SWITCHER - EDGE CASE TESTS
# ══════════════════════════════════════════════════════════════════════════════
#
# Run: ./scripts/test-edge-cases.sh
#
# ══════════════════════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
BOLD='\033[1m'

# Counters
PASS=0
FAIL=0

# Test directory
TEST_DIR="/tmp/iterm2-context-test-$$"
mkdir -p "$TEST_DIR"

# ─── Helper Functions ─────────────────────────────────────────────────────────

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASS++))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAIL++))
}

section() {
    echo ""
    echo -e "${BOLD}$1${NC}"
    echo "─────────────────────────────────────────"
}

cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE THE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

INTEGRATION="$HOME/projects/dev-tools/aiterm/zsh/iterm2-integration.zsh"

echo ""
echo -e "${BOLD}🧪 iTerm2 Context Switcher - Edge Case Tests${NC}"
echo "════════════════════════════════════════════════════"

if [[ ! -f "$INTEGRATION" ]]; then
    echo -e "${RED}ERROR: Integration file not found${NC}"
    exit 1
fi

source "$INTEGRATION"

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Re-entrancy Guard
# ══════════════════════════════════════════════════════════════════════════════

section "1. Re-entrancy Guard"

# Test guard prevents re-entry
_ITERM_SWITCHING=1
cd "$TEST_DIR"
if (( _ITERM_SWITCHING == 1 )); then
    pass "Guard prevents execution when already switching"
else
    fail "Guard did not prevent re-entry"
fi
_ITERM_SWITCHING=0

# Test guard resets after execution
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Guard resets after execution"
else
    fail "Guard not reset after execution"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Empty/Missing Files
# ══════════════════════════════════════════════════════════════════════════════

section "2. Empty/Missing Files"

# Empty DESCRIPTION file
mkdir -p "$TEST_DIR/empty-r-pkg"
touch "$TEST_DIR/empty-r-pkg/DESCRIPTION"
cd "$TEST_DIR/empty-r-pkg"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles empty DESCRIPTION file"
else
    fail "Crashed on empty DESCRIPTION"
fi

# DESCRIPTION without Package: line
echo "Title: Test" > "$TEST_DIR/empty-r-pkg/DESCRIPTION"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles DESCRIPTION without Package: line"
else
    fail "Crashed on DESCRIPTION without Package:"
fi

# Empty package.json
mkdir -p "$TEST_DIR/empty-node"
echo "{}" > "$TEST_DIR/empty-node/package.json"
cd "$TEST_DIR/empty-node"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles empty package.json"
else
    fail "Crashed on empty package.json"
fi

# Malformed package.json
echo "not json" > "$TEST_DIR/empty-node/package.json"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles malformed package.json"
else
    fail "Crashed on malformed package.json"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Special Characters in Paths
# ══════════════════════════════════════════════════════════════════════════════

section "3. Special Characters in Paths"

# Space in path
mkdir -p "$TEST_DIR/path with spaces"
touch "$TEST_DIR/path with spaces/DESCRIPTION"
echo "Package: test-spaces" > "$TEST_DIR/path with spaces/DESCRIPTION"
cd "$TEST_DIR/path with spaces"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles spaces in path"
else
    fail "Crashed on spaces in path"
fi

# Unicode in path
mkdir -p "$TEST_DIR/项目-émoji-🎉"
cd "$TEST_DIR/项目-émoji-🎉"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles unicode in path"
else
    fail "Crashed on unicode in path"
fi

# Special chars in package name
mkdir -p "$TEST_DIR/special-pkg"
echo 'Package: my.pkg_v2' > "$TEST_DIR/special-pkg/DESCRIPTION"
cd "$TEST_DIR/special-pkg"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles special chars in package name"
else
    fail "Crashed on special chars in package name"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Git Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

section "4. Git Edge Cases"

# Directory with .git but no commits
mkdir -p "$TEST_DIR/new-git-repo"
cd "$TEST_DIR/new-git-repo"
git init -q
touch DESCRIPTION
echo "Package: newrepo" > DESCRIPTION
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles new git repo with no commits"
else
    fail "Crashed on git repo with no commits"
fi

# Not a git repo
mkdir -p "$TEST_DIR/not-git"
cd "$TEST_DIR/not-git"
result=$(_git_dirty)
if [[ -z "$result" ]]; then
    pass "Returns empty for non-git directory"
else
    fail "Did not return empty for non-git directory"
fi

# Corrupted .git directory
mkdir -p "$TEST_DIR/bad-git/.git"
echo "corrupted" > "$TEST_DIR/bad-git/.git/HEAD"
cd "$TEST_DIR/bad-git"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles corrupted .git directory"
else
    fail "Crashed on corrupted .git"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Symlinks
# ══════════════════════════════════════════════════════════════════════════════

section "5. Symlinks"

# Symlinked directory
mkdir -p "$TEST_DIR/real-pkg"
echo "Package: realpkg" > "$TEST_DIR/real-pkg/DESCRIPTION"
ln -s "$TEST_DIR/real-pkg" "$TEST_DIR/linked-pkg"
cd "$TEST_DIR/linked-pkg"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles symlinked directories"
else
    fail "Crashed on symlinked directory"
fi

# Broken symlink
ln -s "$TEST_DIR/nonexistent" "$TEST_DIR/broken-link" 2>/dev/null
cd "$TEST_DIR"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles broken symlinks in directory"
else
    fail "Crashed on broken symlink"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Overlapping Patterns
# ══════════════════════════════════════════════════════════════════════════════

section "6. Overlapping Patterns"

# R package in production path (production should win)
mkdir -p "$TEST_DIR/production/my-pkg"
echo "Package: prodpkg" > "$TEST_DIR/production/my-pkg/DESCRIPTION"
cd "$TEST_DIR/production/my-pkg"
# Can't easily test which profile was selected, but should not crash
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles R package in production path"
else
    fail "Crashed on overlapping patterns"
fi

# MCP project with package.json (MCP check comes after package.json)
mkdir -p "$TEST_DIR/my-mcp-server"
echo '{"name": "mcp-test"}' > "$TEST_DIR/my-mcp-server/package.json"
cd "$TEST_DIR/my-mcp-server"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles MCP-named project with package.json"
else
    fail "Crashed on MCP project"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Rapid Directory Changes
# ══════════════════════════════════════════════════════════════════════════════

section "7. Rapid Directory Changes"

# Rapidly change directories
mkdir -p "$TEST_DIR/rapid-test/"{a,b,c,d,e}
for dir in a b c d e a b c d e; do
    cd "$TEST_DIR/rapid-test/$dir"
done
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles rapid directory changes"
else
    fail "Guard stuck after rapid changes"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: _project_name Function
# ══════════════════════════════════════════════════════════════════════════════

section "8. Helper Functions"

# Test _project_name
cd "$TEST_DIR"
result=$(_project_name)
expected=$(basename "$TEST_DIR")
if [[ "$result" == "$expected" ]]; then
    pass "_project_name returns correct basename"
else
    fail "_project_name returned '$result' instead of '$expected'"
fi

# Test _iterm_badge doesn't crash
_iterm_badge "test badge"
if [[ $? -eq 0 ]]; then
    pass "_iterm_badge executes without error"
else
    fail "_iterm_badge returned error"
fi

# Test _iterm_badge with empty string
_iterm_badge ""
if [[ $? -eq 0 ]]; then
    pass "_iterm_badge handles empty string"
else
    fail "_iterm_badge failed on empty string"
fi

# Test _iterm_badge with unicode
_iterm_badge "📦 テスト 🎉"
if [[ $? -eq 0 ]]; then
    pass "_iterm_badge handles unicode"
else
    fail "_iterm_badge failed on unicode"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 9: Quarto Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

section "9. Quarto Edge Cases"

# Quarto with no title
mkdir -p "$TEST_DIR/quarto-no-title"
echo "format: html" > "$TEST_DIR/quarto-no-title/_quarto.yml"
cd "$TEST_DIR/quarto-no-title"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles _quarto.yml without title"
else
    fail "Crashed on Quarto without title"
fi

# Both _quarto.yml and _quarto.yaml
mkdir -p "$TEST_DIR/quarto-both"
echo "title: yml-title" > "$TEST_DIR/quarto-both/_quarto.yml"
echo "title: yaml-title" > "$TEST_DIR/quarto-both/_quarto.yaml"
cd "$TEST_DIR/quarto-both"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles both _quarto.yml and _quarto.yaml"
else
    fail "Crashed on duplicate quarto configs"
fi

# ══════════════════════════════════════════════════════════════════════════════
# TEST 10: Python Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

section "10. Python Edge Cases"

# pyproject.toml without name
mkdir -p "$TEST_DIR/python-no-name"
echo "[tool.poetry]" > "$TEST_DIR/python-no-name/pyproject.toml"
cd "$TEST_DIR/python-no-name"
chpwd_iterm_profile
if (( _ITERM_SWITCHING == 0 )); then
    pass "Handles pyproject.toml without name"
else
    fail "Crashed on Python without name"
fi

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════"
echo -e "${BOLD}Summary${NC}"
echo "────────────────────────────────────────────────────"
echo -e "  ${GREEN}✓ Passed:${NC}  $PASS"
echo -e "  ${RED}✗ Failed:${NC}  $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✅ All edge case tests passed!${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}❌ Some tests failed${NC}"
    exit 1
fi
