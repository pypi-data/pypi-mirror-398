#!/bin/bash
# ait-done.sh - Task completion wizard

echo "--- ✅ DONE CHECKLIST ---"

# 1. Run Tests
echo "🧪 Running Tests..."
if command -v pytest &> /dev/null; then
    pytest > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   [OK] Tests Passed"
    else
        echo "   [FAIL] Tests Failed! Fix them before committing."
        exit 1
    fi
else
    echo "   [SKIP] Pytest not found"
fi

# 2. Check TODOs
echo "📝 Updating TODOS..."
if [ -f "TODOS.md" ]; then
    echo "   Reminder: Did you mark your task as [x] in TODOS.md?"
fi

# 3. Check Changelog
echo "📄 Checking Changelog..."
if [ -f "CHANGELOG.md" ]; then
    if git diff --name-only | grep -q "CHANGELOG.md"; then
         echo "   [OK] CHANGELOG.md modified."
    else
         echo "   [WARN] No changes to CHANGELOG.md detected."
    fi
fi

# 4. Ready to Commit?
echo ""
echo "🚀 READY TO COMMIT?"
echo "Run: gemini \"[commit] <your summary>\""
