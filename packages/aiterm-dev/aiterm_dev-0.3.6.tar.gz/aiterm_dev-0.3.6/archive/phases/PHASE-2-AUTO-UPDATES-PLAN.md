# Phase 2: Documentation Auto-Updates Implementation Plan

**Date:** 2025-12-24
**Status:** Planning
**Predecessor:** Phase 0 (Documentation Complete ✅), Phase 1 (Detection Complete ✅)

---

## Overview

Phase 2 implements **automatic documentation updates** for the aiterm project, leveraging the proven workflow plugin auto-update system that was successfully implemented and tested on the workflow and aiterm projects.

**Goal:** Automate documentation maintenance so that CHANGELOG.md, CLAUDE.md, and mkdocs.yml stay current without manual effort.

**Time Savings:** ~15 minutes per session → ~30 seconds (97% reduction)

---

## Background: Proven Success

### Workflow Plugin Auto-Update System

**Location:** `~/.claude/commands/workflow/lib/`

**Scripts Created:**
1. `update-changelog.sh` (441 lines) - CHANGELOG generation from git commits
2. `update-mkdocs-nav.sh` (366 lines) - mkdocs.yml navigation sync
3. `update-claude-md.sh` (297 lines) - .STATUS/CLAUDE.md updates
4. `run-all-updaters.sh` (306 lines) - Master orchestrator

**Total:** 1,410 lines of production-ready shell scripts

**Features:**
- ✅ Parses 9 conventional commit types
- ✅ Groups into 7 CHANGELOG sections
- ✅ Auto-generates GitHub commit links
- ✅ Detects orphaned docs
- ✅ Infers sections from 11 filename patterns
- ✅ Creates timestamped backups
- ✅ Validates YAML syntax
- ✅ Tests builds before saving
- ✅ Auto-rollback on failures
- ✅ ~10 seconds total execution time

**Usage Modes:**
1. **Interactive** - Confirm each change
2. **Auto** - Apply all updates automatically
3. **Dry-run** - Preview changes without applying

**Integration:**
- Works standalone via CLI
- Integrated into `/workflow:done` command (Step 1.6)
- Used successfully on both workflow and aiterm projects

---

## Phase 2 Goals for aiterm

### Primary Objectives

1. **Leverage Existing Scripts**
   - Use proven workflow plugin updaters
   - No reinvention - adapt, don't rewrite
   - Maintain compatibility with workflow plugin

2. **Customize for aiterm**
   - Adjust section patterns for Python/CLI project
   - Add aiterm-specific metadata handling
   - Support both dev and main branches

3. **Seamless Integration**
   - Add to aiterm's `/workflow:done` (if exists)
   - Or create standalone `aiterm update-docs` command
   - Work in both CLI and development modes

4. **ADHD-Friendly**
   - Fast execution (< 30 seconds)
   - Clear visual feedback
   - Actionable confirmations
   - No decision paralysis

---

## Architecture

### Option A: Symlink to Workflow Scripts (Recommended ⭐)

**Approach:** Use workflow plugin scripts directly via symlinks

**Structure:**
```
aiterm/
├── scripts/
│   └── update-docs.sh          # Wrapper script
│       → Calls ~/.claude/commands/workflow/lib/run-all-updaters.sh
├── .aiterm-doc-config.json    # aiterm-specific config
└── CLAUDE.md
```

**Pros:**
- ✅ Zero duplication
- ✅ Automatic improvements from workflow plugin
- ✅ Tested and proven
- ✅ Easy to maintain

**Cons:**
- ❌ Dependency on workflow plugin location
- ❌ Less customization freedom

---

### Option B: Copy and Customize (Alternative)

**Approach:** Copy scripts to aiterm, customize for Python project

**Structure:**
```
aiterm/
├── scripts/
│   ├── update-changelog.sh     # Copied + customized
│   ├── update-mkdocs-nav.sh    # Copied + customized
│   ├── update-claude-md.sh     # Copied + customized
│   └── run-all-updaters.sh     # Copied + customized
└── .aiterm-doc-config.json
```

**Pros:**
- ✅ Full customization control
- ✅ No external dependencies
- ✅ Can diverge if needed

**Cons:**
- ❌ Duplication (~1,400 lines)
- ❌ Must manually sync improvements
- ❌ More maintenance burden

---

### Recommended: **Option A (Symlink)**

**Rationale:**
- Workflow plugin updaters are **generic** - work on any git repo with docs
- aiterm and workflow plugin are both maintained by DT
- Improvements to workflow benefit aiterm automatically
- Less code to maintain
- Proven to work on aiterm already (we used them today!)

