# Phase 2 Design: Documentation Auto-Updates

**Status:** 🎨 DESIGN (Implementation pending)
**Start Date:** 2025-12-21
**Estimated Time:** 4-6 hours
**Goal:** Automatic documentation updates integrated into `/workflow:done`

---

## Overview

Phase 2 extends Phase 1's detection system with **automatic update capabilities**. Instead of just warning about stale documentation, we now **fix it automatically** (with appropriate safeguards).

**Key Principle:** Safe, incremental, ADHD-friendly automation with rollback capability.

---

## Architecture

### Design Philosophy

**Build on Phase 1's Success:**
- Same location: `~/.claude/commands/workflow/lib/`
- Same pattern: Modular shell scripts
- Same interface: Structured output (warnings → actions)
- **NEW:** Add `--apply` flag to each detector for auto-fix mode

**Progressive Application:**
1. **Safe Auto-Updates** (no confirmation): CHANGELOG append, mkdocs.yml nav sync
2. **Interactive Updates** (confirm before): CLAUDE.md edits, file moves
3. **Manual Only** (suggest, don't do): Major refactors, breaking changes

### Integration with `/workflow:done`

Enhanced workflow with auto-updates:

```
Step 1: Gather Session Activity (existing)
  ↓
Step 1.5: Check Documentation Health (Phase 1 - detection)
  ↓
Step 1.6: Apply Safe Auto-Updates (NEW!)
  ↓
Step 1.7: Prompt for Interactive Updates (NEW!)
  ↓
Step 2: Interactive Session Summary (existing)
```

### File Structure

```
~/.claude/commands/workflow/lib/
├── detect-changelog.sh         # Phase 1 (detect mode)
├── detect-claude-md.sh         # Phase 1 (detect mode)
├── detect-divergence.sh        # Phase 1 (detect mode)
├── detect-orphaned.sh          # Phase 1 (detect mode)
├── run-all-detectors.sh        # Phase 1 (detect mode)
│
├── update-changelog.sh         # Phase 2 (NEW - apply mode)
├── update-claude-md.sh         # Phase 2 (NEW - apply mode)
├── update-mkdocs-nav.sh        # Phase 2 (NEW - apply mode)
└── run-all-updaters.sh         # Phase 2 (NEW - orchestrator)
```

**Alternative Design:** Add `--apply` flag to existing detectors instead of separate updater scripts.

**Decision:** **Separate updater scripts** (clearer separation of concerns, safer testing)

---

## Updater 1: CHANGELOG Auto-Generation

### Purpose
Automatically generate CHANGELOG entries from git commits since last update.

### Detection → Update Flow

**Phase 1 Detection:**
```bash
# detect-changelog.sh (existing)
missing_commits=$(git log --oneline $(cat .last-changelog-commit)..HEAD)
if [ -n "$missing_commits" ]; then
  echo "WARNING: 5 commits not in CHANGELOG"
fi
```

**Phase 2 Update:**
```bash
# update-changelog.sh (NEW)
./update-changelog.sh --apply

# What it does:
# 1. Get commits since last CHANGELOG update
# 2. Group by type (feat/fix/docs/chore)
# 3. Format as markdown list
# 4. Insert under "## [Unreleased]" section
# 5. Update .last-changelog-commit marker
```

### Implementation Strategy

**Smart Commit Parsing:**
```bash
#!/bin/bash
# update-changelog.sh

# Get last changelog update
last_update=$(git log -1 --format=%H -- CHANGELOG.md)

# Get commits since then
git log --oneline --format="%h %s" ${last_update}..HEAD | while read commit msg; do
  # Parse conventional commit format
  if [[ $msg =~ ^(feat|fix|docs|chore|test|refactor|perf|build|ci)\(([^)]+)\):[[:space:]]*(.+)$ ]]; then
    type="${BASH_REMATCH[1]}"
    scope="${BASH_REMATCH[2]}"
    subject="${BASH_REMATCH[3]}"

    # Group by type
    case "$type" in
      feat)     echo "### Added";;
      fix)      echo "### Fixed";;
      docs)     echo "### Documentation";;
      chore)    echo "### Maintenance";;
      refactor) echo "### Changed";;
    esac

    echo "- ${subject} (${commit})"
  fi
done
```

**CHANGELOG Template:**
```markdown
## [Unreleased]

### Added
- Hook management wizard (`aiterm hooks create`) (abc1234)
- MCP server validation (`aiterm mcp validate`) (def5678)

### Fixed
- iTerm2 profile switching on macOS Sequoia (ghi9012)

### Documentation
- Phase 2 auto-update design document (jkl3456)

### Maintenance
- Update dependencies to latest versions (mno7890)
```

**Safety Features:**
1. **Backup CHANGELOG** before editing (`CHANGELOG.md.backup`)
2. **Show diff** before applying (if interactive mode)
3. **Git commit** after update (separate from main commit)
4. **Rollback command** if needed (`git checkout CHANGELOG.md`)

### Configuration

**File:** `.changelog-config.json` (optional)
```json
{
  "skip_types": ["chore", "build", "ci"],
  "group_by": "type",
  "include_scope": true,
  "link_commits": true,
  "repo_url": "https://github.com/Data-Wise/aiterm"
}
```

### Success Criteria
- ✅ 80%+ of commits auto-added to CHANGELOG
- ✅ Conventional commit format detected correctly
- ✅ No duplicate entries
- ✅ No data loss (backup + rollback)
- ✅ < 5 seconds execution time

---

## Updater 2: CLAUDE.md Section Updates

### Purpose
Automatically update specific sections of CLAUDE.md based on detected changes.

### Safe vs. Interactive Updates

**Safe Auto-Updates (no confirmation):**
- Append to "## ✅ Recently Completed" section
- Update "progress:" field in header
- Update "updated:" date field
- Increment version numbers (patch only)

**Interactive Updates (require confirmation):**
- Modify "## Current Focus" section (might conflict with user's plan)
- Update feature lists (might misrepresent capabilities)
- Add new sections (might break structure)

### Implementation Strategy

**Template-Based Updates:**
```bash
#!/bin/bash
# update-claude-md.sh

update_completed_section() {
  local session_summary="$1"

  # Find "## ✅ Recently Completed" section
  # Insert new entry at top (reverse chronological)

  cat >> CLAUDE.md.tmp <<EOF
## ✅ Recently Completed ($(date +%Y-%m-%d))
${session_summary}

EOF
}

update_progress() {
  local new_progress="$1"  # 0-100

  # Update "progress:" field in frontmatter
  sed -i.backup "s/^progress: .*/progress: ${new_progress}/" CLAUDE.md
}

update_version() {
  local new_version="$1"

  # Update "version:" field
  sed -i.backup "s/^version: .*/version: ${new_version}/" CLAUDE.md
}
```

**Content Generation:**
Use session data from `/workflow:done`:
```bash
# Input from /workflow:done
session_data=$(cat <<EOF
Files changed: 12
Commits: 3
Features: Hook management wizard, MCP validator
Tests: 15 new tests added
EOF
)

# Transform to CLAUDE.md format
format_for_claude_md() {
  echo "- ✅ **Implemented Hook Management** (3 commits, 12 files)"
  echo "  - Created interactive wizard (\`aiterm hooks create\`)"
  echo "  - Added 9 hook templates (PreToolUse, PostToolUse, etc.)"
  echo "  - Wrote 15 tests for hook validation"
}
```

### Safety Features
1. **Section boundary detection** (don't overwrite wrong section)
2. **Backup before edit** (`CLAUDE.md.backup`)
3. **Dry-run mode** (`--dry-run` to preview changes)
4. **Interactive confirmation** for risky edits
5. **Git diff preview** before committing

### Success Criteria
- ✅ 90% of session completions auto-update CLAUDE.md
- ✅ No section boundaries violated
- ✅ No data loss (backup + rollback)
- ✅ User can preview changes before applying

---

## Updater 3: mkdocs.yml Navigation Sync

### Purpose
Automatically add new documentation files to mkdocs.yml navigation.

### Detection → Update Flow

**Phase 1 Detection:**
```bash
# detect-orphaned.sh (existing)
# Find *.md files in docs/ not linked in mkdocs.yml or README
orphaned_files=(docs/PHASE-2-DESIGN.md docs/CLAUDE-MD-GUIDE.md)
echo "WARNING: 2 orphaned files"
```

**Phase 2 Update:**
```bash
# update-mkdocs-nav.sh (NEW)
./update-mkdocs-nav.sh --apply

# What it does:
# 1. Find orphaned files from Phase 1 detector
# 2. Infer navigation placement from file name/content
# 3. Add to appropriate nav section in mkdocs.yml
# 4. Maintain alphabetical order within sections
```

### Smart Placement Logic

**File Name → Nav Section Mapping:**
```bash
infer_nav_section() {
  local filename="$1"

  case "$filename" in
    *API*)           echo "nav.Reference";;
    *ARCHITECTURE*)  echo "nav.Reference";;
    *GUIDE*)         echo "nav.Guides";;
    *USER-GUIDE*)    echo "nav.Guides";;
    *INTEGRATION*)   echo "nav.Guides";;
    *TROUBLESHOOT*)  echo "nav.Guides";;
    *TUTORIAL*)      echo "nav.Tutorials";;
    *QUICKSTART*)    echo "nav.Getting Started";;
    *PHASE*)         echo "nav.Development.Planning";;
    *DESIGN*)        echo "nav.Development.Design";;
    *IMPLEMENTATION*) echo "nav.Development.Implementation";;
    *SUMMARY*)       echo "nav.Development.Reports";;
    *)               echo "nav.Miscellaneous";;
  esac
}
```

**Content-Based Detection (fallback):**
```bash
# If filename ambiguous, check first heading
first_heading=$(head -20 "$file" | grep -m1 "^# " | sed 's/^# //')

if grep -qi "tutorial\|walkthrough\|step-by-step" "$file"; then
  section="nav.Tutorials"
elif grep -qi "troubleshoot\|debug\|error" "$file"; then
  section="nav.Guides"
elif grep -qi "api\|reference\|specification" "$file"; then
  section="nav.Reference"
fi
```

### Implementation Strategy

**YAML Manipulation:**
```bash
#!/bin/bash
# update-mkdocs-nav.sh

# Parse mkdocs.yml (simple approach - line-based)
add_to_nav() {
  local file="$1"
  local section="$2"
  local title="$3"

  # Find section in mkdocs.yml
  # Add entry maintaining alphabetical order

  # Example: Add to "Guides" section
  awk -v file="$file" -v title="$title" '
    /^  - Guides:/ {
      print
      getline
      print "    - " title ": " file
      next
    }
    { print }
  ' mkdocs.yml > mkdocs.yml.tmp

  mv mkdocs.yml.tmp mkdocs.yml
}
```

**Alternative: Use yq (YAML processor):**
```bash
# More robust YAML editing
yq eval ".nav.Guides += [{\"${title}\": \"${file}\"}]" -i mkdocs.yml
```

### Safety Features
1. **Validate YAML syntax** after edit (`yq eval mkdocs.yml`)
2. **Backup mkdocs.yml** before changes
3. **Test build** (`mkdocs build --strict`)
4. **Show diff** before applying
5. **Rollback on build failure**

### Success Criteria
- ✅ 95% of new docs auto-added to nav
- ✅ Correct section placement 90%+ of time
- ✅ Alphabetical order maintained
- ✅ No YAML syntax errors
- ✅ No broken builds

---

## Orchestrator: run-all-updaters.sh

### Purpose
Master script that runs all updaters in correct order with appropriate safeguards.

### Execution Flow

```bash
#!/bin/bash
# run-all-updaters.sh

set -e  # Exit on error

# 1. Run Phase 1 detectors first (warnings only)
echo "🔍 Detecting documentation issues..."
./run-all-detectors.sh > /tmp/detection-report.txt

# 2. Apply safe auto-updates (no confirmation needed)
echo "🤖 Applying safe auto-updates..."

# CHANGELOG (safe - append only)
if grep -q "missing-changelog" /tmp/detection-report.txt; then
  ./update-changelog.sh --apply
  echo "  ✅ CHANGELOG updated"
fi

# mkdocs.yml (safe - append only)
if grep -q "orphaned-page" /tmp/detection-report.txt; then
  ./update-mkdocs-nav.sh --apply
  echo "  ✅ mkdocs.yml navigation updated"
fi

# 3. Prompt for interactive updates (risky - need confirmation)
echo ""
echo "📝 Interactive updates available:"

if grep -q "claude-md-stale" /tmp/detection-report.txt; then
  read -p "  Update CLAUDE.md 'Recently Completed' section? [Y/n] " response
  if [[ "$response" =~ ^[Yy]?$ ]]; then
    ./update-claude-md.sh --apply --section="completed"
    echo "  ✅ CLAUDE.md updated"
  fi
fi

# 4. Validate all changes
echo ""
echo "🔬 Validating changes..."

# Test mkdocs build
if [ -f mkdocs.yml ]; then
  if mkdocs build --strict 2>/dev/null; then
    echo "  ✅ mkdocs build successful"
  else
    echo "  ❌ mkdocs build failed - rolling back"
    git checkout mkdocs.yml
    exit 1
  fi
fi

# 5. Show summary
echo ""
echo "📊 Summary:"
git diff --stat HEAD

# 6. Offer to commit
read -p "Commit documentation updates? [Y/n] " commit_response
if [[ "$commit_response" =~ ^[Yy]?$ ]]; then
  git add CHANGELOG.md CLAUDE.md mkdocs.yml docs/
  git commit -m "docs: auto-update documentation

- CHANGELOG: Added entries for recent commits
- CLAUDE.md: Updated Recently Completed section
- mkdocs.yml: Added new documentation files to navigation

Generated by /workflow:done Phase 2 auto-updater"
  echo "  ✅ Changes committed"
fi
```

### Integration with `/workflow:done`

**Updated `/workflow:done` flow:**
```markdown
# In ~/.claude/commands/workflow/done.md

## Step 1.6: Apply Documentation Auto-Updates

Run Phase 2 auto-updaters:

```bash
cd ~/.claude/commands/workflow/lib
./run-all-updaters.sh
```

**What this does:**
1. ✅ Detects documentation issues (Phase 1)
2. 🤖 Applies safe auto-updates (CHANGELOG, mkdocs.yml)
3. 📝 Prompts for interactive updates (CLAUDE.md)
4. 🔬 Validates changes (mkdocs build test)
5. 📊 Shows summary and offers to commit

**ADHD-Friendly:**
- Fast path: Press Enter to accept defaults
- Clear prompts: Y/n questions (capital = default)
- Visual feedback: Emoji indicators for each step
- Rollback on failure: Git checkout if validation fails
```

---

## Testing Strategy

### Unit Tests (Per Updater)

**test-changelog-updater.sh:**
```bash
#!/bin/bash
# Test CHANGELOG auto-generation

# Setup
mkdir -p /tmp/test-changelog
cd /tmp/test-changelog
git init
echo "# CHANGELOG" > CHANGELOG.md
git add CHANGELOG.md
git commit -m "Initial commit"

# Create test commits
git commit --allow-empty -m "feat: add new feature"
git commit --allow-empty -m "fix: resolve bug"
git commit --allow-empty -m "docs: update README"

# Run updater
~/.claude/commands/workflow/lib/update-changelog.sh --apply

# Verify
if grep -q "add new feature" CHANGELOG.md; then
  echo "✅ Feature commit added"
else
  echo "❌ Feature commit missing"
  exit 1
fi

# Cleanup
cd /
rm -rf /tmp/test-changelog
```

### Integration Tests (Full Flow)

**test-phase2-integration.sh:**
```bash
#!/bin/bash
# Test full Phase 2 workflow

# Setup test project
setup_test_project() {
  mkdir -p /tmp/test-aiterm
  cd /tmp/test-aiterm

  # Create minimal project structure
  git init
  echo "# Test Project" > README.md
  echo "# CHANGELOG" > CHANGELOG.md
  echo "project: test\nstatus: active\nprogress: 50" > .STATUS
  mkdir -p docs
  echo "# New Guide" > docs/NEW-GUIDE.md

  # Create mkdocs.yml
  cat > mkdocs.yml <<EOF
nav:
  - Home: index.md
  - Guides:
    - Existing: guides/existing.md
EOF

  git add .
  git commit -m "Initial project setup"
}

# Simulate session work
simulate_session() {
  # Make some changes
  git commit --allow-empty -m "feat: implement new feature"
  git commit --allow-empty -m "fix: resolve critical bug"
  echo "Some changes" >> README.md
  git add README.md
  git commit -m "docs: update README"
}

# Run Phase 2 updaters
test_auto_updates() {
  ~/.claude/commands/workflow/lib/run-all-updaters.sh --non-interactive

  # Verify CHANGELOG updated
  if grep -q "implement new feature" CHANGELOG.md; then
    echo "✅ CHANGELOG auto-update works"
  else
    echo "❌ CHANGELOG auto-update failed"
    return 1
  fi

  # Verify mkdocs.yml updated
  if grep -q "NEW-GUIDE.md" mkdocs.yml; then
    echo "✅ mkdocs.yml auto-update works"
  else
    echo "❌ mkdocs.yml auto-update failed"
    return 1
  fi
}

# Run tests
setup_test_project
simulate_session
test_auto_updates

# Cleanup
cd /
rm -rf /tmp/test-aiterm
```

### Validation Tests

**test-phase2-safety.sh:**
```bash
#!/bin/bash
# Test safety features (backups, rollbacks)

# Test backup creation
test_backups() {
  # Modify CHANGELOG
  ./update-changelog.sh --apply

  if [ -f CHANGELOG.md.backup ]; then
    echo "✅ Backup created"
  else
    echo "❌ No backup created"
    return 1
  fi
}

# Test rollback on failure
test_rollback() {
  # Break mkdocs.yml
  echo "invalid: yaml: syntax" >> mkdocs.yml

  # Try to update (should fail and rollback)
  if ./update-mkdocs-nav.sh --apply; then
    echo "❌ Should have failed on invalid YAML"
    return 1
  fi

  # Verify rollback
  if ! grep -q "invalid: yaml" mkdocs.yml; then
    echo "✅ Rollback successful"
  else
    echo "❌ Rollback failed"
    return 1
  fi
}
```

---

## Implementation Timeline

### Estimated Effort: 4-6 hours

**Hour 1-2: CHANGELOG Auto-Generation**
- Write `update-changelog.sh` (1 hour)
- Test commit parsing logic (30 min)
- Add backup/rollback safety (30 min)

**Hour 3-4: mkdocs.yml Navigation Sync**
- Write `update-mkdocs-nav.sh` (1 hour)
- Implement smart placement logic (30 min)
- Add YAML validation (30 min)

**Hour 5: CLAUDE.md Section Updates**
- Write `update-claude-md.sh` (45 min)
- Template-based updates (15 min)

**Hour 6: Integration & Testing**
- Write `run-all-updaters.sh` orchestrator (30 min)
- Integration tests (20 min)
- Documentation (10 min)

### Deliverables

**Scripts Created (4 files):**
- `update-changelog.sh` (~150 lines)
- `update-claude-md.sh` (~120 lines)
- `update-mkdocs-nav.sh` (~180 lines)
- `run-all-updaters.sh` (~100 lines)

**Total Code:** ~550 lines of shell scripts

**Tests Created (3 files):**
- `test-changelog-updater.sh`
- `test-mkdocs-updater.sh`
- `test-phase2-integration.sh`

**Documentation:**
- This design document (PHASE-2-DESIGN.md)
- Update PHASE-1-IMPLEMENTATION.md with links to Phase 2
- Update IDEAS.md with Phase 2 completion status

---

## Success Criteria

### Functional Requirements
- ✅ CHANGELOG auto-generates 80%+ of entries correctly
- ✅ mkdocs.yml navigation auto-updates for new files
- ✅ CLAUDE.md sections update without data loss
- ✅ All safety features work (backup, rollback, validation)
- ✅ Integration with `/workflow:done` seamless

### Non-Functional Requirements
- ✅ < 10 seconds total execution time
- ✅ No false positives (wrong section placement)
- ✅ No data loss (all edits reversible)
- ✅ Clear user feedback (progress indicators)
- ✅ ADHD-friendly (fast path, minimal decisions)

### Quality Requirements
- ✅ 100% test coverage for updater logic
- ✅ Integration tests pass
- ✅ Code reviewed and documented
- ✅ Validated on real aiterm project

---

## Future Enhancements (Phase 3)

**LLM-Powered Generation:**
- Use Claude API to generate changelog entries from diffs
- Semantic understanding of changes (not just commit messages)
- Auto-generate CLAUDE.md section summaries
- Full documentation from code comments

**Advanced Features:**
- Shared content system (`docs/snippets/`)
- Cross-reference validation
- Broken link detection
- Documentation quality scoring

**Integration:**
- IDE plugins (VS Code, Positron)
- Git hooks (pre-commit documentation check)
- CI/CD pipeline integration

---

## Appendix: Example Outputs

### CHANGELOG Auto-Generation Example

**Input (Git Commits):**
```
abc1234 feat(hooks): add hook management wizard
def5678 fix(iterm2): resolve profile switching on Sequoia
ghi9012 docs: create Phase 2 design document
jkl3456 test: add integration tests for updaters
mno7890 chore: update dependencies
```

**Output (CHANGELOG.md):**
```markdown
## [Unreleased]

### Added
- Hook management wizard for interactive hook creation ([abc1234](https://github.com/Data-Wise/aiterm/commit/abc1234))

### Fixed
- iTerm2 profile switching compatibility on macOS Sequoia ([def5678](https://github.com/Data-Wise/aiterm/commit/def5678))

### Documentation
- Phase 2 auto-update design document ([ghi9012](https://github.com/Data-Wise/aiterm/commit/ghi9012))

### Tests
- Integration tests for documentation updaters ([jkl3456](https://github.com/Data-Wise/aiterm/commit/jkl3456))

(Note: chore commits excluded by default config)
```

### mkdocs.yml Navigation Example

**Before:**
```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
  - Guides:
    - User Guide: guides/user-guide.md
  - Reference:
    - API: reference/api.md
```

**New File Detected:** `docs/guides/integration-guide.md`

**After (Auto-Updated):**
```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
  - Guides:
    - Integration Guide: guides/integration-guide.md  # NEW - auto-added
    - User Guide: guides/user-guide.md
  - Reference:
    - API: reference/api.md
```

### CLAUDE.md Auto-Update Example

**Before:**
```markdown
## ✅ Recently Completed (2025-12-20)
- Created comprehensive documentation suite (3,800+ lines)
- Deployed to GitHub Pages
```

**Session Summary Input:**
- 3 commits (feat: hooks, fix: iterm2, docs: phase-2)
- 12 files changed
- 550 lines added

**After (Auto-Updated):**
```markdown
## ✅ Recently Completed (2025-12-21)
- ✅ **Implemented Documentation Auto-Updates** (Phase 2)
  - CHANGELOG auto-generation from git commits
  - mkdocs.yml navigation sync for new files
  - CLAUDE.md section updates with safety features
  - 550 lines of updater scripts + tests
  - Full integration with /workflow:done command

## ✅ Recently Completed (2025-12-20)
- Created comprehensive documentation suite (3,800+ lines)
- Deployed to GitHub Pages
```

---

**End of Design Document**
