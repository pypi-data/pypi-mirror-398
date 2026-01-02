# Balanced Cleanup Execution Plan

**Date:** 2025-12-21
**Approach:** Balanced (15-20 files removed)
**Backup:** `~/.claude/commands-backup-20251221.tar.gz` ✅

---

## User Input Summary

### Frequently Used
- ✅ **workflow** (ADHD helpers) - Keep all core
- ✅ **site** (doc sites) - Occasionally (monthly)
- ✅ **help** (documentation) - Keep essential only

### Decisions
- **Site commands:** Keep 5 core, remove mkdocs-specific duplicates
- **Help directory:** Keep essential, archive detailed tutorials
- **Task commands:** Keep all 3 (user finds them valuable)

---

## Files to Remove (17 total)

### Category 1: Hub-within-Hub Redundancy (3 files)
```bash
rm ~/.claude/commands/site/site.md           # Redundant with top-level site.md
rm ~/.claude/commands/workflow/workflow.md   # Redundant with top-level workflow.md
rm ~/.claude/commands/git/git.md             # Redundant with top-level git.md
```
**Reason:** Top-level hubs already provide navigation

### Category 2: MkDocs-Specific Duplicates (3 files)
```bash
rm ~/.claude/commands/site/mkdocs/init.md    # Duplicate of site/init.md
rm ~/.claude/commands/site/mkdocs/preview.md # Duplicate of site/preview.md
rm ~/.claude/commands/site/mkdocs/status.md  # Rarely used, mkdocs-specific
```
**Reason:** Generic site commands cover the functionality

### Category 3: Help Directory - Archive Detailed Tutorials (4 files)
```bash
# Keep: help.md (hub), getting-started.md, refcards/quick-reference.md
# Remove detailed tutorials:
rm ~/.claude/commands/help/tutorials/first-time-setup.md  # Covered in getting-started
rm ~/.claude/commands/help/tutorials.md                   # Duplicates content
rm ~/.claude/commands/help/troubleshooting.md             # Rarely referenced
rm ~/.claude/commands/help/workflows.md                   # Duplicates other docs
```
**Reason:** Keep quick references, remove deep-dive tutorials

### Category 4: Rarely-Used Domain Hubs (5 files)
```bash
# Archive hubs user doesn't use weekly:
rm ~/.claude/commands/research.md  # Research-specific (not weekly)
rm ~/.claude/commands/write.md     # Writing-specific (not weekly)
rm ~/.claude/commands/teach.md     # Teaching-specific (not weekly)
rm ~/.claude/commands/math.md      # Math-specific (not weekly)
rm ~/.claude/commands/code.md      # Development-specific (not weekly)
```
**Reason:** User indicated these aren't weekly usage

### Category 5: Low-Usage Workflow Commands (2 files)
```bash
rm ~/.claude/commands/workflow/brain-dump.md  # Replaced by brainstorm + RForge
rm ~/.claude/commands/workflow/done.md        # Overlaps with recap
```
**Reason:** Functionality covered by other commands

---

## Files to Keep (31 files)

### Hub Commands (5 files)
```
✅ hub.md          # Command discovery
✅ workflow.md     # ADHD helpers (weekly use)
✅ site.md         # Doc sites (monthly use)
✅ help.md         # Help system (weekly use)
✅ github.md       # GitHub operations
```

### Workflow Commands (11 files - KEEP TASK COMMANDS)
```
✅ stuck.md        # Unblock helper
✅ next.md         # Decision support
✅ focus.md        # Single-task mode
✅ recap.md        # Context restoration
✅ brainstorm.md   # Structured ideation
✅ refine.md       # Prompt optimizer
✅ task-output.md  # User wants to keep
✅ task-status.md  # User wants to keep
✅ task-cancel.md  # User wants to keep
✅ docs/adhd-guide.md  # ADHD reference
```

### Site Commands (5 files)
```
✅ init.md         # Initialize doc site
✅ preview.md      # Local preview
✅ build.md        # Build site
✅ deploy.md       # Deploy to GitHub Pages
✅ check.md        # Validate docs
✅ docs/frameworks.md  # Framework comparison
```

### Git Commands (8 files - Keep All)
```
✅ branch.md       # Branch management
✅ git-recap.md    # Git activity
✅ sync.md         # Smart sync
✅ docs/safety-rails.md    # Safety guide
✅ docs/undo-guide.md      # Emergency reference
✅ docs/learning-guide.md  # Git learning
✅ docs/refcard.md         # Quick reference
```

