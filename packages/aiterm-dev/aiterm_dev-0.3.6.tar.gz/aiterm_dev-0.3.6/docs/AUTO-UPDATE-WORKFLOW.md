# Documentation Auto-Update Workflow Diagrams

**Visual guide to how the auto-update system works**

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Documentation Auto-Update System             │
│                          (Phase 2)                               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────┐
        │     Master Orchestrator                     │
        │     run-all-updaters.sh                     │
        └─────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   CHANGELOG  │ │    mkdocs    │ │   .STATUS    │
│   Updater    │ │   Updater    │ │   Updater    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ CHANGELOG.md │ │ mkdocs.yml   │ │ .STATUS      │
│   Updated    │ │   Updated    │ │  Updated     │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Detailed Flow: run-all-updaters.sh

```
START
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Run Phase 1 Detectors               │
│ • detect-changelog.sh                       │
│ • detect-orphaned.sh                        │
│ • detect-divergence.sh                      │
│ • detect-claude-md.sh                       │
└─────────────────────────────────────────────┘
  │
  │ Output: detection-report.txt
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 2: Safe Auto-Updates                   │
│ (No confirmation needed)                    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ CHANGELOG.md                         │  │
│  │ • Parse git commits                  │  │
│  │ • Group by type (feat/fix/docs)      │  │
│  │ • Create backup                      │  │
│  │ • Insert under [Unreleased]          │  │
│  │ • 5 seconds                          │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ mkdocs.yml                           │  │
│  │ • Find orphaned .md files            │  │
│  │ • Infer navigation section           │  │
│  │ • Create backup                      │  │
│  │ • Add to navigation                  │  │
│  │ • Validate YAML                      │  │
│  │ • 3 seconds                          │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 3: Interactive Updates                 │
│ (Requires user confirmation)                │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ .STATUS / CLAUDE.md                  │  │
│  │                                      │  │
│  │ PROMPT: Update 'Just Completed'     │  │
│  │         section? [Y/n]               │  │
│  │           │                          │  │
│  │           ├─ Yes → Update            │  │
│  │           └─ No → Skip               │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 4: Validation                          │
│ • mkdocs build --strict                     │
│ • Check YAML syntax                         │
│ • Auto-rollback on failure                  │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 5: Summary & Commit                    │
│ • Show git diff --stat                      │
│ • PROMPT: Commit changes? [Y/n]             │
│   └─ Yes → git commit                       │
│   └─ No → Leave staged                      │
└─────────────────────────────────────────────┘
  │
  ▼
DONE
(3 files updated in ~10 seconds)
```

---

## CHANGELOG Updater Flow

```
START: update-changelog.sh
  │
  ▼
┌─────────────────────────────────────┐
│ Get last CHANGELOG update           │
│ • Check .last-changelog-commit      │
│ • Or: git log -1 CHANGELOG.md       │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Get commits since last update       │
│ git log LAST_UPDATE..HEAD           │
└─────────────────────────────────────┘
  │
  │ Example commits:
  │ • abc1234 feat(hooks): add wizard
  │ • def5678 fix(bug): resolve crash
  │ • ghi9012 docs: update guide
  ▼
┌─────────────────────────────────────────────────────┐
│ Parse each commit with regex:                       │
│ type(scope): subject                                │
│                                                     │
│ feat(hooks): add wizard                             │
│  │     │       └─ subject                           │
│  │     └─ scope (optional)                          │
│  └─ type                                            │
└─────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ Group by type:                                      │
│ • feat → SECTION_ADDED                              │
│ • fix → SECTION_FIXED                               │
│ • docs → SECTION_DOCUMENTATION                      │
└─────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ Format entries:                                     │
│ - **scope**: subject (`commit`)                     │
│                                                     │
│ Example:                                            │
│ - **hooks**: add wizard (`abc1234`)                 │
└─────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Generate markdown sections:         │
│                                     │
│ ### Added                           │
│ - **hooks**: add wizard (abc1234)   │
│                                     │
│ ### Fixed                           │
│ - **bug**: resolve crash (def5678)  │
│                                     │
│ ### Documentation                   │
│ - update guide (ghi9012)            │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Insert into CHANGELOG.md:           │
│                                     │
│ ## [Unreleased]                     │
│                                     │
│ ### Added                           │
│ - **hooks**: add wizard             │
│                                     │
│ ### Fixed                           │
│ - **bug**: resolve crash            │
│                                     │
│ ## [0.1.0] - 2025-12-15             │
│ (existing entries)                  │
└─────────────────────────────────────┘
  │
  ▼
DONE
```

---

## mkdocs Updater Flow

