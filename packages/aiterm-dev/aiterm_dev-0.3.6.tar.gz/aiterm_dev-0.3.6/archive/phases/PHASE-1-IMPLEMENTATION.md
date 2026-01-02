# Phase 1 Implementation: Documentation Detection & Warnings

**Status:** ✅ COMPLETE
**Start Date:** 2025-12-21
**Completion Date:** 2025-12-21
**Actual Time:** 2.5 hours
**Goal:** Add intelligent documentation detection to `/workflow:done` command

---

## Overview

Enhance `/workflow:done` with smart detection for documentation gaps and staleness. This phase adds **detection and warnings only** - no automatic updates yet (that's Phase 2).

**Key Principle:** ADHD-friendly - quick, visual, actionable warnings without analysis paralysis.

---

## Architecture

### Integration Point

Add new **Step 1.5** to `/workflow:done` between "Gather Session Activity" and "Interactive Session Summary":

```
Step 1: Gather Session Activity (existing)
  ↓
Step 1.5: Check Documentation Health (NEW!)
  ↓
Step 2: Interactive Session Summary (existing, enhanced)
```

### Detection Functions

Four independent detectors, each returns structured warnings:

```typescript
interface DocumentationWarning {
  type: "claude-md" | "orphaned-page" | "readme-divergence" | "missing-changelog"
  severity: "high" | "medium" | "low"
  file: string
  message: string
  suggestion: string
}
```

---

## Detector 1: CLAUDE.md Staleness Detection

### Purpose
Detect when CLAUDE.md hasn't been updated despite significant code/feature changes.

### Detection Method

**Git-based staleness scoring:**

```bash
# 1. Get last CLAUDE.md update
last_claude_update=$(git log -1 --format=%ct CLAUDE.md)

# 2. Get significant changes since then
recent_features=$(git log --since=$last_claude_update --oneline --grep="feat:" --grep="BREAKING" | wc -l)
recent_files=$(git diff --name-only HEAD~$recent_features HEAD | wc -l)

# 3. Score staleness
if [ $recent_features -ge 3 ] || [ $recent_files -ge 10 ]; then
  echo "HIGH: CLAUDE.md may be stale"
fi
```

### Warning Message

```
⚠️  DOCUMENTATION WARNING: CLAUDE.md may be outdated

Last updated: 3 days ago
Since then:
  • 5 feature commits
  • 23 files changed
  • New Homebrew distribution added

💡 Suggestion: Add "What's New" section to CLAUDE.md
   mentioning Homebrew and /workflow:done
```

### Implementation

1. Add `detect_claude_md_staleness()` function to `/workflow:done`
2. Check if CLAUDE.md exists in project
3. Compare git history of CLAUDE.md vs recent commits
4. Return warning if mismatch detected

---

## Detector 2: Orphaned Documentation Pages

### Purpose
Find documentation files (*.md) not linked from mkdocs.yml or README.

### Detection Method

**Two-phase grep approach:**

```bash
# 1. Find all markdown files
all_docs=$(find docs/ -name "*.md" -type f)

# 2. Check each against mkdocs.yml
for doc in $all_docs; do
  if ! grep -q "$doc" mkdocs.yml 2>/dev/null; then
    echo "ORPHAN: $doc"
  fi
done

# 3. Check against README.md links
for doc in $all_docs; do
  basename=$(basename "$doc")
  if ! grep -q "$basename" README.md 2>/dev/null; then
    echo "NOT_LINKED: $doc (not in README)"
  fi
done
```

### Warning Message

```
⚠️  ORPHANED DOCUMENTATION: 2 files not linked

Orphaned pages:
  • docs/advanced/performance.md (not in mkdocs.yml)
  • docs/reference/api.md (not in README.md)

💡 Suggestion: Add to mkdocs.yml navigation or remove if obsolete
```

### Implementation

1. Add `detect_orphaned_docs()` function
2. Check for docs/ directory existence
3. Grep for file references in mkdocs.yml and README.md
4. Return warnings for unlinked files

---

## Detector 3: README/docs Divergence

### Purpose
Detect when README.md and docs/index.md contain different information.

### Detection Method

**Content similarity check:**

```bash
# 1. Extract key sections from both files
readme_install=$(sed -n '/## Install/,/##/p' README.md)
docs_install=$(sed -n '/## Install/,/##/p' docs/index.md)

# 2. Compare using diff
if ! diff -q <(echo "$readme_install") <(echo "$docs_install") >/dev/null; then
  echo "DIVERGENCE: Installation instructions differ"
fi

# 3. Check for version mismatches
readme_version=$(grep -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" README.md | head -1)
docs_version=$(grep -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" docs/index.md | head -1)

if [ "$readme_version" != "$docs_version" ]; then
  echo "VERSION_MISMATCH: README=$readme_version, docs=$docs_version"
fi
```

### Warning Message

```
⚠️  CONTENT DIVERGENCE: README.md vs docs/index.md

Differences detected:
  • Installation instructions differ
  • Version numbers don't match (README: v0.1.0, docs: v0.2.0-dev)

💡 Suggestion: Sync installation instructions and version numbers
```

### Implementation

1. Add `detect_readme_divergence()` function
2. Extract comparable sections (installation, quick start, features)
3. Use diff to compare
4. Return warnings with specific sections that diverged

---

## Detector 4: Missing CHANGELOG Entries

### Purpose
Detect significant commits since last CHANGELOG update that aren't documented.

### Detection Method

**Git log analysis:**

```bash
# 1. Get last CHANGELOG update
last_changelog_update=$(git log -1 --format=%ct CHANGELOG.md)

# 2. Get commits since then
undocumented_commits=$(git log --since=$last_changelog_update --oneline \
  --grep="feat:" --grep="fix:" --grep="BREAKING" --invert-grep --grep="docs:")

# 3. Parse commit types
feat_count=$(echo "$undocumented_commits" | grep -c "feat:" || true)
fix_count=$(echo "$undocumented_commits" | grep -c "fix:" || true)
breaking_count=$(echo "$undocumented_commits" | grep -c "BREAKING" || true)

# 4. Warn if significant
if [ $feat_count -ge 2 ] || [ $breaking_count -ge 1 ]; then
  echo "MISSING_ENTRIES: $feat_count features, $breaking_count breaking changes"
fi
```

### Warning Message

```
⚠️  MISSING CHANGELOG ENTRIES: Recent work not documented

Undocumented since last CHANGELOG update:
  • 3 feature commits
  • 1 breaking change
  • 7 bug fixes

Recent commits:
  • feat: add Homebrew distribution
  • feat: create /workflow:done command
  • BREAKING: rename repository to aiterm

💡 Suggestion: Add [Unreleased] section to CHANGELOG.md
```

### Implementation

1. Add `detect_missing_changelog()` function
2. Compare git log timestamps for CHANGELOG.md vs recent commits
3. Parse commit messages for types (feat, fix, BREAKING)
4. Return warnings with commit list

---

## Integration into /workflow:done

### New Step 1.5: Check Documentation Health

Insert after "Gather Session Activity", before "Interactive Session Summary":

```markdown
### Step 1.5: Check Documentation Health (NEW!)

Run all four detectors:

```bash
# Run detectors (only if in git repo with docs)
warnings=()
warnings+=($(detect_claude_md_staleness))
warnings+=($(detect_orphaned_docs))
warnings+=($(detect_readme_divergence))
warnings+=($(detect_missing_changelog))
```

**Filter warnings by severity:**
- HIGH severity: Show immediately, block flow
- MEDIUM severity: Show in summary
- LOW severity: Mention count only

**Example output:**

```
🔍 Checking documentation health...

⚠️  3 DOCUMENTATION WARNINGS:

HIGH:
  • CLAUDE.md outdated (3 features since last update)

MEDIUM:
  • 2 orphaned docs (not in mkdocs.yml)
  • README/docs divergence (installation section)

Would you like to:
  A) See details and continue
  B) Fix documentation now
  C) Ignore and proceed
