#!/bin/bash
# Interactive CLI Test Suite for: aiterm
# Generated: 2025-12-26
# Run: bash tests/cli/interactive-tests.sh
#
# This suite guides you through manual testing with prompts.
# Use for QA, demos, or validating visual output.

set -euo pipefail

# ============================================
# Configuration
# ============================================

PASS=0
FAIL=0
TOTAL=0
TOTAL_TESTS=27  # Update when adding tests

# Logging
LOG_DIR="${LOG_DIR:-tests/cli/logs}"
mkdir -p "$LOG_DIR" 2>/dev/null || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/interactive-test-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

log "=== Interactive Test Session Started ==="
log "Working directory: $(pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================
# Helpers
# ============================================

print_header() {
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  INTERACTIVE CLI TEST SUITE: aiterm ($TOTAL_TESTS tests)${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  ${BLUE}Keys:${NC} y=pass, n=fail, q=quit"
    echo -e "  ${BLUE}Log:${NC}  $LOG_FILE"
    echo ""
}

run_test() {
    local test_num=$1
    local test_name=$2
    local command=$3
    local expected=$4

    TOTAL=$((TOTAL + 1))

    # Header
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}TEST $test_num/$TOTAL_TESTS: $test_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${BLUE}Command:${NC} $command"
    echo ""

    log "TEST $test_num: $test_name"
    log "  Command: $command"

    # Run command and capture output
    local output
    output=$(bash -c "$command" 2>&1) || true
    log "  Output: $output"

    # Show expected vs actual side by side
    echo -e "${BLUE}EXPECTED:${NC} $expected"
    echo ""
    echo -e "${GREEN}ACTUAL:${NC}"
    echo "$output"
    echo ""

    # Single prompt: pass/fail/quit
    read -p "[y=pass, n=fail, q=quit] " -n 1 -r
    echo ""

    case "$REPLY" in
        [Yy])
            PASS=$((PASS + 1))
            log "  Result: PASS"
            echo -e "${GREEN}✅ PASS${NC}"
            ;;
        [Qq])
            log "User quit at test $test_num"
            echo -e "${YELLOW}Exiting...${NC}"
            print_summary
            exit 0
            ;;
        *)
            FAIL=$((FAIL + 1))
            log "  Result: FAIL"
            echo -e "${RED}❌ FAIL${NC}"
            ;;
    esac
}

print_summary() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  RESULTS: $PASS passed, $FAIL failed (of $TOTAL run)${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"

    if [[ $FAIL -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}🎉 ALL TESTS PASSED!${NC}"
        log "Final: ALL TESTS PASSED ($PASS/$TOTAL)"
    else
        echo -e "${RED}${BOLD}⚠️  $FAIL TEST(S) FAILED${NC}"
        log "Final: $FAIL TESTS FAILED"
    fi

    log "Summary: $PASS passed, $FAIL failed"
    echo -e "Log: ${BLUE}$LOG_FILE${NC}"
    echo ""
}

# ============================================
# Main
# ============================================

print_header

# ============================================
# SMOKE TESTS
# ============================================

run_test 1 "Version Check" \
    "ait --version" \
    "Version string (e.g., 'aiterm 0.3.0')"

run_test 2 "Help Output" \
    "ait --help" \
    "Help text with Commands list showing: doctor, detect, switch, claude, mcp, sessions, ide"

run_test 3 "aiterm Alias" \
    "aiterm --version" \
    "Same version output as 'ait --version'"

# ============================================
# CORE COMMANDS
# ============================================

run_test 4 "Doctor Check" \
    "ait doctor" \
    "System diagnostics with pass/warn status indicators"

run_test 5 "Context Detection" \
    "ait detect" \
    "Project context showing: type (python/r-package/etc), path, git info"

run_test 6 "Context Switch" \
    "ait switch" \
    "Terminal profile applied (may show visual change if iTerm2)"

run_test 7 "Detect with Path" \
    "ait detect ." \
    "Same context info for current directory"

# ============================================
# CLAUDE SUBCOMMANDS
# ============================================

run_test 8 "Claude Settings" \
    "ait claude settings" \
    "Display of ~/.claude/settings.json contents (or message if not found)"

run_test 9 "Claude Approvals List" \
    "ait claude approvals list" \
    "List of auto-approval patterns (may be empty)"

run_test 10 "Claude Backup" \
    "ait claude backup --dry-run 2>/dev/null || ait claude backup" \
    "Backup created or dry-run showing what would be backed up"

# ============================================
# MCP SUBCOMMANDS
# ============================================

run_test 11 "MCP List" \
    "ait mcp list" \
    "List of configured MCP servers (filesystem, statistical-research, etc.)"

run_test 12 "MCP Validate" \
    "ait mcp validate" \
    "Validation results for MCP configuration"

run_test 13 "MCP Test All" \
    "ait mcp test-all" \
    "Status of each MCP server (reachable/unreachable)"

# ============================================
# SESSIONS SUBCOMMANDS
# ============================================

run_test 14 "Sessions Live" \
    "ait sessions live" \
    "Session list OR 'No active sessions' (runs outside Claude Code)"

run_test 15 "Sessions Conflicts" \
    "ait sessions conflicts" \
    "Conflict check OR 'No conflicts' message"

run_test 16 "Sessions History" \
    "ait sessions history" \
    "Archived session dates (grouped by date)"

run_test 17 "Sessions Current" \
    "ait sessions current" \
    "'No active session' (tests run outside Claude Code context)"

# ============================================
# IDE SUBCOMMANDS
# ============================================

run_test 18 "IDE List" \
    "ait ide list" \
    "Table of supported IDEs with installation status"

run_test 19 "IDE Status (VS Code)" \
    "ait ide status vscode" \
    "Detailed VS Code status with config paths"

run_test 20 "IDE Compare" \
    "ait ide compare" \
    "Comparison of configurations across installed IDEs"

run_test 21 "IDE Extensions" \
    "ait ide extensions vscode" \
    "Recommended AI extensions for VS Code"

# ============================================
# OPENCODE SUBCOMMANDS
# ============================================

run_test 22 "OpenCode Config" \
    "ait opencode config" \
    "Current OpenCode configuration (model, MCP servers, etc.)"

run_test 23 "OpenCode Summary" \
    "ait opencode summary" \
    "Complete OpenCode configuration summary"

# ============================================
# ERROR HANDLING
# ============================================

run_test 24 "Invalid Command" \
    "ait nonexistent-command 2>&1" \
    "Error message or usage info (graceful handling)"

run_test 25 "Invalid Subcommand" \
    "ait claude nonexistent 2>&1" \
    "Error message for unknown subcommand"

# ============================================
# VISUAL/TERMINAL FEATURES
# ============================================

run_test 26 "Rich Output Formatting" \
    "ait doctor" \
    "Colored output with tables, checkmarks, emoji"

run_test 27 "Profile Display" \
    "ait profile list 2>/dev/null || echo 'Profile command not implemented'" \
    "List of available terminal profiles"

# ============================================
# Summary
# ============================================

log "=== Session Completed ==="
print_summary
