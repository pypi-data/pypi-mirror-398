# Command & MCP Refactoring Action Plan

**Date:** 2025-12-19
**Based on:** COMMAND-MCP-REFACTORING-ANALYSIS.md

> **TL;DR:** 6-phase plan to reduce 59 commands to 32, create 2 new MCP servers, and eliminate 40% duplication.

---

## 📊 Current State Summary

**Inventory:**
- 59 custom command files (7 domain hubs)
- 3 custom MCP servers
- 12 plugins installed
- ~40% duplication

**Problems:**
- Git commands duplicate `commit-commands` plugin
- Research commands split between files and MCP
- Teaching commands lack stateful capabilities
- Meta planning docs clutter command directory

---

## 🎯 Goals

1. **Reduce duplication** from 40% to <10%
2. **Better plugin utilization** - delegate to specialized plugins
3. **Consolidate domain logic** into MCP servers (stateful, reusable)
4. **Maintain UX** - keep hubs for discoverability
5. **Enable sharing** - publish MCP servers to community

---

## 📋 6-Phase Implementation Plan

### Phase 1: Quick Wins (Week 1) ⭐⭐⭐

**Time:** 1-2 hours
**Risk:** Very Low
**Impact:** Immediate cleanup, -13 files

**Actions:**

1. **Archive Meta Documents (6 files)**
   ```bash
   mkdir -p ~/.claude/archive
   mv ~/.claude/commands/BACKGROUND-AGENT-PROPOSAL.md ~/.claude/archive/
   mv ~/.claude/commands/PHASE1-IMPLEMENTATION-SUMMARY.md ~/.claude/archive/
   mv ~/.claude/commands/REORGANIZATION-SUMMARY.md ~/.claude/archive/
   mv ~/.claude/commands/UNIVERSAL-DELEGATION-PLANS.md ~/.claude/archive/
   # (+ 2 more meta docs)
   ```

2. **Deprecate Git/GitHub Commands (7 files)**
   ```bash
   # These are 100% duplicated by plugins
   mv ~/.claude/commands/git/commit.md ~/.claude/archive/
   mv ~/.claude/commands/git/pr-create.md ~/.claude/archive/
   mv ~/.claude/commands/git/pr-review.md ~/.claude/archive/
   mv ~/.claude/commands/github/*.md ~/.claude/archive/
   ```

3. **Update Git Hub to Reference Plugins**
   Edit `~/.claude/commands/git.md`:
   ```markdown
   ## Git Workflows

   ### Quick Actions
   - `/commit` - Smart mid-session commit → Use `commit-commands:commit` plugin
   - `/pr-create` - Create PR → Use `commit-commands:commit-push-pr` plugin
   - `/pr-review` - Pre-review → Use `pr-review-toolkit:review-pr` plugin

   ### Still Available
   - `/git-recap` - Git activity summary
   - `/branch` - Branch management
   - `/sync` - Smart git sync
   ```

**Result:**
- 59 → 46 files (-22%)
- 0 functionality lost (plugins cover everything)
- Cleaner command directory

---

### Phase 2: Research Consolidation (Week 2) ⭐⭐⭐

**Time:** 4-6 hours
**Risk:** Low
**Impact:** Better research workflow, -8 files

**Current State:**
- 8 research commands split between commands/ and MCP
- 6 overlap with `statistical-research` MCP tools
- 2 unique (manuscript writer, reviewer response)

**Actions:**

1. **Add 2 New Tools to statistical-research MCP**

   **Tool 1: write_manuscript_section**
   ```typescript
   {
     name: "write_manuscript_section",
     description: "Draft manuscript sections based on analysis results",
     inputSchema: {
       type: "object",
       properties: {
         section: {enum: ["introduction", "methods", "results", "discussion"]},
         analysis_file: {type: "string"},
         references: {type: "array"}
       }
     }
   }
   ```

   **Tool 2: respond_to_reviewers**
   ```typescript
   {
     name: "respond_to_reviewers",
     description: "Generate point-by-point responses to reviewer comments",
     inputSchema: {
       type: "object",
       properties: {
         review_file: {type: "string"},
         manuscript_file: {type: "string"},
         response_template: {type: "string"}
       }
     }
   }
   ```

