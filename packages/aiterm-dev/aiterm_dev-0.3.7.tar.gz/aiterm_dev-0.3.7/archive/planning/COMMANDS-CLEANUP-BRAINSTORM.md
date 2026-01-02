# Claude Code Commands Cleanup - Brainstorm

**Date:** 2025-12-21
**Scope:** `~/.claude/commands/` directory only
**Goal:** Identify redundant/unused commands to simplify structure

---

## Current Inventory

**Total:** 48 command files

### Hub Commands (10 files - top level)
```
code.md, github.md, help.md, hub.md, math.md,
research.md, site.md, teach.md, workflow.md, write.md
```

### Git Commands (8 files in git/)
```
git/
├── branch.md
├── git.md
├── git-recap.md
├── sync.md
└── docs/
    ├── learning-guide.md
    ├── refcard.md
    ├── safety-rails.md
    └── undo-guide.md
```

### Site Commands (10 files in site/)
```
site/
├── build.md
├── check.md
├── deploy.md
├── init.md
├── preview.md
├── site.md
├── docs/
│   └── frameworks.md
└── mkdocs/
    ├── init.md
    ├── preview.md
    └── status.md
```

### Workflow Commands (13 files in workflow/)
```
workflow/
├── brain-dump.md
├── brainstorm.md
├── done.md
├── focus.md
├── next.md
├── recap.md
├── refine.md
├── stuck.md
├── task-cancel.md
├── task-output.md
├── task-status.md
├── workflow.md
└── docs/
    └── adhd-guide.md
```

### Help Commands (7 files in help/)
```
help/
├── getting-started.md
├── refcard.md
├── troubleshooting.md
├── tutorials.md
├── workflows.md
├── refcards/
│   └── quick-reference.md
└── tutorials/
    └── first-time-setup.md
```

---

## Questions to Answer

### 1. Which commands do you actually use?

**Hub commands - probably keep all:**
- ✅ `workflow` - ADHD helpers (use frequently?)
- ✅ `help` - Documentation (use?)
- ⏳ `code`, `research`, `write`, `teach`, `math` - Do you use these?
- ⏳ `site` - MkDocs sites (use frequently?)
- ⏳ `github` - GitHub operations (use?)
- ⏳ `hub` - Command discovery (useful?)

**Git commands - which are actually useful?**
- ⏳ `git/branch.md` - Branch management (vs just using gh/git directly?)
- ⏳ `git/git-recap.md` - Git activity summary (use this?)
- ⏳ `git/sync.md` - Smart git sync (vs manual git commands?)
- ⏳ `git/git.md` - Git hub (duplicate of top-level functionality?)
- ✅ `git/docs/safety-rails.md` - Safety guide (valuable reference!)
- ✅ `git/docs/undo-guide.md` - Emergency reference (valuable!)
- ⏳ `git/docs/learning-guide.md` - Git learning (still needed?)
- ⏳ `git/docs/refcard.md` - Quick reference (vs online docs?)

**Site commands - duplication issues:**
- `site/init.md` vs `site/mkdocs/init.md` - **DUPLICATE**
- `site/preview.md` vs `site/mkdocs/preview.md` - **DUPLICATE**
- ⏳ `site/site.md` - Hub within hub? (seems redundant)
- ⏳ `site/build.md`, `site/check.md`, `site/deploy.md` - Use these?
- ⏳ `site/docs/frameworks.md` - Framework comparison (useful?)
- ⏳ `site/mkdocs/status.md` - MkDocs status (use this?)

**Workflow commands - task management overlap:**
- ⏳ `workflow/task-output.md` - Built-in `/tasks` command covers this?
- ⏳ `workflow/task-status.md` - Built-in `/tasks` command covers this?
- ⏳ `workflow/task-cancel.md` - Built-in covers this?
- ✅ `workflow/stuck.md` - Unblock helper (ADHD-valuable!)
- ✅ `workflow/next.md` - Decision support (ADHD-valuable!)
- ✅ `workflow/focus.md` - Single-task mode (ADHD-valuable!)
- ✅ `workflow/recap.md` - Context restoration (ADHD-valuable!)
- ✅ `workflow/brainstorm.md` - Structured ideation (valuable!)
- ⏳ `workflow/brain-dump.md` - Quick capture (vs brainstorm?)
- ⏳ `workflow/done.md` - Session wrap (vs recap?)
- ⏳ `workflow/refine.md` - Prompt optimizer (use this?)
- ⏳ `workflow/workflow.md` - Hub within hub? (redundant with top-level?)
- ⏳ `workflow/docs/adhd-guide.md` - Reference doc (valuable?)

**Help commands - structural issues:**
- ⏳ `help/refcard.md` vs `help/refcards/quick-reference.md` - **DUPLICATE**
- ⏳ `help/tutorials.md` vs `help/tutorials/first-time-setup.md` - Unclear relationship
- ⏳ All help files - Are these actually helpful or just maintenance burden?

---

## Duplication Issues

### Clear Duplicates (Remove One)

