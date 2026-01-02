#!/bin/bash
# Install iTerm2 context switcher profiles
# Run: bash scripts/install-profiles.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROFILES_SOURCE="$PROJECT_DIR/profiles/context-switcher-profiles.json"
PROFILES_DEST="$HOME/Library/Application Support/iTerm2/DynamicProfiles"

echo "🔧 iTerm2 Context Switcher - Profile Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check if profiles exist
if [[ ! -f "$PROFILES_SOURCE" ]]; then
    echo "❌ Profile file not found: $PROFILES_SOURCE"
    exit 1
fi

# Create destination directory if needed
mkdir -p "$PROFILES_DEST"

# Copy profiles
echo "📦 Installing dynamic profiles..."
cp "$PROFILES_SOURCE" "$PROFILES_DEST/"
echo "   ✓ Copied to: $PROFILES_DEST"
echo

# List installed profiles
echo "📋 Installed profiles:"
grep '"Name"' "$PROFILES_SOURCE" | sed 's/.*"Name" : "\([^"]*\)".*/   • \1/'
echo

# Instructions for manual step
echo "⚠️  IMPORTANT: Manual step required!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "For each profile above, set the title to 'Session Name':"
echo
echo "1. Open iTerm2 → Settings → Profiles"
echo "2. Select each profile (R-Dev, AI-Session, etc.)"
echo "3. Go to General tab"
echo "4. Set 'Title' dropdown to: Session Name"
echo "5. Check: 'Applications in terminal may change title'"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Profile installation complete!"
echo
echo "Add to your .zshrc:"
echo "   source $PROJECT_DIR/zsh/iterm2-integration.zsh"