**Implementation:**
```bash
# Create wrapper script
cat > scripts/update-docs.sh <<'EOF'
#!/bin/bash
# Wrapper for workflow plugin auto-updaters
# Applies aiterm-specific configuration

# Load aiterm config if exists
if [ -f ".aiterm-doc-config.json" ]; then
    export DOC_CONFIG=".aiterm-doc-config.json"
fi

# Run workflow plugin updaters
~/.claude/commands/workflow/lib/run-all-updaters.sh "$@"
EOF

chmod +x scripts/update-docs.sh
```

---

## Configuration: `.aiterm-doc-config.json`

**Purpose:** aiterm-specific customization for workflow updaters

**Format:**
```json
{
  "project_name": "aiterm",
  "project_type": "python-cli",
  "changelog": {
    "sections": [
      "Breaking Changes",
      "Features",
      "Bug Fixes",
      "Documentation",
      "Testing",
      "Build System",
      "Other"
    ],
    "commit_types": {
      "feat": "Features",
      "fix": "Bug Fixes",
      "docs": "Documentation",
      "test": "Testing",
      "build": "Build System",
      "ci": "Build System",
      "refactor": "Other",
      "style": "Other",
      "chore": "Other"
    },
    "exclude_patterns": [
      "^Merge branch",
      "^Merge pull request",
      "WIP:",
      "temp:"
    ]
  },
  "mkdocs": {
    "section_patterns": {
      "getting-started": ["install", "quick", "setup"],
      "guides": ["guide", "tutorial", "how-to"],
      "reference": ["api", "commands", "config"],
      "architecture": ["architecture", "design", "implementation"],
      "troubleshooting": ["troubleshoot", "debug", "error"]
    },
    "auto_add_orphans": true,
    "validate_build": true
  },
  "claude_md": {
    "update_progress": true,
    "prepend_to_section": "Just Completed",
    "max_entries": 10
  }
}
```

---

## Implementation Plan

### Phase 2.1: Setup & Configuration (2 hours)

**Tasks:**
1. ✅ Review workflow plugin updaters
2. Create `scripts/update-docs.sh` wrapper
3. Create `.aiterm-doc-config.json`
4. Test wrapper calls workflow scripts correctly
5. Verify config is loaded

**Deliverables:**
- `scripts/update-docs.sh` executable
- `.aiterm-doc-config.json` with aiterm settings
- Test run showing all 3 updaters work

---

### Phase 2.2: CHANGELOG Auto-Generation (1 hour)

**Tasks:**
1. Review current CHANGELOG.md format
2. Test `update-changelog.sh` on aiterm
3. Adjust config for Python commit patterns
4. Verify [Unreleased] section handling
5. Test backup creation

**Expected Behavior:**
```bash
$ scripts/update-docs.sh --changelog --dry-run

📝 CHANGELOG Update Preview
═══════════════════════════════════════════

Found 5 new commits since last update:

Features (2):
  • feat: add mcp list command (68d92eb)
  • feat: create diagnostic flowchart (68d92eb)

Documentation (3):
  • docs: fix version mismatches (68d92eb)
  • docs: enhance Phase 0 documentation (68d92eb)
  • docs: update last modified dates (68d92eb)

Would add to CHANGELOG.md [Unreleased] section

Apply changes? [y/N]
```

**Success Criteria:**
- ✅ Conventional commits parsed correctly
- ✅ Commits grouped by type
- ✅ GitHub links generated
- ✅ [Unreleased] section updated
- ✅ Backup created before changes

---

### Phase 2.3: mkdocs Navigation Sync (1 hour)

**Tasks:**
1. Test `update-mkdocs-nav.sh` on aiterm
2. Verify section pattern matching
3. Test orphaned page detection
4. Verify YAML validation
5. Test `mkdocs build --strict` before saving

**Expected Behavior:**
```bash
$ scripts/update-docs.sh --mkdocs --dry-run

🗂️  mkdocs.yml Navigation Update
═══════════════════════════════════════════

Orphaned pages detected: 0
All pages properly linked ✓

Navigation structure:
  ✓ Home: index.md
  ✓ Getting Started (2 pages)
  ✓ User Guide (6 pages)
  ✓ Reference (4 pages)
  ✓ Architecture (4 pages)
  ✓ Documentation Automation (5 pages)

YAML validation: PASSED
mkdocs build test: PASSED

No changes needed.
```

**Success Criteria:**
- ✅ Orphaned pages detected
- ✅ Section patterns work
- ✅ YAML validation passes
- ✅ Build test passes
- ✅ Backup created if changes made

---

### Phase 2.4: CLAUDE.md Updates (1 hour)

**Tasks:**
1. Test `update-claude-md.sh` on aiterm
2. Verify "Just Completed" section handling
3. Test progress field updates
4. Test frontmatter preservation
5. Verify commit summary generation

