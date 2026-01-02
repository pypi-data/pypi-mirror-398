#!/bin/zsh
# Run this in your iTerm2 window to diagnose

echo "=== iTerm2 Context Switcher Diagnostics ==="
echo ""

echo "1. Terminal environment:"
echo "   TERM_PROGRAM: $TERM_PROGRAM"
echo "   ITERM_SESSION_ID: $ITERM_SESSION_ID"
echo ""

echo "2. Integration loaded?"
if typeset -f _iterm_detect_context > /dev/null; then
    echo "   ✅ _iterm_detect_context function exists"
else
    echo "   ❌ _iterm_detect_context NOT found"
    echo "   Try: source ~/.config/zsh/.zshrc"
fi
echo ""

echo "3. Hook registered?"
if [[ " ${chpwd_functions[*]} " == *" _iterm_detect_context "* ]]; then
    echo "   ✅ Hook is registered"
else
    echo "   ❌ Hook NOT registered"
fi
echo ""

echo "4. Current profile cache: $_ITERM_CURRENT_PROFILE"
echo ""

echo "5. Testing profile switch manually..."
echo "   Sending: SetProfile=R-Dev"
printf '\033]1337;SetProfile=R-Dev\007'
echo ""
echo "   Did the background turn GREEN? (y/n)"
read answer
if [[ "$answer" == "y" ]]; then
    echo "   ✅ Profile switching works!"
    echo ""
    echo "   Restoring Default..."
    printf '\033]1337;SetProfile=Default\007'
else
    echo "   ❌ Profile switch failed"
    echo ""
    echo "   Checking if R-Dev profile exists..."
    defaults read com.googlecode.iterm2 "New Bookmarks" 2>/dev/null | grep -A1 '"Name" = "R-Dev"' || echo "   R-Dev profile not found in iTerm2"
fi