2. **Deprecate 8 Research Commands**
   ```bash
   mv ~/.claude/commands/research/*.md ~/.claude/archive/
   ```

3. **Update Research Hub**
   Edit `~/.claude/commands/research.md`:
   ```markdown
   ## Research Tools (via statistical-research MCP)

   All research capabilities now available through MCP server tools:
   - cite: Citation lookup
   - hypothesis: Formulate hypotheses
   - analysis-plan: Create analysis plan
   - manuscript: Draft manuscript sections (NEW)
   - revision: Respond to reviewers (NEW)
   - sim-design: Simulation study design
   - method-scout: Scout methods
   - lit-gap: Literature gap finder
   ```

**Result:**
- 46 → 38 files (-17% additional)
- More powerful research tools (stateful, integrated with R)
- Can share statistical-research MCP with community

---

### Phase 3: Teaching MCP Server (Week 3-4) ⭐⭐⭐

**Time:** 8-12 hours
**Risk:** Medium
**Impact:** Revolutionary teaching workflow, -9 files

**Why MCP for Teaching:**
- Persistent question banks across sessions
- Stateful exam generation (reuse questions)
- Canvas API integration (publish directly)
- Rubric templates with memory

**New MCP Server:** `teaching-toolkit`

**Tools (10):**
```typescript
{
  tools: [
    "create_quiz",           // Generate quiz with difficulty levels
    "create_exam",           // Generate exam from question bank
    "create_homework",       // Create homework assignments
    "generate_rubric",       // Create grading rubric
    "create_solution_key",   // Generate solutions
    "provide_feedback",      // Student feedback generator
    "manage_question_bank",  // CRUD for question database
    "canvas_publish",        // Publish to Canvas LMS (NEW)
    "create_syllabus",       // Generate course syllabus
    "create_lecture_outline" // Lecture planning
  ]
}
```

**Question Bank (SQLite):**
```sql
CREATE TABLE questions (
  id INTEGER PRIMARY KEY,
  course TEXT,
  topic TEXT,
  difficulty INTEGER, -- 1-5
  text TEXT,
  answer TEXT,
  bloom_level TEXT,   -- remember, understand, apply, analyze, evaluate, create
  last_used DATE,
  times_used INTEGER
);
```

**Canvas Integration:**
```typescript
// Uses Canvas REST API
async function publishToCanvas(
  course_id: string,
  assignment: {
    title: string,
    description: string,
    points: number,
    due_date: string
  }
) {
  // POST to Canvas API
}
```

**Actions:**

1. **Create teaching-toolkit MCP Server**
   ```bash
   cd ~/projects/dev-tools/mcp-servers
   mkdir teaching-toolkit
   cd teaching-toolkit
   npm init -y
   npm install @modelcontextprotocol/sdk sqlite3 canvas-api
   ```

2. **Implement 10 Tools** (see detailed spec in analysis)

3. **Migrate Teaching Commands**
   ```bash
   mv ~/.claude/commands/teach/*.md ~/.claude/archive/
   ```

4. **Update Teaching Hub**
   Edit `~/.claude/commands/teach.md`:
   ```markdown
   ## Teaching Tools (via teaching-toolkit MCP)

   All teaching capabilities now via MCP with persistent question banks:
   - /quiz - Create quiz → teaching-toolkit:create_quiz
   - /exam - Create exam → teaching-toolkit:create_exam
   - /homework - Create homework → teaching-toolkit:create_homework
   - /rubric - Generate rubric → teaching-toolkit:generate_rubric
   - /solution - Create solutions → teaching-toolkit:create_solution_key
   - /feedback - Student feedback → teaching-toolkit:provide_feedback
   - /canvas - Publish to Canvas (NEW)
   ```

