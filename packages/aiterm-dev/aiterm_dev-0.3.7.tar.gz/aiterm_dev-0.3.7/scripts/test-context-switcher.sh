#!/usr/bin/env zsh

# Test suite for iTerm2 context switcher
# Tests the chpwd_iterm_profile function from zsh/iterm2-integration.zsh

# Removed set -e to see all test results

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
pass() {
    echo "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

fail() {
    echo "${RED}✗${NC} $1"
    echo "  Expected: $2"
    echo "  Got: $3"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

info() {
    echo "${YELLOW}ℹ${NC} $1"
}

# Override it2profile and printf BEFORE sourcing the integration file
# This way they'll be used by the integration script

# Mock it2profile to capture what profile would be set
it2profile() {
    echo "PROFILE_SET:$1"
}

# Track what would be set
_TEST_PROFILE=""
_TEST_TITLE=""

# Disable project detector to use fallback detection
typeset -g _ITERM_HAS_DETECTOR=0

# Source the integration file
INTEGRATION_FILE="$(dirname "$0")/../zsh/iterm2-integration.zsh"

if [[ ! -f "$INTEGRATION_FILE" ]]; then
    echo "${RED}Error:${NC} Cannot find $INTEGRATION_FILE"
    exit 1
fi

info "Loading integration file: $INTEGRATION_FILE"

# Set TERM_PROGRAM so iTerm detection works
export TERM_PROGRAM="iTerm.app"

source "$INTEGRATION_FILE" 2>/dev/null

# Store the real _iterm_git_info before overriding
_real_iterm_git_info=$functions[_iterm_git_info]

# NOW override the functions after sourcing (so we override the real ones)
_iterm_switch_profile() {
    _TEST_PROFILE="$1"
}
_iterm_set_title() {
    _TEST_TITLE="$1"
}
_iterm_set_user_var() { :; }  # No-op
_iterm_set_status_vars() { :; }  # No-op
# Don't mock _iterm_git_info - let it run normally

# Create temporary test directory
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

info "Test directory: $TEST_DIR"
echo ""

# ============================================================================
# TEST 1: R Package Detection
# ============================================================================
echo "Test 1: R package detection (DESCRIPTION file)"

# Setup test environment
mkdir -p "$TEST_DIR/test-r-package"
cat > "$TEST_DIR/test-r-package/DESCRIPTION" <<EOF
Package: testpkg
Title: Test Package
Version: 0.1.0
EOF

# Change to test directory
cd "$TEST_DIR/test-r-package"

# Clear the cache so the function will output again
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""

# Run the function (mocked functions will capture values)
_iterm_detect_context 2>/dev/null

# Check if R-Dev profile was set
if [[ "$_TEST_PROFILE" == "R-Dev" ]]; then
    pass "R-Dev profile set for R package"
else
    fail "R-Dev profile not set for R package" "R-Dev" "$_TEST_PROFILE"
fi

# Check if title contains package name
if [[ "$_TEST_TITLE" == *"📦 testpkg"* ]]; then
    pass "Title set to '📦 testpkg' for R package"
else
    fail "Title not set correctly for R package" "*📦 testpkg*" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 2: Default Fallback
# ============================================================================
echo ""
echo "Test 2: Default fallback (no special files)"

# Setup test environment
mkdir -p "$TEST_DIR/test-default"
cd "$TEST_DIR/test-default"

# Clear cache
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""

# Run the function
_iterm_detect_context 2>/dev/null

# Check if Default profile was set
if [[ "$_TEST_PROFILE" == "Default" ]]; then
    pass "Default profile set for generic directory"
else
    fail "Default profile not set for generic directory" "Default" "$_TEST_PROFILE"
fi

# For default, the title should have no special icons
if [[ "$_TEST_TITLE" != *"📦"* && "$_TEST_TITLE" != *"🐍"* && "$_TEST_TITLE" != *"🔴"* ]]; then
    pass "Title has no special icons for default directory"
else
    fail "Title should have no special icons for default" "No icons" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 3: Python Project Detection
# ============================================================================
echo ""
echo "Test 3: Python project detection (pyproject.toml)"

# Setup test environment
mkdir -p "$TEST_DIR/test-python"
cat > "$TEST_DIR/test-python/pyproject.toml" <<EOF
[project]
name = "mypyapp"
version = "1.0.0"
EOF

# Change to test directory
cd "$TEST_DIR/test-python"
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""
_iterm_detect_context 2>/dev/null

# Check if Python-Dev profile was set
if [[ "$_TEST_PROFILE" == "Python-Dev" ]]; then
    pass "Python-Dev profile set for Python project"
else
    fail "Python-Dev profile not set for Python project" "Python-Dev" "$_TEST_PROFILE"
fi

# Check if title contains Python icon
if [[ "$_TEST_TITLE" == *"🐍"* ]]; then
    pass "Python icon (🐍) set for Python project"
else
    fail "Python icon not set for Python project" "*🐍*" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 4: Node.js Project Detection
# ============================================================================
echo ""
echo "Test 4: Node.js project detection (package.json)"

# Setup test environment
mkdir -p "$TEST_DIR/test-node"
cat > "$TEST_DIR/test-node/package.json" <<EOF
{
  "name": "my-node-app",
  "version": "1.0.0"
}
EOF

# Change to test directory
cd "$TEST_DIR/test-node"
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""
_iterm_detect_context 2>/dev/null

# Check if Node-Dev profile was set
if [[ "$_TEST_PROFILE" == "Node-Dev" ]]; then
    pass "Node-Dev profile set for Node.js project"
else
    fail "Node-Dev profile not set for Node.js project" "Node-Dev" "$_TEST_PROFILE"
fi

# Check if title contains package icon
if [[ "$_TEST_TITLE" == *"📦"* ]]; then
    pass "Package icon (📦) set for Node.js project"
else
    fail "Package icon not set for Node.js project" "*📦*" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 5: MCP Server Detection
# ============================================================================
echo ""
echo "Test 5: MCP server detection (mcp-server/ directory)"

# Setup test environment - MCP detected by mcp-server/ directory
# Don't add package.json as Node.js detection takes precedence
mkdir -p "$TEST_DIR/test-mcp-project/mcp-server"

# Change to test directory
cd "$TEST_DIR/test-mcp-project"
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""
_iterm_detect_context 2>/dev/null

# Check if AI-Session profile was set (MCP uses AI-Session when path contains "mcp")
if [[ "$_TEST_PROFILE" == "AI-Session" ]]; then
    pass "AI-Session profile set for MCP project"
else
    fail "AI-Session profile not set for MCP project" "AI-Session" "$_TEST_PROFILE"
fi

# Check if title contains MCP icon
if [[ "$_TEST_TITLE" == *"🔌"* ]]; then
    pass "MCP icon (🔌) set for MCP project"
else
    fail "MCP icon not set for MCP project" "*🔌*" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 6: Production Path Detection
# ============================================================================
echo ""
echo "Test 6: Production path detection (*/production/*)"

# Setup test environment
mkdir -p "$TEST_DIR/production/app"
cd "$TEST_DIR/production/app"
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""
_iterm_detect_context 2>/dev/null

# Check if Production profile was set
if [[ "$_TEST_PROFILE" == "Production" ]]; then
    pass "Production profile set for production path"
else
    fail "Production profile not set for production path" "Production" "$_TEST_PROFILE"
fi

# Check if title contains warning icon
if [[ "$_TEST_TITLE" == *"🚨"* ]]; then
    pass "Warning icon (🚨) set for production path"
else
    fail "Warning icon not set for production path" "*🚨*" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 7: Git Dirty Indicator
# ============================================================================
echo ""
echo "Test 7: Git dirty indicator (uncommitted changes)"

# Setup test environment with git repo
mkdir -p "$TEST_DIR/test-git-dirty"
cd "$TEST_DIR/test-git-dirty"
git init -q
git config user.email "test@test.com"
git config user.name "Test"
cat > DESCRIPTION <<EOF
Package: dirtypkg
Title: Dirty Package
Version: 0.1.0
EOF
git add DESCRIPTION
git commit -q -m "Initial commit"

# Make uncommitted change
echo "# Modified" >> DESCRIPTION

# Capture output
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""
_iterm_detect_context 2>/dev/null

# Check if dirty indicator appears in title (git shows asterisk for dirty)
if [[ "$_TEST_TITLE" == *"*"* ]]; then
    pass "Dirty indicator (*) shown for uncommitted changes"
else
    fail "Dirty indicator not shown for uncommitted changes" "*" "$_TEST_TITLE"
fi

# ============================================================================
# TEST 8: Quarto Project Detection
# ============================================================================
echo ""
echo "Test 8: Quarto project detection (_quarto.yml)"

# Setup test environment
mkdir -p "$TEST_DIR/test-quarto"
cat > "$TEST_DIR/test-quarto/_quarto.yml" <<EOF
project:
  type: default
  title: "My Quarto Project"
EOF

# Change to test directory
cd "$TEST_DIR/test-quarto"
_ITERM_CURRENT_PROFILE=""
_ITERM_CURRENT_TITLE=""
_iterm_detect_context 2>/dev/null

# Check if R-Dev profile is used (Quarto uses R-Dev now)
if [[ "$_TEST_PROFILE" == "R-Dev" ]]; then
    pass "R-Dev profile set for Quarto project"
else
    fail "R-Dev profile not set for Quarto project" "R-Dev" "$_TEST_PROFILE"
fi

# Check if title contains Quarto icon
if [[ "$_TEST_TITLE" == *"📊"* ]]; then
    pass "Quarto icon (📊) set for Quarto project"
else
    fail "Quarto icon not set for Quarto project" "*📊*" "$_TEST_TITLE"
fi

# ============================================================================
# Test Summary
# ============================================================================
echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Tests run:    $TESTS_RUN"
echo "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo "${RED}Some tests failed.${NC}"
    exit 1
fi
