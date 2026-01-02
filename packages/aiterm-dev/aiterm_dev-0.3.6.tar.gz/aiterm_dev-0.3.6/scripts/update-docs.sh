#!/bin/bash
# aiterm Documentation Auto-Update Wrapper
# Calls workflow plugin auto-updaters with aiterm-specific configuration
#
# Usage:
#   ./scripts/update-docs.sh                    # Interactive mode
#   ./scripts/update-docs.sh --auto             # Auto mode (no confirmation)
#   ./scripts/update-docs.sh --dry-run          # Preview only
#   ./scripts/update-docs.sh --changelog        # Update CHANGELOG only
#   ./scripts/update-docs.sh --mkdocs           # Update mkdocs.yml only
#   ./scripts/update-docs.sh --claude-md        # Update CLAUDE.md only

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root (assuming script is in scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Workflow plugin updater location
WORKFLOW_UPDATERS="$HOME/.claude/commands/workflow/lib"

# Configuration file
AITERM_CONFIG="$PROJECT_ROOT/.aiterm-doc-config.json"

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  ${BLUE}aiterm Documentation Auto-Update${NC}                     ${CYAN}║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if workflow plugin updaters exist
if [ ! -f "$WORKFLOW_UPDATERS/run-all-updaters.sh" ]; then
    echo -e "${RED}✗ Error: Workflow plugin updaters not found${NC}"
    echo "  Expected location: $WORKFLOW_UPDATERS/run-all-updaters.sh"
    echo ""
    echo "  The workflow plugin may not be installed or is in a different location."
    exit 1
fi

# Check if aiterm config exists
if [ ! -f "$AITERM_CONFIG" ]; then
    echo -e "${YELLOW}⚠ Warning: aiterm config not found${NC}"
    echo "  Expected: $AITERM_CONFIG"
    echo "  Will use default settings from workflow plugin."
    echo ""
fi

# Export config path for workflow updaters to use
export DOC_CONFIG="$AITERM_CONFIG"
export PROJECT_NAME="aiterm"
export PROJECT_TYPE="python-cli"

# Show configuration info
echo -e "${BLUE}📁 Project:${NC} $PROJECT_ROOT"
echo -e "${BLUE}⚙️  Config:${NC} ${AITERM_CONFIG}"
echo -e "${BLUE}🔧 Updaters:${NC} $WORKFLOW_UPDATERS"
echo ""

# Call workflow plugin updaters
echo -e "${GREEN}Running documentation updaters...${NC}"
echo ""

# Pass all arguments to the workflow plugin updater
"$WORKFLOW_UPDATERS/run-all-updaters.sh" "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Documentation update complete!${NC}"
else
    echo ""
    echo -e "${RED}✗ Documentation update failed (exit code: $exit_code)${NC}"
fi

exit $exit_code
