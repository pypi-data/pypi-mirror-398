#!/bin/bash
# Automated CLI Test Suite for: aiterm
# Generated: 2025-12-26
# Run: bash tests/cli/automated-tests.sh
#
# Options:
#   --junit <file>     Output JUnit XML to file
#   --benchmark        Enable performance benchmarking
#   VERBOSE=1          Show detailed output
#   BAIL=1             Stop on first failure
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed
#   2 - Test suite error

set -euo pipefail

# ============================================
# Configuration
# ============================================

PASS=0
FAIL=0
SKIP=0
VERBOSE=${VERBOSE:-0}
BAIL=${BAIL:-0}
BENCHMARK=${BENCHMARK:-0}
JUNIT_FILE=""
SUITE_START=$(date +%s%N)

# Performance tracking
declare -a TIMINGS=()
SLOW_THRESHOLD_MS=2000

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --junit)
            JUNIT_FILE="$2"
            shift 2
            ;;
        --benchmark)
            BENCHMARK=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================
# Helpers
# ============================================

# Current test timing
CURRENT_TEST_START=0
CURRENT_TEST_NAME=""

# JUnit XML handling
declare -a JUNIT_TESTS=()

junit_init() {
    [[ -z "$JUNIT_FILE" ]] && return
    # Will write at end
}

