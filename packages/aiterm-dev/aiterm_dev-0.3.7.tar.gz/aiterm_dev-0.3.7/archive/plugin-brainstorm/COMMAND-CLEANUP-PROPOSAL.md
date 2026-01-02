# Command & Plugin Cleanup Proposal

**Date:** 2025-12-21
**Context:** Post-Phase 1, RForge MCP server installed
**Goal:** Simplify command structure, reduce duplication, leverage MCP servers

---

## Current State

### Command Inventory
- **Total files**: 48 command files
- **Hub commands**: 10 (code, github, help, hub, math, research, site, teach, workflow, write)
- **Subdirectories**: 12
- **Categories**: Git (8), Site (10), Workflow (13), Help (7)

### Current Structure
```
~/.claude/commands/
├── *.md (10 hub commands)
├── git/ (8 files)
│   └── docs/ (3 guides)
├── github/ (0 files)
├── help/ (7 files)
│   ├── refcards/
│   └── tutorials/
├── site/ (10 files)
│   ├── docs/
│   └── mkdocs/
└── workflow/ (13 files)
    └── docs/
```

---

## Problem Analysis

### 1. Duplication with MCP Servers

**RForge MCP Server provides:**
- ✅ `rforge_plan` - Ideation/planning (replaces manual planning commands)
- ✅ `rforge_plan_quick_fix` - Quick fixes (replaces ad-hoc fix commands)
- ✅ `rforge_detect` - Auto-detection (built-in)
- ✅ `rforge_status` - Status dashboard (built-in)
- ✅ `rforge_deps` - Dependency analysis
- ✅ `rforge_impact` - Impact assessment

**Statistical Research MCP Server provides:**
- R execution
- Literature search
- Zotero integration
- Simulation tools

**Project Refactor MCP Server provides:**
- Safe renaming
- Multi-language refactoring

**Result:** Many commands could be replaced by MCP tool calls

---

### 2. Overlapping Functionality

**Git commands** (8 files in git/):
- Most are documentation/guides
- Actual git operations handled by plugins
- **Opportunity:** Consolidate to git.md hub + essential docs

**Site commands** (10 files in site/):
- MkDocs-specific workflows
- **Opportunity:** Move to site-specific plugin or MCP server

**Workflow commands** (13 files in workflow/):
- ADHD-friendly helpers
- **Opportunity:** Keep core, move advanced to plugins

**Help commands** (7 files in help/):
- Documentation/tutorials
- **Opportunity:** Consolidate into fewer, better organized files

---

### 3. Hub vs Subdirectory Confusion

**Current pattern inconsistency:**
- Some hubs have subdirectories (git, site, workflow, help)
- Others don't (math, research, teach, write, code)
- No clear rule on when to use subdirectories

**Recommendation:** Use subdirectories only for:
1. Reference docs (refcards, guides)
2. Framework-specific commands (mkdocs, quarto)
3. Related command groups (>5 commands)

---

## Cleanup Strategy

### Phase 1: Audit & Categorize (This Document)

**Categorize each command:**
1. **Keep** - Essential, no MCP equivalent
2. **Replace** - MCP server provides better functionality
3. **Consolidate** - Merge with similar commands
4. **Archive** - Rarely used, move to backup

---

### Phase 2: MCP Server Consolidation

**Replace these with MCP server calls:**

#### Planning/Ideation → RForge MCP
- ❌ Remove manual planning workflows
- ✅ Use `rforge_plan` instead
- ✅ Use `rforge_plan_quick_fix` instead

#### R Package Development → RForge MCP
- ❌ Remove scattered R package commands
- ✅ Use RForge tools (detect, status, deps, impact)

#### Literature/Research → Statistical Research MCP
- ❌ Remove manual research workflows
- ✅ Use MCP tools for R execution, literature

---

### Phase 3: Hub Simplification

**Proposed new structure:**

