#!/bin/bash
# ait-recap.sh - Quick context gatherer

echo "--- 🔄 RECAP: $(date) ---"
echo ""

echo "📊 GIT STATUS:"
git status -s -b
echo ""

if [ -f "TODOS.md" ]; then
    echo "📝 RECENT TODOS:"
    grep -v "[x]" TODOS.md | head -n 5
    echo ""
fi

echo "🔧 LAST COMMIT:"
git log -1 --oneline
echo ""

echo "💡 SUGGESTION:"
echo "Run 'gemini "[recap] based on this output..."' to get an AI summary."