```
START: update-mkdocs-nav.sh
  │
  ▼
┌──────────────────────────────────────┐
│ Find all documentation files:        │
│ • docs/**/*.md                       │
│ • Root files (PHASE-*, *-DESIGN.md)  │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Filter exclusions:                   │
│ • *BRAINSTORM*                       │
│ • *RFORGE*                           │
│ • *PLAN.md                           │
│ • *.tmp, *.bak                       │
│ • .backup-*                          │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Get files in mkdocs.yml nav          │
│ grep "*.md" mkdocs.yml               │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Find orphaned files                  │
│ (in all_files but not in nav)        │
└──────────────────────────────────────┘
  │
  │ Example orphans:
  │ • PHASE-2-DESIGN.md
  │ • docs/INTEGRATION-GUIDE.md
  ▼
┌─────────────────────────────────────────────────┐
│ For each orphaned file:                         │
│                                                 │
│ 1. Extract title from first # heading          │
│    Example: "# Phase 2 Design"                 │
│    → Title: "Phase 2 Design"                   │
│                                                 │
│ 2. Infer section from filename                 │
│    PHASE-2-DESIGN.md                           │
│    → Pattern: *PHASE* + *DESIGN*               │
│    → Section: "Development"                    │
│                                                 │
│ 3. Prepare update:                             │
│    file: PHASE-2-DESIGN.md                     │
│    title: "Phase 2 Design"                     │
│    section: "Development"                      │
└─────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────┐
│ Insert into mkdocs.yml:                         │
│                                                 │
│ nav:                                            │
│   - Development:                                │
│       - Phase 2 Design: PHASE-2-DESIGN.md  ←NEW│
│       - Phase 1 Implementation: PHASE-1.md      │
│   - User Guide:                                 │
│       - Integration: docs/INTEGRATION-GUIDE.md  │
└─────────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Validate YAML:                       │
│ • python3 yaml.safe_load(file)       │
│ • Check for syntax errors            │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Test build:                          │
│ • mkdocs build --strict              │
│ • Auto-rollback on failure           │
└──────────────────────────────────────┘
  │
  ▼
DONE
```

---

## .STATUS Updater Flow

```
START: update-claude-md.sh
  │
  ▼
┌──────────────────────────────────────┐
│ Auto-detect status file:             │
│ • .STATUS (preferred)                │
│ • CLAUDE.md (fallback)               │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Generate session summary             │
│ (if not provided via --session)      │
│                                      │
│ From git:                            │
│ • Commits in last 24h                │
│ • Files changed stats                │
│ • Commit subjects                    │
└──────────────────────────────────────┘
  │
  │ Example summary:
  │ - ✅ Session (2025-12-22)
  │   - 3 commits
  │   - Changes: 12 files, 450+, 50-
  │   - feat(hooks): add wizard
  │   - fix(bug): resolve crash
  ▼
┌──────────────────────────────────────┐
│ Find "Just Completed" section:       │
│ ## ✅ Just Completed                 │
│ ## ✅ Recently Completed             │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────────────┐
│ Update frontmatter:                               │
│                                                  │
│ BEFORE:                    AFTER:                │
│ updated: 2025-12-20        updated: 2025-12-22   │
│ progress: 60               progress: 75          │
└──────────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────────────┐
│ Prepend to "Just Completed" section:             │
│                                                  │
│ ## ✅ Just Completed (2025-12-22)                │
│ - ✅ Session (2025-12-22)  ← NEW                 │
│   - 3 commits                                    │
│   - Changes: 12 files                            │
│                                                  │
│ ## ✅ Just Completed (2025-12-20)                │
│ - Previous entry                                 │
└──────────────────────────────────────────────────┘
  │
  ▼
DONE
```

---

## Integration with /workflow:done

```
User runs: /workflow:done
  │
  ▼
┌─────────────────────────────────────────────────┐
│ Step 1: Gather Session Activity                 │
│ • Git commits                                   │
│ • Files changed                                 │
│ • Lines added/removed                           │
└─────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────┐
│ Step 1.5: Detect Documentation Issues           │
│ (Phase 1)                                       │
│ • Missing CHANGELOG entries                     │
│ • Orphaned documentation files                  │
│ • Outdated .STATUS                              │
│ • Navigation divergence                         │
└─────────────────────────────────────────────────┘
  │
  │ Output warnings:
  │ ⚠ 3 commits not in CHANGELOG
  │ ⚠ 2 orphaned documentation files
  ▼
┌─────────────────────────────────────────────────┐
│ Step 1.6: Apply Auto-Updates                    │
│ (Phase 2 - NEW!)                                │
│                                                 │
│ run-all-updaters.sh                             │
│   ├─ update-changelog.sh --apply                │
│   ├─ update-mkdocs-nav.sh --apply               │
│   └─ update-claude-md.sh --apply (prompted)     │
│                                                 │
│ Result: All warnings → Fixed!                   │
└─────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────┐
│ Step 2: Interactive Session Summary             │
│ • Review all changes                            │
│ • User adds context/notes                       │
└─────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────┐
│ Step 3: Commit & Cleanup                        │
│ • git commit with summary                       │
│ • Clean temp files                              │
└─────────────────────────────────────────────────┘
  │
  ▼
DONE
Session documented automatically!
```