```
~/.claude/commands/
├── Hub Commands (10 - keep)
│   ├── code.md
│   ├── github.md
│   ├── help.md
│   ├── hub.md
│   ├── math.md
│   ├── research.md
│   ├── site.md
│   ├── teach.md
│   ├── workflow.md
│   └── write.md
│
├── docs/ (consolidated documentation)
│   ├── git-quick-reference.md
│   ├── workflow-guide.md
│   ├── adhd-friendly-tips.md
│   └── command-workflows.md
│
├── git/ (essential git only - 3 files max)
│   ├── safety-rails.md
│   ├── undo-guide.md
│   └── learning-guide.md
│
└── workflow/ (core ADHD helpers only - 5 files max)
    ├── stuck.md
    ├── next.md
    ├── focus.md
    ├── recap.md
    └── brainstorm.md
```

**Result:** 48 → ~25 files (-48% reduction)

---

## Detailed Recommendations

### Keep (Essential Commands)

#### Hub Commands (10) - All Keep
1. ✅ `hub.md` - Command discovery
2. ✅ `workflow.md` - ADHD-friendly workflows
3. ✅ `help.md` - Help system
4. ✅ `code.md` - Development tools
5. ✅ `research.md` - Research tools
6. ✅ `write.md` - Writing tools
7. ✅ `teach.md` - Teaching tools
8. ✅ `math.md` - Math tools
9. ✅ `site.md` - Documentation sites
10. ✅ `github.md` - GitHub tools

#### Core Workflow Commands (5)
1. ✅ `workflow/stuck.md` - Unblock helper
2. ✅ `workflow/next.md` - Decision support
3. ✅ `workflow/focus.md` - Single-task mode
4. ✅ `workflow/recap.md` - Context restoration
5. ✅ `workflow/brainstorm.md` - Structured ideation

#### Essential Git Docs (3)
1. ✅ `git/docs/safety-rails.md` - Git safety guide
2. ✅ `git/docs/undo-guide.md` - Emergency reference
3. ✅ `git/docs/learning-guide.md` - Git learning

**Subtotal: 18 files**

---

### Replace with MCP Servers (8)

#### R Package Planning → RForge MCP
1. ❌ Remove: Manual R package planning commands
2. ✅ Use: `rforge_plan`, `rforge_plan_quick_fix`

#### Code Analysis → RForge/Project Refactor MCP
1. ❌ Remove: Manual refactoring workflows
2. ✅ Use: `project-refactor` MCP tools

#### Research Workflows → Statistical Research MCP
1. ❌ Remove: Manual R execution commands
2. ✅ Use: Statistical Research MCP tools

**Files to remove: ~8**

---

### Consolidate (15)

#### Site Commands → site/ directory (5 files)
**Current:** 10 files across site/, site/docs/, site/mkdocs/
**Consolidate to:**
1. `site/init.md` - Initialize any doc site
2. `site/preview.md` - Preview locally
3. `site/build.md` - Build site
4. `site/deploy.md` - Deploy to GitHub Pages
5. `site/frameworks.md` - Framework comparison

**Remove:** Duplicate mkdocs-specific files (5 removed)

#### Workflow Commands → workflow/ directory (5 files)
**Current:** 13 files
**Keep core 5:** (listed above in "Keep" section)
**Remove:** 8 advanced workflow files
- Task management (replaced by plugins)
- Advanced planning (replaced by RForge MCP)
- Session tracking (rarely used)

#### Help Commands → docs/ directory (4 files)
**Current:** 7 files across help/, help/refcards/, help/tutorials/
**Consolidate to:**
1. `docs/quick-reference.md` - All commands
2. `docs/workflows.md` - Common workflows
3. `docs/adhd-guide.md` - ADHD tips
4. `docs/troubleshooting.md` - Problem solving

**Remove:** Duplicate tutorial/refcard files (3 removed)

#### Git Commands → git/ directory (3 files)
**Current:** 8 files
**Keep:** 3 essential docs (listed above)
**Remove:** 5 files (git.md hub covers the rest)