**Result:**
- 38 → 29 files (-24% additional)
- Persistent question banks (huge time saver!)
- Canvas integration (direct publishing)
- Can share teaching-toolkit MCP with academia

---

### Phase 4: Code Quality Tools (Week 5) ⭐⭐

**Time:** 4-6 hours
**Risk:** Low
**Impact:** Better code review, -3 files

**Current State:**
- 8 code commands, 5 overlap with plugins

**Actions:**

1. **Keep Unique Commands:**
   - `ecosystem-health.md` (R package ecosystem checks)
   - `rpkg-check.md` (R package specific)
   - `release.md` (release workflow)

2. **Delegate to Plugins:**
   - `debug.md` → `code:debug` plugin skill
   - `demo.md` → `code:demo` plugin skill
   - `docs-check.md` → `code:docs-check` plugin skill
   - `refactor.md` → `code:refactor` plugin skill
   - `test-gen.md` → `code:test-gen` plugin skill

3. **Update Code Hub**
   ```bash
   mv ~/.claude/commands/code/{debug,demo,docs-check,refactor,test-gen}.md ~/.claude/archive/
   ```

**Result:**
- 29 → 26 files (-10% additional)
- Better plugin utilization

---

### Phase 5: Site Automation MCP (Week 6) ⭐

**Time:** 6-8 hours
**Risk:** Medium
**Impact:** Automated docs deployment, -5 files

**Why MCP for Site:**
- Stateful build/deploy tracking
- GitHub Pages integration
- Multi-framework support (MkDocs, Quarto, Jekyll)

**New MCP Server:** `site-deployer`

**Tools (6):**
```typescript
{
  tools: [
    "init_docs_site",      // Initialize documentation site
    "build_site",          // Build site
    "preview_site",        // Local preview
    "deploy_site",         // Deploy to GitHub Pages
    "check_site",          // Validate docs
    "site_status"          // Build/deploy status
  ]
}
```

**Actions:**

1. **Create site-deployer MCP** (optional if Phase 3 goes well)
2. **Migrate site commands**
3. **Update site hub**

**Result:**
- 26 → 21 files (-19% additional)
- Automated deployment tracking

---

### Phase 6: Workflow Manager MCP (Week 7) ⭐

**Time:** 8-10 hours (optional)
**Risk:** High (ADHD workflow is critical)
**Impact:** Session persistence, -6 files

**Why MCP for Workflow:**
- Session state across days
- Task persistence
- Context recovery
- Focus mode tracking

**New MCP Server:** `workflow-manager`

**Tools (8):**
```typescript
{
  tools: [
    "focus_mode",          // Start focused session
    "brain_dump",          // Capture scattered thoughts
    "context_restore",     // "Where was I?"
    "next_action",         // Decision support
    "done_session",        // Wrap up
    "task_output",         // Background task results
    "task_status",         // Task tracking
    "task_cancel"          // Cancel background
  ]
}
```

**Database (SQLite):**
```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  focus_mode BOOLEAN,
  tasks_completed INTEGER,
  context TEXT  -- JSON blob
);

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  description TEXT,
  status TEXT,  -- pending, in_progress, done
  created_at TIMESTAMP
);
```

**CAUTION:** Only do this if you're confident the workflow commands work well as MCP.

---

## 📊 Projected Final State

### Before Refactoring

| Component | Count |
|-----------|-------|
| Command files | 59 |
| MCP servers | 3 |
| Plugins | 12 (underutilized) |
| Duplication | ~40% |

### After Refactoring

| Component | Count | Change |
|-----------|-------|--------|
| Command files | 32 | -27 (-46%) |
| MCP servers | 5 | +2 (+67%) |
| Plugins | 12 (well-utilized) | Better usage |
| Duplication | <10% | -75% |

**Command Breakdown:**
- 7 hubs (unchanged)
- 25 domain commands (down from 52)
- 0 meta docs (archived)

