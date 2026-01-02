#!/bin/bash
# TEST SCRIPT FOR ITERM2 PROFILE SWITCHING
# Run this INSIDE iTerm2 after re-enabling the integration
#
# What to watch:
#   - Terminal background color should change
#   - Badge should appear (if configured in profile)
#   - NO looping (script should complete)

echo "============================================"
echo "iTerm2 Context Switcher - Live Test"
echo "============================================"
echo ""
echo "Press Ctrl+C at any time if you see looping!"
echo ""
sleep 1

echo "1. Going to home directory..."
cd ~
echo "   Current profile should be: Default"
echo "   PWD: $PWD"
sleep 2

echo ""
echo "2. Going to an R package..."
cd ~/projects/r-packages/active/medfit 2>/dev/null || {
    echo "   medfit not found, trying other location..."
    cd ~/projects/r-packages 2>/dev/null
}
echo "   Current profile should be: R-Dev"
echo "   PWD: $PWD"
sleep 2

echo ""
echo "3. Going back home (should restore Default)..."
cd ~
echo "   Current profile should be: Default"
echo "   PWD: $PWD"
sleep 2

echo ""
echo "4. Testing multiple rapid cd commands..."
for i in 1 2 3 4 5; do
    cd /tmp
    cd ~
done
echo "   Completed 10 rapid cd operations"
sleep 1

echo ""
echo "============================================"
echo "TEST COMPLETE - No loops detected!"
echo "============================================"
echo ""
echo "If colors changed correctly and no hangs occurred,"
echo "the integration is working!"