**Subtotal to consolidate: 15 files removed**

---

### Archive (Rarely Used) (5)

1. ❌ `workflow/task-output.md` - Replaced by built-in /tasks
2. ❌ `workflow/task-status.md` - Replaced by built-in /tasks
3. ❌ `workflow/task-cancel.md` - Replaced by built-in /tasks
4. ❌ `workflow/brain-dump.md` - Rarely used
5. ❌ `workflow/done.md` - Covered by recap/focus

**Move to:** `~/.claude/commands/archive/` (for reference)

**Files archived: 5**

---

## Summary

### Before
- **Total**: 48 command files
- **Structure**: Inconsistent (some hubs have subdirs, others don't)
- **Duplication**: High (MCP servers provide better versions)
- **Maintenance**: Difficult (scattered across many files)

### After
- **Total**: ~25 command files (-48%)
- **Structure**: Consistent (hubs + essential subdirs only)
- **Duplication**: Minimal (MCP servers handle complex workflows)
- **Maintenance**: Easy (fewer, better organized files)

---

## File Count Breakdown

| Category | Current | Proposed | Change |
|----------|---------|----------|--------|
| Hub Commands | 10 | 10 | 0 |
| Workflow | 13 | 5 | -8 |
| Site | 10 | 5 | -5 |
| Git | 8 | 3 | -5 |
| Help | 7 | 4 | -3 |
| **TOTAL** | **48** | **27** | **-21 (-44%)** |

---

## Implementation Plan

### Step 1: Backup (Safety First)
```bash
# Create backup
cd ~/.claude
tar -czf commands-backup-$(date +%Y%m%d).tar.gz commands/

# Verify backup
tar -tzf commands-backup-*.tar.gz | head
```

### Step 2: Create Archive Directory
```bash
mkdir -p ~/.claude/commands/archive
mkdir -p ~/.claude/commands/docs
```

### Step 3: Move Files (Gradual)

**Week 1: Archive task management commands**
```bash
# Move rarely used task commands
mv ~/.claude/commands/workflow/task-*.md ~/.claude/commands/archive/
mv ~/.claude/commands/workflow/brain-dump.md ~/.claude/commands/archive/
mv ~/.claude/commands/workflow/done.md ~/.claude/commands/archive/
```

**Week 2: Consolidate site commands**
```bash
# Keep only 5 essential site commands
# Archive mkdocs-specific duplicates
mv ~/.claude/commands/site/mkdocs/*.md ~/.claude/commands/archive/
```

**Week 3: Consolidate help commands**
```bash
# Create consolidated docs
cat help/refcards/*.md > docs/quick-reference.md
cat help/tutorials/*.md > docs/workflows.md

# Archive originals
mv ~/.claude/commands/help/refcards ~/.claude/commands/archive/
mv ~/.claude/commands/help/tutorials ~/.claude/commands/archive/
```

**Week 4: Consolidate git commands**
```bash
# Keep only 3 essential docs
# Archive others
mv ~/.claude/commands/git/[non-essential files] ~/.claude/commands/archive/
```

### Step 4: Test & Validate

After each week:
1. ✅ Test remaining commands work
2. ✅ Verify hubs still functional
3. ✅ Check MCP servers provide replacement functionality
4. ✅ Document any issues

### Step 5: Final Cleanup

After 4 weeks of validation:
- ✅ Delete archive/ if no issues
- ✅ Update documentation
- ✅ Commit changes

---

## Risk Assessment

### Low Risk ✅
- **Archiving task commands** - Built-in /tasks provides same functionality
- **Consolidating help docs** - Content preserved in new locations
- **Removing duplicate files** - Originals backed up

### Medium Risk ⚠️
- **Replacing with MCP servers** - Need to verify MCP tools work as expected
- **Consolidating site commands** - Some MkDocs-specific features might be used

**Mitigation:**
- Test MCP replacements before removing commands
- Keep archive/ for 1 month before deletion
- Gradual rollout (1 category per week)

### No Risk 🔒
- **Backup created** - Full restore possible
- **Gradual approach** - Easy to revert individual changes
- **Archive, don't delete** - Original files preserved

---

## Benefits

### 1. Simplicity
- 48 → 27 files (-44%)
- Clearer organization
- Easier to find commands

### 2. Maintainability
- Fewer files to update
- Less duplication
- Consistent structure

### 3. Modern Architecture
- Leverage MCP servers (built-in functionality)
- Focus on coordination, not implementation
- Better separation of concerns

### 4. ADHD-Friendly
- Less overwhelming (fewer choices)
- Clearer categories
- Faster command discovery

---

## Decision Points

### 1. Aggressive vs Conservative Cleanup?

**Option A: Aggressive (recommended)**
- Remove 21 files immediately
- Keep archive for 1 month
- Fast transition to MCP-centric workflow

**Option B: Conservative**
- Archive 21 files (don't remove)
- Test for 3 months
- Slower transition

**Recommendation:** Option A (aggressive) with 1-month safety buffer

---

### 2. MCP Server Trust Level?

**Question:** How much should we rely on MCP servers vs commands?

**Current Stance:**
- ✅ Trust RForge MCP (we built it, well-tested)
- ✅ Trust Statistical Research MCP (we built it)
- ✅ Trust Project Refactor MCP (we built it)
- ⚠️ Verify MCP tools match command functionality before removal

**Recommendation:** Trust our own MCP servers, verify before removal

---

### 3. Hub Subdirectory Policy?

**Proposed rule:**
- ✅ Use subdirectory if: >5 related files OR framework-specific
- ❌ Don't use subdirectory if: <5 files OR general-purpose

**Examples:**
- ✅ `git/` (3 essential docs, grouped for clarity)
- ✅ `workflow/` (5 core commands, ADHD-focused)
- ✅ `site/` (5 commands, doc-site specific)
- ✅ `docs/` (4 consolidated reference docs)
- ❌ `github/` (0 files, remove empty dir)

---

## Next Steps

**Immediate (Today):**
1. ✅ Create backup
2. ✅ Review this proposal
3. ⏳ Decide on approach (aggressive vs conservative)

**This Week:**
1. ⏳ Archive task management commands
2. ⏳ Test MCP replacements
3. ⏳ Document MCP workflows

**Next 4 Weeks:**
1. ⏳ Gradual consolidation (1 category/week)
2. ⏳ Test each change
3. ⏳ Update documentation

**After 1 Month:**
1. ⏳ Final validation
2. ⏳ Delete archive if no issues
3. ⏳ Document new structure

---

## Success Metrics

### Quantitative
- ✅ Files reduced by 40%+ (48 → 27)
- ✅ Subdirectories reduced by 50%+ (12 → 6)
- ✅ Duplication eliminated (0 duplicate files)

### Qualitative
- ✅ Easier to find commands (clearer organization)
- ✅ Faster command execution (MCP servers)
- ✅ Better maintainability (fewer files)
- ✅ More ADHD-friendly (less overwhelming)

---

## Questions for User

1. **Cleanup approach?**
   - [ ] Aggressive (21 files removed, 1-month archive)
   - [ ] Conservative (21 files archived, 3-month trial)

2. **MCP server reliance?**
   - [ ] Full trust (use MCP for all matching functionality)
   - [ ] Verify first (test MCP before removing commands)

3. **Timeline?**
   - [ ] Fast (1 week all-at-once)
   - [ ] Gradual (4 weeks, 1 category per week)

4. **Subdirectory policy?**
   - [ ] Agree with >5 files rule
   - [ ] Different threshold
   - [ ] Keep all subdirectories as-is

---

**Status:** Ready for user decision! 🚀
**Next:** Create backup and begin cleanup (pending user approval)