**MCP Servers:**
1. statistical-research (enhanced +2 tools)
2. project-refactor (unchanged)
3. docling (unchanged)
4. teaching-toolkit (NEW)
5. site-deployer (NEW, optional)
6. workflow-manager (NEW, optional)

---

## 🎯 Success Criteria

### Phase 1 Success
- [ ] 13 files archived
- [ ] Git hub updated to reference plugins
- [ ] All functionality still works
- [ ] Command count: 59 → 46

### Phase 2 Success
- [ ] 2 new tools in statistical-research MCP
- [ ] 8 research commands archived
- [ ] Research hub updated
- [ ] Command count: 46 → 38

### Phase 3 Success
- [ ] teaching-toolkit MCP server working
- [ ] Question bank operational
- [ ] Canvas integration working
- [ ] 9 teaching commands archived
- [ ] Command count: 38 → 29

### Phases 4-6 Success
- [ ] Code commands delegated to plugins
- [ ] Site automation MCP (optional)
- [ ] Workflow MCP (optional)
- [ ] Final command count: <35

---

## ⚠️ Risks & Mitigation

### Risk 1: Breaking Existing Workflows
**Mitigation:** Keep archived files for 1 month, easy rollback

### Risk 2: MCP Server Complexity
**Mitigation:** Start with Phase 1-2 (low risk), build confidence

### Risk 3: Plugin Limitations
**Mitigation:** Document workarounds, keep command as fallback if needed

### Risk 4: Time Investment
**Mitigation:** Each phase is independent, can pause anytime

---

## 📅 Recommended Timeline

**Week 1:** Phase 1 (Quick Wins)
- Monday: Archive meta docs
- Tuesday: Deprecate git/github commands
- Wednesday: Update hubs
- Thursday: Test everything
- Friday: Document outcomes

**Week 2:** Phase 2 (Research)
- Monday-Tuesday: Add 2 tools to statistical-research MCP
- Wednesday: Test tools
- Thursday: Deprecate research commands
- Friday: Update research hub

**Week 3-4:** Phase 3 (Teaching MCP)
- Week 3: Build teaching-toolkit MCP
- Week 4: Test, migrate commands, Canvas integration

**Week 5-7:** Phases 4-6 (Optional)
- Only if Phases 1-3 go well
- Code tools, site automation, workflow manager

---

## 🚀 Next Actions

### Immediate (Today)

1. **Review Analysis:**
   ```bash
   cat COMMAND-MCP-REFACTORING-ANALYSIS.md
   ```

2. **Decision Point:**
   - ✅ Proceed with Phase 1 this week?
   - ⏸️ Wait and plan more?
   - 🔄 Adjust strategy?

3. **If Proceeding:**
   ```bash
   # Create backup
   cp -r ~/.claude/commands ~/.claude/commands-backup-2025-12-19

   # Create archive directory
   mkdir -p ~/.claude/archive

   # Start Phase 1 (see detailed steps above)
   ```

### This Week (Phase 1)

- [ ] Backup current commands
- [ ] Archive 6 meta documents
- [ ] Deprecate 7 git/github commands
- [ ] Update git.md hub
- [ ] Test git workflows still work
- [ ] Document Phase 1 outcomes

### Next Week (Phase 2)

- [ ] Review Phase 1 success
- [ ] Add 2 tools to statistical-research MCP
- [ ] Test new tools
- [ ] Deprecate research commands
- [ ] Update research hub

---

## 📚 Reference Documents

- **Full Analysis:** `COMMAND-MCP-REFACTORING-ANALYSIS.md` (1,283 lines)
- **Project Status:** `.STATUS`
- **MCP Server Index:** `~/projects/dev-tools/_MCP_SERVERS.md`
- **Standards:** `STANDARDS-SUMMARY.md`

---

**Generated:** 2025-12-19
**Status:** 🟢 Ready to execute
**Recommended Start:** Phase 1 this week (low risk, high impact)