**Expected Behavior:**
```bash
$ scripts/update-docs.sh --claude-md --dry-run

📋 CLAUDE.md Update Preview
═══════════════════════════════════════════

Session Summary (5 commits):
  • Enhanced Phase 0 documentation with diagrams
  • Fixed version mismatches across 7 files
  • Added 5 comprehensive Mermaid diagrams
  • Added diagnostic flowchart
  • Updated documentation deployment

Would prepend to "Just Completed" section:

## ✅ Just Completed (Dec 24, 2024)

**Phase 0 Documentation Complete:**
- ✅ Enhanced architecture with 5 new diagrams
- ✅ Fixed version consistency (0.2.0-dev → 0.1.0-dev)
- ✅ Added diagnostic flowchart to Troubleshooting
- ✅ Deployed to GitHub Pages
- ✅ 22 total diagrams (exceeded 20+ target)

Apply changes? [y/N]
```

**Success Criteria:**
- ✅ Commit summaries generated
- ✅ Frontmatter updated (progress, updated date)
- ✅ "Just Completed" section prepended
- ✅ Existing content preserved
- ✅ Backup created

---

### Phase 2.5: Integration Testing (2 hours)

**Tasks:**
1. Test `run-all-updaters.sh` with all 3 updaters
2. Test interactive mode (confirm each)
3. Test auto mode (apply all)
4. Test dry-run mode (preview only)
5. Test error handling (invalid config, git issues)
6. Test rollback on failures

**Test Scenarios:**

**Scenario 1: Fresh commits, no changes needed**
```bash
$ scripts/update-docs.sh --auto

Running all documentation updaters...

✓ CHANGELOG: Up to date (no new commits)
✓ mkdocs: Up to date (all pages linked)
✓ CLAUDE.md: Up to date (updated recently)

All documentation current. No changes needed.
```

**Scenario 2: Multiple changes needed**
```bash
$ scripts/update-docs.sh

Running all documentation updaters...

📝 CHANGELOG: 5 new commits to add
🗂️  mkdocs: 2 orphaned pages detected
📋 CLAUDE.md: Session summary ready

Review changes:
[1] Preview CHANGELOG changes
[2] Preview mkdocs changes
[3] Preview CLAUDE.md changes
[A] Apply all changes
[S] Skip documentation updates
[Q] Quit

Choice: A

Applying changes...
  ✓ CHANGELOG.md updated (backup: CHANGELOG.md.backup-20251224-173000)
  ✓ mkdocs.yml updated (backup: mkdocs.yml.backup-20251224-173001)
  ✓ CLAUDE.md updated (backup: CLAUDE.md.backup-20251224-173002)

Documentation updated successfully!
```

**Success Criteria:**
- ✅ All 3 modes work (interactive, auto, dry-run)
- ✅ Backups created correctly
- ✅ Rollback works on errors
- ✅ Clear user feedback
- ✅ < 30 seconds execution time

---

### Phase 2.6: Integration with /workflow:done (1 hour)

**Option A: Add to existing /workflow:done (if aiterm has one)**

Add new Step 1.6 (same as workflow plugin):

```markdown
### Step 1.6: Auto-Update Documentation (Optional)

If in a git repository with documentation:

```bash
# Run documentation updaters
if [ -f "scripts/update-docs.sh" ]; then
    echo ""
    echo "🔍 Checking documentation..."
    scripts/update-docs.sh --auto
fi
```

Skip with: `SKIP_DOC_UPDATE=1 /workflow:done`
```

**Option B: Standalone command**

Create `aiterm update-docs` CLI command:

```python
# src/aiterm/cli/docs.py
import typer
from pathlib import Path
import subprocess

app = typer.Typer()

@app.command()
def update(
    dry_run: bool = False,
    auto: bool = False,
    changelog_only: bool = False,
    mkdocs_only: bool = False,
    claude_md_only: bool = False
):
    """Update documentation files automatically"""

    script = Path.home() / "projects/dev-tools/aiterm/scripts/update-docs.sh"

    args = []
    if dry_run:
        args.append("--dry-run")
    if auto:
        args.append("--auto")
    if changelog_only:
        args.append("--changelog")
    if mkdocs_only:
        args.append("--mkdocs")
    if claude_md_only:
        args.append("--claude-md")

    subprocess.run([str(script)] + args)
```

**Recommended:** Both - standalone command + workflow integration

---

## Success Metrics

### Performance
- ✅ Total execution time < 30 seconds
- ✅ CHANGELOG update < 5 seconds
- ✅ mkdocs update < 3 seconds
- ✅ CLAUDE.md update < 2 seconds

### Accuracy
- ✅ 100% of conventional commits parsed correctly
- ✅ 90%+ correct section inference for orphaned docs
- ✅ 0 YAML validation errors
- ✅ 0 mkdocs build failures

