#!/bin/bash
# Sync standards from zsh-configuration
#
# This script syncs standard templates from the zsh-configuration project
# (source of truth for DT's dev standards) to the aiterm project.
#
# Usage: ./scripts/sync-standards.sh [--dry-run]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SOURCE="$HOME/projects/dev-tools/zsh-configuration/standards"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$SCRIPT_DIR/../standards"

# Parse arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Check source exists
if [[ ! -d "$SOURCE" ]]; then
    echo -e "${RED}❌ Source not found: $SOURCE${NC}"
    echo ""
    echo "The zsh-configuration project needs to be cloned first:"
    echo "  git clone <url> ~/projects/dev-tools/zsh-configuration"
    echo ""
    exit 1
fi

# Check rsync available
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}❌ rsync not found${NC}"
    echo "Install rsync first:"
    echo "  brew install rsync"
    exit 1
fi

# Show what will be synced
echo -e "${BLUE}📦 Standards Sync${NC}"
echo ""
echo "Source: $SOURCE"
echo "Target: $TARGET"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}🔍 DRY RUN MODE (no changes will be made)${NC}"
    echo ""
fi

# Confirm sync (unless dry-run)
if [[ "$DRY_RUN" == "false" ]]; then
    read -p "Continue with sync? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
    echo ""
fi

# Sync directories
DIRS=("adhd" "code" "project" "workflow")
RSYNC_OPTS="-av --delete"

if [[ "$DRY_RUN" == "true" ]]; then
    RSYNC_OPTS="$RSYNC_OPTS --dry-run"
fi

for dir in "${DIRS[@]}"; do
    echo -e "${BLUE}📁 Syncing $dir/...${NC}"

    # Create target directory if it doesn't exist
    mkdir -p "$TARGET/$dir"

    # Sync with rsync
    rsync $RSYNC_OPTS "$SOURCE/$dir/" "$TARGET/$dir/"

    echo ""
done

# Update README timestamp (only if not dry-run)
if [[ "$DRY_RUN" == "false" ]]; then
    README="$TARGET/README.md"

    # Remove old "Last synced" line if exists
    if [[ -f "$README" ]]; then
        sed -i.bak '/^Last synced:/d' "$README" && rm "$README.bak"
    fi

    # Add new timestamp
    echo "" >> "$README"
    echo "Last synced: $(date '+%Y-%m-%d %H:%M:%S')" >> "$README"
fi

# Summary
echo -e "${GREEN}✅ Standards sync complete${NC}"
echo ""

if [[ "$DRY_RUN" == "false" ]]; then
    echo "Next steps:"
    echo "  git add standards/"
    echo "  git commit -m 'chore(standards): sync from zsh-configuration'"
    echo ""
    echo "Updated directories:"
    for dir in "${DIRS[@]}"; do
        file_count=$(find "$TARGET/$dir" -type f | wc -l | xargs)
        echo "  - $dir/ ($file_count files)"
    done
else
    echo "This was a dry run. Run without --dry-run to apply changes."
fi