---

## Safety Feature: Backup & Rollback

```
Update Process with Safety:

BEFORE UPDATE
  │
  ▼
┌──────────────────────────────────────┐
│ Create timestamped backup:           │
│ CHANGELOG.md.backup-20251222-143022  │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Perform update:                      │
│ • Modify file                        │
│ • Insert new content                 │
└──────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────┐
│ Validate:                            │
│ • YAML syntax check                  │
│ • mkdocs build test                  │
└──────────────────────────────────────┘
  │
  ├─ Success ─────────┐
  │                   │
  │                   ▼
  │         ┌──────────────────────┐
  │         │ Keep changes         │
  │         │ Delete backup later  │
  │         └──────────────────────┘
  │
  └─ Failure ─────────┐
                      │
                      ▼
            ┌──────────────────────────┐
            │ Auto-rollback:           │
            │ cp backup → original     │
            │ Restore previous state   │
            └──────────────────────────┘
```

---

## Decision Tree: Which Mode to Use?

```
Need to update documentation?
  │
  ├─ YES: Part of /workflow:done session
  │   │
  │   └─► Use: /workflow:done
  │       (Auto-updater runs as Step 1.6)
  │       Result: All docs updated automatically
  │
  ├─ YES: Want to review before applying
  │   │
  │   └─► Use: run-all-updaters.sh --dry-run
  │       Result: Preview changes, no modifications
  │
  ├─ YES: Want full automation (CI/CD)
  │   │
  │   └─► Use: run-all-updaters.sh --auto
  │       Result: All safe updates applied, no prompts
  │
  ├─ YES: Only need CHANGELOG
  │   │
  │   └─► Use: update-changelog.sh --apply
  │       Result: Just CHANGELOG updated
  │
  ├─ YES: Only need mkdocs navigation
  │   │
  │   └─► Use: update-mkdocs-nav.sh --apply
  │       Result: Just mkdocs.yml updated
  │
  └─ YES: Only need .STATUS
      │
      └─► Use: update-claude-md.sh --apply
          Result: Just .STATUS updated
```

---

## Performance Comparison

```
Manual Documentation (15-20 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
████████████████████████████████████████████████████░░░░░░░░░░

Automatic Documentation (30 sec)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

Time saved: 14.5 min/session
Time saved per month (25 sessions): 6+ hours
```

---

## Example: Complete Session Timeline

```
Time    Activity                               Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0:00    Start coding session                   Your IDE
2:00    Finish features, write tests           Your IDE

2:02    Commit changes                         git
        git commit -m "feat: new feature"
        git commit -m "fix: bug fix"
        git commit -m "docs: new guide"

2:05    Run /workflow:done                     Claude Code

2:06    │ Phase 1: Detect issues
        │ ⚠ 3 commits not in CHANGELOG
        │ ⚠ 1 orphaned doc

2:07    │ Phase 2: Auto-update
        │ ✓ CHANGELOG updated (3 entries)
        │ ✓ mkdocs.yml updated (1 file)
        │ Update .STATUS? [Y/n] ▼

2:08    │ Press Enter (Y)
        │ ✓ .STATUS updated
        │ Commit changes? [Y/n] ▼

2:09    │ Press Enter (Y)
        │ ✓ Committed

2:10    Done!

        Time spent on documentation: 5 seconds (pressing Enter)
        Manual alternative: 15-20 minutes
```

---

## Summary: What Gets Automated

```
┌────────────────────────────────────────────────────┐
│              Before Auto-Update                     │
├────────────────────────────────────────────────────┤
│ Manual tasks per session:                          │
│ • Read git log for commits            (3 min)      │
│ • Format CHANGELOG entries            (5 min)      │
│ • Find new documentation files        (2 min)      │
│ • Update mkdocs.yml navigation        (3 min)      │
│ • Update .STATUS file                 (2 min)      │
│                                                    │
│ Total: 15 minutes                                  │
│ Reality: Skip 50% of time                          │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│              After Auto-Update                      │
├────────────────────────────────────────────────────┤
│ Automated tasks per session:                       │
│ • ✓ Parse commits automatically      (auto)        │
│ • ✓ Format CHANGELOG with links      (auto)        │
│ • ✓ Detect orphaned files            (auto)        │
│ • ✓ Update mkdocs.yml navigation     (auto)        │
│ • ✓ Generate .STATUS summary         (auto)        │
│                                                    │
│ Your time: 30 seconds (press Enter)                │
│ Done: 100% of time                                 │
└────────────────────────────────────────────────────┘

Result: 15 min → 30 sec (30x faster)
        50% compliance → 100% compliance
```

---

**See Also:**
- Full Tutorial: `AUTO-UPDATE-TUTORIAL.md`
- Quick Reference: `AUTO-UPDATE-REFCARD.md`
- Design Docs: `PHASE-2-DESIGN.md`, `PHASE-2-COMPLETE.md`