### User Experience
- ✅ Clear visual feedback at each step
- ✅ Preview mode shows exactly what will change
- ✅ Interactive mode asks for confirmation
- ✅ Auto mode completes without intervention
- ✅ Backups created for all changes
- ✅ Rollback works on errors

### Documentation Quality
- ✅ CHANGELOG entries comprehensive
- ✅ GitHub links work
- ✅ mkdocs navigation logical
- ✅ CLAUDE.md summaries accurate
- ✅ No duplicate entries

---

## Timeline

### Week 1: Setup & Core Implementation (6 hours)
**Days 1-2:**
- Phase 2.1: Setup (2 hours)
- Phase 2.2: CHANGELOG (1 hour)
- Phase 2.3: mkdocs (1 hour)

**Days 3-4:**
- Phase 2.4: CLAUDE.md (1 hour)
- Phase 2.5: Integration Testing (2 hours)

**Day 5:**
- Phase 2.6: /workflow:done integration (1 hour)

### Week 2: Validation & Documentation (4 hours)
**Days 1-2:**
- Test on real commits
- Refine config based on usage
- Fix any issues

**Days 3-4:**
- Write AUTO-UPDATE-AITERM.md
- Update CLAUDE.md with new feature
- Update README with auto-update info

**Total Time:** ~10 hours over 2 weeks

---

## Risks & Mitigations

### Risk 1: Scripts don't work on aiterm
**Likelihood:** Low (already tested successfully)
**Impact:** Medium
**Mitigation:** Wrapper script allows customization without modifying workflow plugin

### Risk 2: Python project patterns differ
**Likelihood:** Medium
**Impact:** Low
**Mitigation:** `.aiterm-doc-config.json` customizes patterns

### Risk 3: Performance too slow
**Likelihood:** Low (workflow plugin is fast)
**Impact:** Low
**Mitigation:** Profile and optimize if needed

### Risk 4: mkdocs build errors
**Likelihood:** Low (validation before saving)
**Impact:** High (breaks documentation)
**Mitigation:** Auto-rollback on build failure

---

## Deliverables

### Code
- ✅ `scripts/update-docs.sh` - Wrapper script
- ✅ `.aiterm-doc-config.json` - Configuration
- ✅ `src/aiterm/cli/docs.py` - CLI command (optional)

### Documentation
- ✅ `AUTO-UPDATE-AITERM.md` - Usage guide
- ✅ Updated CLAUDE.md - Mention new feature
- ✅ Updated README.md - Quick reference

### Tests
- ✅ Manual test scenarios documented
- ✅ Integration test results
- ✅ Performance benchmarks

---

## Future Enhancements (Phase 3+)

### Phase 3: LLM-Powered Generation
- Use Claude API to generate changelogs from diffs
- Semantic understanding of changes
- Auto-generate documentation from code comments
- Intelligent section placement

### Phase 4: Advanced Features
- Shared content system (`docs/snippets/`)
- Cross-reference validation
- Broken link detection
- Documentation quality scoring
- Version-specific CHANGELOG sections

### Phase 5: Integrations
- IDE plugins (VS Code, Positron)
- Git hooks (pre-commit checks)
- CI/CD pipelines
- GitHub Actions

---

## Decision Points

### Before Starting
1. **Approach:** Option A (symlink) or Option B (copy)?
   - **Recommendation:** Option A (symlink)

2. **Integration:** Standalone command or /workflow:done?
   - **Recommendation:** Both

3. **Timing:** Start Phase 2 now or wait?
   - **Recommendation:** Start now (documentation fresh, momentum)

### During Implementation
1. If scripts need significant modification → Switch to Option B (copy)
2. If performance issues → Profile and optimize
3. If config not sufficient → Add custom logic to wrapper

---

## Next Steps

### Immediate (Today)
1. Review this plan
2. Decide on Option A vs Option B
3. Create `scripts/` directory
4. Copy/link updater scripts

### This Week
1. Implement Phase 2.1-2.4 (core updaters)
2. Test thoroughly
3. Fix any issues
4. Validate on real commits

### Next Week
1. Integrate with /workflow:done
2. Create documentation
3. Test end-to-end workflow
4. Mark Phase 2 complete

---

## Conclusion

Phase 2 builds on the proven success of the workflow plugin auto-update system, adapting it for the aiterm project. By leveraging existing, tested scripts and customizing via configuration, we achieve:

✅ **Fast Implementation** - ~10 hours total
✅ **Proven Reliability** - 1,400 lines of tested code
✅ **Minimal Maintenance** - Improvements flow from workflow plugin
✅ **ADHD-Friendly** - 30 seconds vs 15 minutes per session
✅ **High Quality** - Consistent, accurate documentation

**Ready to start!** 🚀

---

**Status:** Planning Complete - Ready for Implementation
**Estimated Time:** 10 hours over 2 weeks
**Success Probability:** High (proven scripts + clear plan)