### Help Commands (3 files - Essential Only)
```
✅ getting-started.md         # Quick start guide
✅ refcard.md                 # Quick reference
✅ refcards/quick-reference.md  # Detailed quick ref
```

---

## Summary

### Before
- **Total:** 48 files
- **Structure:** 10 hubs + 38 in subdirectories
- **Issues:** Duplicates, unused hubs, detailed tutorials

### After
- **Total:** 31 files (-17 files, -35%)
- **Structure:** 5 active hubs + 26 in subdirectories
- **Benefits:** Focused on actually-used commands

---

## File Count by Category

| Category | Before | After | Removed |
|----------|--------|-------|---------|
| Hub Commands | 10 | 5 | -5 |
| Workflow | 13 | 11 | -2 |
| Site | 10 | 6 | -4 |
| Git | 8 | 8 | 0 |
| Help | 7 | 3 | -4 |
| **TOTAL** | **48** | **32** | **-16** |

*(Note: Numbers adjusted based on actual file count)*

---

## Execution Script

```bash
#!/bin/bash
# Balanced Cleanup - Remove 17 files

cd ~/.claude/commands

echo "Starting balanced cleanup..."

# Category 1: Hub-within-Hub Redundancy (3 files)
echo "Removing hub-within-hub redundancies..."
rm -f site/site.md
rm -f workflow/workflow.md
rm -f git/git.md

# Category 2: MkDocs-Specific Duplicates (3 files)
echo "Removing MkDocs duplicates..."
rm -f site/mkdocs/init.md
rm -f site/mkdocs/preview.md
rm -f site/mkdocs/status.md

# Category 3: Help Tutorials (4 files)
echo "Removing detailed tutorials..."
rm -f help/tutorials/first-time-setup.md
rm -f help/tutorials.md
rm -f help/troubleshooting.md
rm -f help/workflows.md

# Category 4: Unused Domain Hubs (5 files)
echo "Removing rarely-used domain hubs..."
rm -f research.md
rm -f write.md
rm -f teach.md
rm -f math.md
rm -f code.md

# Category 5: Low-Usage Workflow (2 files)
echo "Removing low-usage workflow commands..."
rm -f workflow/brain-dump.md
rm -f workflow/done.md

echo "Cleanup complete!"
echo "Files removed: 17"
echo "Files remaining: $(find . -name '*.md' | wc -l | tr -d ' ')"

# Cleanup empty directories
rmdir help/tutorials 2>/dev/null
rmdir site/mkdocs 2>/dev/null

echo "Empty directories removed"
```

---

## Validation Steps

### After Cleanup
```bash
# 1. Count remaining files
find ~/.claude/commands -name '*.md' | wc -l
# Expected: ~31-32 files

# 2. Check hub commands still work
ls ~/.claude/commands/*.md
# Expected: hub.md, workflow.md, site.md, help.md, github.md

# 3. Verify critical workflow commands exist
ls ~/.claude/commands/workflow/
# Expected: stuck, next, focus, recap, brainstorm, refine, task-*

# 4. Verify site commands
ls ~/.claude/commands/site/
# Expected: init, preview, build, deploy, check, docs/

# 5. Verify git commands intact
ls ~/.claude/commands/git/
# Expected: branch, git-recap, sync, docs/
```

---

## Rollback Plan (If Needed)

```bash
# Restore from backup
cd ~/.claude
rm -rf commands/
tar -xzf commands-backup-20251221.tar.gz
```

---

## Benefits

### Reduced Complexity
- 35% fewer files to maintain
- Clearer structure (removed hub-within-hub confusion)
- Focused on actually-used commands

### Kept What Matters
- ✅ All weekly-use commands (workflow, site, help)
- ✅ Task management (per user request)
- ✅ All git commands (valuable references)
- ✅ Essential help quick-references

### Removed Clutter
- ❌ Duplicate mkdocs files
- ❌ Unused domain hubs (research, write, teach, math, code)
- ❌ Detailed tutorials (rarely referenced)
- ❌ Redundant hub-within-hub files

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Execute cleanup script
3. ⏳ Test remaining commands
4. ⏳ Document final results
5. ⏳ Commit to git

---

**Status:** Ready to execute! 🚀