1. **Site Init:**
   - `site/init.md`
   - `site/mkdocs/init.md`
   - **Decision:** Keep generic `site/init.md`, remove mkdocs-specific

2. **Site Preview:**
   - `site/preview.md`
   - `site/mkdocs/preview.md`
   - **Decision:** Keep generic `site/preview.md`, remove mkdocs-specific

3. **Help Refcard:**
   - `help/refcard.md`
   - `help/refcards/quick-reference.md`
   - **Decision:** Keep one, remove other (which is better?)

4. **Hub-within-hub:**
   - `site/site.md` (hub within site/)
   - `workflow/workflow.md` (hub within workflow/)
   - `git/git.md` (hub within git/)
   - **Decision:** Redundant with top-level hubs? Remove?

### Partial Overlaps (Consolidate?)

1. **Task Management:**
   - `workflow/task-output.md`
   - `workflow/task-status.md`
   - `workflow/task-cancel.md`
   - **vs Built-in:** `/tasks` command
   - **Decision:** Are these adding value beyond built-in?

2. **Session Management:**
   - `workflow/done.md` (session wrap-up)
   - `workflow/recap.md` (context restoration)
   - **Decision:** Keep both or consolidate?

3. **Ideation:**
   - `workflow/brainstorm.md` (structured ideation)
   - `workflow/brain-dump.md` (quick capture)
   - **vs RForge:** `rforge_plan` (now available)
   - **Decision:** Keep brainstorm, remove brain-dump?

---

## Unused/Rarely Used (Archive?)

### Low Value Candidates

**Git Commands:**
- `git/git-recap.md` - Git activity summary (is this used?)
- `git/docs/learning-guide.md` - Basic git tutorial (online docs better?)
- `git/docs/refcard.md` - Git quick reference (cheatsheet.io better?)

**Site Commands:**
- `site/docs/frameworks.md` - Framework comparison (one-time read)
- `site/mkdocs/status.md` - MkDocs status checker (how often used?)
- Entire `site/mkdocs/` directory (if not using MkDocs frequently)

**Workflow Commands:**
- `workflow/refine.md` - Prompt optimizer (use this?)
- `workflow/brain-dump.md` - Quick capture (vs brainstorm?)
- `workflow/done.md` - Session wrap (vs recap?)

**Help Commands:**
- Entire `help/` directory? (Is it actually helpful or just docs bloat?)

---

## Keep vs Remove Decision Framework

### Keep If:
1. ✅ **Used frequently** (weekly or more)
2. ✅ **Unique functionality** (no duplicate/replacement)
3. ✅ **ADHD-valuable** (reduces cognitive load, prevents analysis paralysis)
4. ✅ **Hard to find elsewhere** (custom to your workflow)

### Remove If:
1. ❌ **Rarely/never used** (monthly or less)
2. ❌ **Duplicates another command** (same functionality elsewhere)
3. ❌ **Replaced by built-in** (Claude Code has this feature)
4. ❌ **Replaced by MCP server** (RForge, etc. provide better version)
5. ❌ **Easy to find online** (standard git/mkdocs docs)

### Archive (Don't Delete) If:
1. 📦 **Uncertain value** (might be useful later)
2. 📦 **Seasonal use** (teach commands during semester only)
3. 📦 **Under development** (might evolve into something useful)

---

## Proposed Cleanup Categories

### Category A: Clear Duplicates - Remove (6 files)

1. ❌ `site/mkdocs/init.md` (duplicate of site/init.md)
2. ❌ `site/mkdocs/preview.md` (duplicate of site/preview.md)
3. ❌ `site/site.md` (hub-within-hub redundancy)
4. ❌ `workflow/workflow.md` (hub-within-hub redundancy)
5. ❌ `git/git.md` (hub-within-hub redundancy)
6. ❌ One of: `help/refcard.md` OR `help/refcards/quick-reference.md`

**Immediate win: 6 files → 0 files**

---

### Category B: Built-in Replacements - Remove (3 files)

1. ❌ `workflow/task-output.md` (built-in `/tasks` better)
2. ❌ `workflow/task-status.md` (built-in `/tasks` better)
3. ❌ `workflow/task-cancel.md` (built-in `/tasks` better)

**Reason:** Claude Code's built-in `/tasks` command already provides this

---

### Category C: MCP Server Replacements - Remove (2 files)

1. ❌ `workflow/brain-dump.md` (RForge `rforge_plan` better for ideation)
2. ❌ Any R-package specific planning commands (RForge handles this)

**Reason:** RForge MCP server provides superior functionality

---

### Category D: Consolidation Candidates (4 files → 2 files)

1. **Session Management:** Consolidate?
   - `workflow/done.md` + `workflow/recap.md` → Single `workflow/session.md`?

2. **Help Structure:** Simplify?
   - Flatten `help/` directory (remove refcards/ and tutorials/ subdirs)
   - Merge similar content

**Result:** 4 files → 2 files (if consolidated)

---

### Category E: Archive for Review (Low usage, uncertain value)