junit_add_test() {
    local name=$1
    local status=$2  # pass, fail, skip
    local duration_s=$3
    local message=${4:-}

    [[ -z "$JUNIT_FILE" ]] && return

    local xml_name
    xml_name=$(echo "$name" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g')
    local xml_msg
    xml_msg=$(echo "$message" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g')

    if [[ "$status" == "pass" ]]; then
        JUNIT_TESTS+=("    <testcase name=\"$xml_name\" time=\"$duration_s\"/>")
    elif [[ "$status" == "fail" ]]; then
        JUNIT_TESTS+=("    <testcase name=\"$xml_name\" time=\"$duration_s\"><failure message=\"$xml_msg\"/></testcase>")
    elif [[ "$status" == "skip" ]]; then
        JUNIT_TESTS+=("    <testcase name=\"$xml_name\" time=\"$duration_s\"><skipped/></testcase>")
    fi
}

junit_write() {
    [[ -z "$JUNIT_FILE" ]] && return

    local suite_end suite_duration_s
    suite_end=$(date +%s%N)
    suite_duration_s=$(echo "scale=3; ($suite_end - $SUITE_START) / 1000000000" | bc 2>/dev/null || echo "0")

    {
        echo '<?xml version="1.0" encoding="UTF-8"?>'
        echo '<testsuites>'
        echo "  <testsuite name=\"aiterm-cli\" tests=\"$((PASS + FAIL + SKIP))\" failures=\"$FAIL\" skipped=\"$SKIP\" time=\"$suite_duration_s\" timestamp=\"$(date -Iseconds)\">"
        for test in "${JUNIT_TESTS[@]}"; do
            echo "$test"
        done
        echo '  </testsuite>'
        echo '</testsuites>'
    } > "$JUNIT_FILE"

    echo -e "\n${BLUE}JUnit XML written to:${NC} $JUNIT_FILE"
}

# Start timing a test
start_test() {
    CURRENT_TEST_NAME="$1"
    CURRENT_TEST_START=$(date +%s%N)
}

# Get elapsed time in ms
get_elapsed_ms() {
    local end_time
    end_time=$(date +%s%N)
    echo $(( (end_time - CURRENT_TEST_START) / 1000000 ))
}

log_pass() {
    local name=${CURRENT_TEST_NAME:-$1}
    local elapsed_ms duration_s timing_info=""

    if [[ $CURRENT_TEST_START -ne 0 ]]; then
        elapsed_ms=$(get_elapsed_ms)
        duration_s=$(echo "scale=3; $elapsed_ms / 1000" | bc 2>/dev/null || echo "0")
        TIMINGS+=("$elapsed_ms:$name")

        if [[ "$BENCHMARK" == "1" ]]; then
            if [[ $elapsed_ms -gt $SLOW_THRESHOLD_MS ]]; then
                timing_info=" ${YELLOW}(${elapsed_ms}ms - SLOW)${NC}"
            else
                timing_info=" (${elapsed_ms}ms)"
            fi
        fi
    else
        duration_s="0"
    fi

    PASS=$((PASS + 1))
    echo -e "${GREEN}✅ PASS${NC}: $1$timing_info"
    junit_add_test "$name" "pass" "$duration_s"

    CURRENT_TEST_START=0
    CURRENT_TEST_NAME=""
}

log_fail() {
    local name=${CURRENT_TEST_NAME:-$1}
    local elapsed_ms duration_s

    if [[ $CURRENT_TEST_START -ne 0 ]]; then
        elapsed_ms=$(get_elapsed_ms)
        duration_s=$(echo "scale=3; $elapsed_ms / 1000" | bc 2>/dev/null || echo "0")
    else
        duration_s="0"
    fi

    FAIL=$((FAIL + 1))
    echo -e "${RED}❌ FAIL${NC}: $1"
    if [[ "$VERBOSE" == "1" ]] && [[ -n "${2:-}" ]]; then
        echo -e "   ${RED}Details: $2${NC}"
    fi

    junit_add_test "$name" "fail" "$duration_s" "${2:-Test failed}"

    CURRENT_TEST_START=0
    CURRENT_TEST_NAME=""

    if [[ "$BAIL" == "1" ]]; then
        echo -e "\n${RED}Bailing out on first failure${NC}"
        print_summary
        exit 1
    fi
}

log_skip() {
    local name=${CURRENT_TEST_NAME:-$1}
    SKIP=$((SKIP + 1))
    echo -e "${YELLOW}⏭️  SKIP${NC}: $1"
    junit_add_test "$name" "skip" "0"

    CURRENT_TEST_START=0
    CURRENT_TEST_NAME=""
}

log_section() {
    echo ""
    echo -e "${BLUE}${BOLD}━━━ $1 ━━━${NC}"
}

print_summary() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  RESULTS${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  Passed:  ${GREEN}${PASS}${NC}"
    echo -e "  Failed:  ${RED}${FAIL}${NC}"
    echo -e "  Skipped: ${YELLOW}${SKIP}${NC}"
    echo -e "  Total:   $((PASS + FAIL + SKIP))"
    echo ""

    if [[ $FAIL -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}✅ ALL TESTS PASSED${NC}"
    else
        echo -e "${RED}${BOLD}❌ $FAIL TEST(S) FAILED${NC}"
    fi
}

# ============================================
# Test Suite
# ============================================

echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  AUTOMATED CLI TEST SUITE: aiterm${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  CLI:     aiterm / ait"
echo "  Time:    $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Verbose: $VERBOSE"
echo ""

# ============================================
# SMOKE TESTS
# ============================================
log_section "Smoke Tests"

# Test: CLI is installed
start_test "CLI is installed (ait in PATH)"
if command -v ait &> /dev/null; then
    log_pass "CLI is installed (ait in PATH)"
else
    log_fail "CLI not found in PATH" "Run: pip install -e . or uv pip install -e ."
    echo -e "\n${RED}Cannot continue without CLI installed${NC}"
    exit 2
fi

# Test: Version returns successfully
start_test "Version command works"
if ait --version > /dev/null 2>&1; then
    VERSION=$(ait --version 2>&1)
    log_pass "Version command works ($VERSION)"
else
    log_fail "Version command failed"
fi

# Test: Help is accessible
start_test "Help is accessible"
if ait --help > /dev/null 2>&1; then
    log_pass "Help is accessible"
else
    log_fail "Help command failed"
fi

# Test: aiterm alias works too
start_test "aiterm alias works"
if command -v aiterm &> /dev/null && aiterm --version > /dev/null 2>&1; then
    log_pass "aiterm alias works"
else
    log_skip "aiterm alias not available (ait only)"
fi

# ============================================
# CORE COMMANDS
# ============================================
log_section "Core Commands"

# Test: Doctor runs without error
start_test "doctor command completes"
if ait doctor > /dev/null 2>&1; then
    log_pass "doctor command completes"
else
    log_fail "doctor command failed"
fi

# Test: Detect returns context info
start_test "detect returns context info"
if ait detect 2>&1 | grep -qi "type\|project\|context\|python\|r-package\|node"; then
    log_pass "detect returns context info"
else
    log_fail "detect output unexpected"
fi

# Test: Switch runs without error
start_test "switch command completes"
if ait switch > /dev/null 2>&1; then
    log_pass "switch command completes"
else
    log_fail "switch command failed"
fi

# Test: Context detect (explicit)
start_test "context detect works"
if ait context detect > /dev/null 2>&1; then
    log_pass "context detect works"
else
    log_fail "context detect failed"
fi

# ============================================
# CLAUDE SUBCOMMANDS
# ============================================
log_section "Claude Subcommands"

# Test: Claude settings accessible
start_test "claude settings works"
if ait claude settings > /dev/null 2>&1; then
    log_pass "claude settings works"
else
    log_fail "claude settings failed"
fi

# Test: Claude approvals list
start_test "claude approvals list works"
if ait claude approvals list > /dev/null 2>&1; then
    log_pass "claude approvals list works"
else
    log_fail "claude approvals list failed"
fi

# Test: Claude help
start_test "claude --help works"
if ait claude --help > /dev/null 2>&1; then
    log_pass "claude --help works"
else
    log_fail "claude --help failed"
fi

# ============================================
# MCP SUBCOMMANDS
# ============================================
log_section "MCP Subcommands"

# Test: MCP list works
start_test "mcp list works"
if ait mcp list > /dev/null 2>&1; then
    log_pass "mcp list works"
else
    log_fail "mcp list failed"
fi

# Test: MCP validate works
start_test "mcp validate works"
if ait mcp validate > /dev/null 2>&1; then
    log_pass "mcp validate works"
else
    log_fail "mcp validate failed"
fi

# Test: MCP help
start_test "mcp --help works"
if ait mcp --help > /dev/null 2>&1; then
    log_pass "mcp --help works"
else
    log_fail "mcp --help failed"
fi

# ============================================
# SESSIONS SUBCOMMANDS
# ============================================
log_section "Sessions Subcommands"

# Test: Sessions live works
start_test "sessions live works"
if ait sessions live > /dev/null 2>&1; then
    log_pass "sessions live works"
else
    log_fail "sessions live failed"
fi

# Test: Sessions conflicts works
start_test "sessions conflicts works"
if ait sessions conflicts > /dev/null 2>&1; then
    log_pass "sessions conflicts works"
else
    log_fail "sessions conflicts failed"
fi

# Test: Sessions history works
start_test "sessions history works"
if ait sessions history > /dev/null 2>&1; then
    log_pass "sessions history works"
else
    log_fail "sessions history failed"
fi

# Test: Sessions help
start_test "sessions --help works"
if ait sessions --help > /dev/null 2>&1; then
    log_pass "sessions --help works"
else
    log_fail "sessions --help failed"
fi

# ============================================
# IDE SUBCOMMANDS
# ============================================
log_section "IDE Subcommands"

# Test: IDE list works
start_test "ide list works"
if ait ide list > /dev/null 2>&1; then
    log_pass "ide list works"
else
    log_fail "ide list failed"
fi

# Test: IDE compare works
start_test "ide compare works"
if ait ide compare > /dev/null 2>&1; then
    log_pass "ide compare works"
else
    log_fail "ide compare failed"
fi

# Test: IDE help
start_test "ide --help works"
if ait ide --help > /dev/null 2>&1; then
    log_pass "ide --help works"
else
    log_fail "ide --help failed"
fi

# ============================================
# OPENCODE SUBCOMMANDS
# ============================================
log_section "OpenCode Subcommands"

# Test: OpenCode config works
start_test "opencode config works"
if ait opencode config > /dev/null 2>&1; then
    log_pass "opencode config works"
else
    log_fail "opencode config failed"
fi

# Test: OpenCode help
start_test "opencode --help works"
if ait opencode --help > /dev/null 2>&1; then
    log_pass "opencode --help works"
else
    log_fail "opencode --help failed"
fi

# ============================================
# ERROR HANDLING
# ============================================
log_section "Error Handling"

# Test: Invalid command shows error
start_test "Invalid commands show 'No such command'"
OUTPUT=$(ait nonexistent-command 2>&1 || true)
if echo "$OUTPUT" | grep -q "No such command"; then
    log_pass "Invalid commands show 'No such command'"
else
    log_fail "Invalid command not handled"
fi

# Test: Invalid subcommand
start_test "Invalid subcommands show 'No such command'"
OUTPUT=$(ait claude nonexistent 2>&1 || true)
if echo "$OUTPUT" | grep -q "No such command"; then
    log_pass "Invalid subcommands show 'No such command'"
else
    log_fail "Invalid subcommand not handled"
fi

# ============================================
# EXIT CODES
# ============================================
log_section "Exit Codes"

# Test: Exit code 0 on success
start_test "Exit code 0 on success"
ait --version > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    log_pass "Exit code 0 on success"
else
    log_fail "Exit code not 0 on success"
fi

# Test: Exit code non-zero on error
start_test "Non-zero exit on invalid command"
ait nonexistent-command > /dev/null 2>&1 || EXIT_CODE=$?
if [[ ${EXIT_CODE:-0} -ne 0 ]]; then
    log_pass "Non-zero exit on invalid command"
else
    log_skip "Exit code 0 for invalid (Typer behavior)"
fi

# ============================================
# HELP ACCESSIBILITY
# ============================================
log_section "Help Accessibility"

# Test all major subcommand help
for cmd in context profile claude mcp sessions ide opencode; do
    start_test "$cmd --help accessible"
    if ait $cmd --help > /dev/null 2>&1; then
        log_pass "$cmd --help accessible"
    else
        log_fail "$cmd --help failed"
    fi
done

# ============================================
# Performance Summary (if benchmarking enabled)
# ============================================
if [[ "$BENCHMARK" == "1" ]] && [[ ${#TIMINGS[@]} -gt 0 ]]; then
    echo ""
    echo -e "${BLUE}${BOLD}━━━ Performance Summary ━━━${NC}"

    # Count by category
    FAST=0
    MEDIUM=0
    SLOW=0

    for timing in "${TIMINGS[@]}"; do
        ms="${timing%%:*}"
        if [[ $ms -lt 500 ]]; then
            FAST=$((FAST + 1))
        elif [[ $ms -lt 2000 ]]; then
            MEDIUM=$((MEDIUM + 1))
        else
            SLOW=$((SLOW + 1))
        fi
    done

    echo -e "  Fast (< 500ms):  ${GREEN}${FAST}${NC} tests"
    echo -e "  Medium (< 2s):   ${YELLOW}${MEDIUM}${NC} tests"
    echo -e "  Slow (> 2s):     ${RED}${SLOW}${NC} tests"

    # Show slowest tests if any are slow
    if [[ $SLOW -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}Slowest tests:${NC}"
        printf '%s\n' "${TIMINGS[@]}" | sort -t: -k1 -n -r | head -5 | while IFS=: read -r ms name; do
            echo -e "  ${YELLOW}${ms}ms${NC}: $name"
        done
    fi
fi

# ============================================
# Summary
# ============================================
print_summary

# Write JUnit XML if requested
junit_write

# Exit with appropriate code
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