```
```

### Enhanced Step 2: Interactive Session Summary

Add documentation warnings section to the summary box:

```
┌─────────────────────────────────────────────────────────────┐
│ 📝 SESSION SUMMARY                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✅ COMPLETED:                                               │
│    • Created /workflow:done command                         │
│    • Added Homebrew distribution                            │
│                                                             │
│ ⚠️  DOCUMENTATION NEEDS ATTENTION:                          │
│    • CLAUDE.md outdated (add Homebrew info)                │
│    • Missing CHANGELOG entries (2 features)                │
│                                                             │
│ 📁 FILES CHANGED: 4 files                                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Does this look right?                                       │
│                                                             │
│ A) Yes - update .STATUS and suggest commit                 │
│ B) Let me edit what was completed                          │
│ C) Skip .STATUS update (just suggest commit)               │
│ D) Cancel (don't save anything)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

Create new directory for detection logic:

```
~/.claude/
├── commands/
│   └── workflow/
│       ├── done.md                    # Main command (updated)
│       └── lib/                       # NEW! Shared functions
│           ├── detect-claude-md.sh
│           ├── detect-orphaned.sh
│           ├── detect-divergence.sh
│           └── detect-changelog.sh
```

**Why separate files?**
- Testable in isolation
- Reusable across commands
- Easier to maintain
- Clear separation of concerns

---

## Implementation Order

### Task 1: Set up infrastructure ✅ (20 min)
- [x] Create `PHASE-1-IMPLEMENTATION.md` (this file)
- [x] Create `~/.claude/commands/workflow/lib/` directory
- [x] Add helper functions (git checks, file existence)

### Task 2: Implement detectors ✅ (70 min)
- [x] `detect-claude-md.sh` - CLAUDE.md staleness (20 min)
- [x] `detect-orphaned.sh` - Orphaned docs (25 min)
- [x] `detect-divergence.sh` - README/docs sync (15 min)
- [x] `detect-changelog.sh` - Missing entries (10 min)

### Task 3: Integrate into /workflow:done ✅ (30 min)
- [x] Add Step 1.5 to done.md
- [x] Enhance Step 2 summary display
- [x] Create master orchestrator (run-all-detectors.sh)
- [x] Test integration

### Task 4: Testing ✅ (30 min)
- [x] Test each detector individually
- [x] Test master orchestrator
- [x] Validated with aiterm project (found 2 real issues!)
- [x] Confirmed ADHD-friendly UX

**Total Actual Time:** 2.5 hours (faster than estimated!)

---

## Success Criteria

### Must Have ✅ ALL COMPLETE
- [x] All 4 detectors working
- [x] Warnings show in `/workflow:done` output
- [x] Clear, actionable suggestions
- [x] Real issues found on aiterm project (2 HIGH warnings)
- [x] < 500ms total detection time

### Should Have ✅ ALL COMPLETE
- [x] Severity-based filtering (HIGH/MEDIUM/LOW)
- [x] Option to skip documentation checks (SKIP_DOC_CHECK=1)
- [x] Visual hierarchy in warnings (colors, sections)

### Nice to Have (Deferred to Phase 2)
- [ ] Detector configuration (enable/disable individual detectors)
- [ ] Custom warning thresholds
- [ ] Project-specific rules

---

## Next Steps (After Phase 1)

### Phase 2: Auto-Updates (4-6 hours)
- Implement CHANGELOG generation
- Auto-update CLAUDE.md sections
- Sync mkdocs.yml navigation
- Link validation and fixing

### Phase 3: AI-Powered (8-12 hours)
- LLM-based doc writing
- Interactive review interface
- Multi-doc consistency
- Screenshot/diagram generation

---

## Notes

- **ADHD-Friendly:** Keep interactions fast (<30 sec), visual, actionable
- **Graceful Degradation:** Work without git, without docs/, without mkdocs.yml
- **No Breaking Changes:** /workflow:done works exactly as before if detectors disabled
- **Future-Proof:** Detection logic reusable for other commands (e.g., pre-commit hook)

---

## References

- Original planning: `IDEAS.md` Phase 2.6
- Roadmap: `ROADMAP.md` Phase 2 Section 4
- Command spec: `~/.claude/commands/workflow/done.md`