**Git:**
- 📦 `git/git-recap.md`
- 📦 `git/docs/learning-guide.md`
- 📦 `git/docs/refcard.md`

**Site:**
- 📦 `site/mkdocs/status.md`
- 📦 `site/docs/frameworks.md`

**Workflow:**
- 📦 `workflow/refine.md`
- 📦 `workflow/done.md` (if not consolidating)

**Help:**
- 📦 Entire `help/` directory? (User decision needed)

---

## Questions for User

### High Priority (Affects many files)

**Q1: Help directory - Keep or Archive?**
- [ ] Keep all help files (7 files)
- [ ] Archive entire help/ directory (move to ~/.claude/commands/archive/)
- [ ] Keep only essential, archive rest (which are essential?)

**Q2: Site/MkDocs - How often used?**
- [ ] Frequently (keep all 10 site files)
- [ ] Occasionally (keep 5 core, archive mkdocs-specific)
- [ ] Rarely (archive entire site/ directory)

**Q3: Teaching commands - Seasonal or Year-round?**
- [ ] Year-round (keep teach.md hub)
- [ ] Seasonal (archive during non-teaching periods)
- [ ] Rarely used (archive permanently)

### Medium Priority (Structural decisions)

**Q4: Hub-within-hub files?**
- Current: `site/site.md`, `workflow/workflow.md`, `git/git.md`
- [ ] Remove all (redundant with top-level hubs)
- [ ] Keep (they serve a purpose I don't see)

**Q5: Task management commands?**
- Current: `task-output.md`, `task-status.md`, `task-cancel.md`
- [ ] Remove (built-in `/tasks` is sufficient)
- [ ] Keep (they add value beyond built-in)

**Q6: Session management?**
- Current: `done.md` (wrap-up) + `recap.md` (restore context)
- [ ] Consolidate into single `session.md`
- [ ] Keep both (serve different purposes)

### Low Priority (Individual files)

**Q7: Which specific files do you actually use?**

Mark files you use **weekly or more**:
- [ ] `git/branch.md`
- [ ] `git/git-recap.md`
- [ ] `git/sync.md`
- [ ] `workflow/brain-dump.md`
- [ ] `workflow/refine.md`
- [ ] `workflow/done.md`
- [ ] `site/build.md`
- [ ] `site/check.md`
- [ ] `site/deploy.md`

---

## Conservative Cleanup (Minimal Risk)

If you want to start small, here's a **safe 6-file cleanup**:

### Remove Clear Duplicates Only (6 files)

1. ❌ `site/mkdocs/init.md` (duplicate)
2. ❌ `site/mkdocs/preview.md` (duplicate)
3. ❌ `site/site.md` (hub redundancy)
4. ❌ `workflow/workflow.md` (hub redundancy)
5. ❌ `git/git.md` (hub redundancy)
6. ❌ `workflow/task-output.md` (built-in `/tasks` better)

**Result:** 48 → 42 files (-12%)
**Risk:** Very low (obvious duplicates/redundancies)
**Time:** 5 minutes

---

## Aggressive Cleanup (Maximum Simplification)

If you want major simplification:

### Remove All Low-Value (20+ files)

**Duplicates (6)** + **Built-in Replacements (3)** + **MCP Replacements (2)** + **Archive Low-Usage (10+)**

**Result:** 48 → ~25 files (-48%)
**Risk:** Medium (might remove something occasionally useful)
**Mitigation:** Archive (don't delete), easy to restore

---

## Recommended Approach

### Phase 1: Safe Cleanup (Today)
1. ✅ Backup: `tar -czf ~/.claude/commands-backup-$(date +%Y%m%d).tar.gz ~/.claude/commands`
2. ✅ Remove 6 clear duplicates/redundancies
3. ✅ Test commands still work
4. ✅ Commit changes

**Impact:** 48 → 42 files (-12%)
**Risk:** Very low
**Time:** 10 minutes

### Phase 2: User Decision (This Week)
1. Answer questions about usage patterns
2. Decide on help/, site/, teach/ directories
3. Plan deeper cleanup based on actual usage

### Phase 3: Implementation (Next Week)
1. Archive rarely-used commands
2. Consolidate related commands
3. Document new structure
4. Final validation

---

## Success Metrics

### Minimum (Conservative)
- ✅ Remove 6 obvious duplicates
- ✅ No functionality lost
- ✅ 10-minute cleanup time

### Target (Balanced)
- ✅ Remove 15-20 files
- ✅ Clearer organization
- ✅ Easier command discovery

### Stretch (Aggressive)
- ✅ Remove 20+ files
- ✅ Lean, focused command set
- ✅ Maximum ADHD-friendliness

---

## Next Steps

**Immediate:**
1. ✅ Create backup
2. ⏳ Answer usage questions above
3. ⏳ Decide on approach (conservative/balanced/aggressive)

**After User Input:**
1. ⏳ Execute chosen cleanup
2. ⏳ Test remaining commands
3. ⏳ Document changes
4. ⏳ Commit to git

---

**Status:** Ready for user input on usage patterns and cleanup scope! 🚀
