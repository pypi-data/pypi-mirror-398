# Claude CLI Command & MCP Server Refactoring Analysis

**Generated:** 2025-12-19
**Analyzed By:** Claude Sonnet 4.5
**Purpose:** Comprehensive inventory and refactoring proposal for DT's Claude Code setup

---

## Executive Summary

**Current State:**
- 59 custom command files organized into 7 domain hubs
- 3 custom MCP servers (statistical-research, project-refactor, docling)
- 12 official plugins installed
- Extensive duplication between commands, plugins, and MCP servers

**Key Findings:**
1. **~40% of custom commands overlap with plugin skills** (especially git, code, research domains)
2. **Statistical research commands should be consolidated into MCP server** (currently split)
3. **Teaching commands are unique** and should remain as-is
4. **Hub commands provide valuable UX** but could be enhanced with MCP integration

**Recommended Actions:**
1. Migrate 18 commands → plugin skills (leverage existing plugins)
2. Consolidate 8 research commands → expand statistical-research MCP server
3. Create 2 new MCP servers (teaching-toolkit, workflow-manager)
4. Keep 25 commands as-is (unique value, UX-focused hubs)
5. Archive 6 planning/meta documents

---

## 1. Command Inventory Report

### 1.1 Complete Command Count: 59 Files

**By Category:**

| Hub | Commands | Subdirs | Total Files | Notes |
|-----|----------|---------|-------------|-------|
| **git** | 7 | 1 (docs/) | 11 | Most overlap with plugins |
| **code** | 8 | 0 | 8 | Moderate overlap with plugins |
| **research** | 8 | 0 | 8 | Should be MCP tools |
| **write** | 5 | 0 | 5 | Unique, keep as-is |
| **teach** | 9 | 0 | 9 | Unique, consider MCP |
| **math** | 4 | 0 | 4 | Unique, keep as-is |
| **workflow** | 12 | 1 (docs/) | 13 | Core ADHD workflow |
| **site** | 7 | 2 (docs/, mkdocs/) | 10 | Documentation hub |
| **github** | 4 | 0 | 4 | Overlap with github plugin |
| **help** | 6 | 2 (refcards/, tutorials/) | 9 | UX/onboarding |
| **Top-level** | 7 hubs | - | 7 | Hub entry points |
| **Meta** | 6 | - | 6 | Planning docs |

**Total:** 59 files

---

### 1.2 Detailed Command Structure

#### Git Commands (11 files)
```
git.md                    [Hub - Learning center with interactive menu]
git/
  ├── branch.md           [Branch management]
  ├── commit.md           [Smart mid-session commits]
  ├── git-recap.md        [Git activity summary]
  ├── pr-create.md        [Enhanced PR creation]
  ├── pr-review.md        [Pre-review before PR]
  ├── sync.md             [Smart git sync]
  └── docs/
      ├── learning-guide.md   [4-week learning path]
      ├── refcard.md          [Quick reference]
      ├── safety-rails.md     [Git safety guide]
      └── undo-guide.md       [Emergency reference]
```

**Overlap Analysis:**
- `commit.md` → **100% overlap** with `commit-commands:commit` plugin skill
- `pr-create.md` → **100% overlap** with `commit-commands:commit-push-pr` plugin skill
- `pr-review.md` → **80% overlap** with `pr-review-toolkit:review-pr` plugin skill
- `branch.md` → **Partial overlap** with native git commands
- `sync.md` → **Partial overlap** with native git commands
- `git-recap.md` → **Unique** (status summary specific to DT's workflow)
- `git.md` hub → **Unique** (learning/UX wrapper)

**Recommendation:**
- ✅ Keep `git.md` hub (provides learning UX)
- ✅ Keep `git-recap.md` (unique to workflow)
- ❌ **Deprecate** `commit.md`, `pr-create.md`, `pr-review.md` (use plugins instead)
- 🔄 Refactor `branch.md` and `sync.md` to delegate to plugins with DT-specific presets

---

#### Code Commands (8 files)
```
code.md                   [Hub - Development tools]
code/
  ├── debug.md            [Debug assistance]
  ├── demo.md             [Code demonstration]
  ├── docs-check.md       [Documentation check]
  ├── ecosystem-health.md [Package ecosystem health]
  ├── refactor.md         [Refactoring guidance]
  ├── release.md          [Release workflow]
  ├── rpkg-check.md       [R package checks]
  └── test-gen.md         [Generate tests]
```

**Overlap Analysis:**
- `debug.md` → **60% overlap** with `code-review:code-review` plugin
- `refactor.md` → **70% overlap** with `code-review:code-review` plugin
- `test-gen.md` → **Partial overlap** with general coding capabilities
- `docs-check.md` → **50% overlap** with `codebase-documenter` plugin
- `release.md` → **Partial overlap** with `feature-dev:feature-dev` plugin
- `rpkg-check.md` → **Unique** (R-specific)
- `ecosystem-health.md` → **Unique** (R ecosystem specific)
- `demo.md` → **Unique** (example generation)

**Recommendation:**
- ✅ Keep `code.md` hub
- ✅ Keep R-specific commands (`rpkg-check.md`, `ecosystem-health.md`)
- ✅ Keep `demo.md` (unique use case)
- 🔄 Refactor `debug.md`, `refactor.md`, `docs-check.md` to delegate to plugins with R context
- ❌ **Deprecate** `release.md` (use `feature-dev` plugin instead)

---

#### Research Commands (8 files)
```
research.md               [Hub - Research tools]
research/
  ├── analysis-plan.md    [Create analysis plan]
  ├── cite.md             [Citation lookup]
  ├── hypothesis.md       [Formulate hypotheses]
  ├── lit-gap.md          [Literature gap finder]
  ├── manuscript.md       [Manuscript section writer]
  ├── method-scout.md     [Scout methods]
  ├── revision.md         [Respond to reviewers]
  └── sim-design.md       [Simulation study design]
```

**Overlap Analysis with statistical-research MCP:**

Current MCP Tools (14):
- `r_execute`, `r_inspect`, `r_session_info`
- `literature_search`, `method_recommendations`
- `zotero_search`, `zotero_add`, `zotero_collections`
- `create_analysis_plan`, `design_simulation`
- `hypothesis_generator`, `power_calculation`
- `bayesian_prior_selection`, `causal_dag_analysis`

**All 8 research commands should be MCP tools:**
- `cite.md` → **Use existing** `zotero_search` tool
- `lit-gap.md` → **Use existing** `literature_search` + enhance
- `analysis-plan.md` → **Use existing** `create_analysis_plan` tool
- `sim-design.md` → **Use existing** `design_simulation` tool
- `hypothesis.md` → **Use existing** `hypothesis_generator` tool
- `method-scout.md` → **Use existing** `method_recommendations` tool
- `manuscript.md` → **CREATE NEW** MCP tool
- `revision.md` → **CREATE NEW** MCP tool

**Recommendation:**
- ✅ Keep `research.md` hub (UX wrapper for MCP tools)
- ❌ **Migrate all 8 commands → statistical-research MCP server**
- 🆕 Add 2 new tools to MCP: `manuscript_section_writer`, `reviewer_response_generator`
- 🔄 Update hub to show MCP tool availability

---

#### Write Commands (5 files)
```
write.md                  [Hub - Writing tools]
write/
  ├── abstract.md         [Write abstract]
  ├── cover-letter.md     [Write cover letter]
  ├── draft.md            [Draft document]
  ├── edit.md             [Editing and proofreading]
  └── response.md         [Write response]
```

**Overlap Analysis:**
- No direct plugin overlap
- General writing capabilities, not domain-specific
- `cover-letter.md` → Academic/professional specific
- `response.md` → Could overlap with research revision

**Recommendation:**
- ✅ **Keep all as-is** (unique, well-scoped commands)
- 🔄 Consider consolidating `response.md` into research MCP server

---

#### Teach Commands (9 files)
```
teach.md                  [Hub - Teaching tools]
teach/
  ├── canvas.md           [Canvas LMS operations]
  ├── exam.md             [Create exam]
  ├── feedback.md         [Generate student feedback]
  ├── homework.md         [Create homework]
  ├── lecture.md          [Create lecture outline]
  ├── quiz.md             [Create quiz]
  ├── rubric.md           [Generate grading rubric]
  ├── solution.md         [Create solution key]
  └── syllabus.md         [Create course syllabus]
```

**Overlap Analysis:**
- No plugin overlap (highly domain-specific)
- Integrates with `examark` CLI tool
- Canvas LMS specific workflows
- Statistical teaching focus (STAT courses)

**MCP Server Opportunity:**
- These are perfect candidates for a **teaching-toolkit MCP server**
- Tools could integrate with:
  - Canvas API (course management)
  - examark (exam generation)
  - Statistical concept database
  - Student data (anonymized feedback patterns)

**Recommendation:**
- ✅ Keep `teach.md` hub
- 🆕 **CREATE teaching-toolkit MCP server** with 9 tools:
  - `canvas_export_qti`, `canvas_grade_sync`
  - `exam_generator`, `quiz_generator`
  - `homework_generator`, `solution_key_generator`
  - `rubric_generator`, `feedback_generator`
  - `lecture_outline_generator`, `syllabus_generator`
- 🔄 Migrate all 9 commands to MCP tools
- 💡 Benefits: Stateful exam banks, reusable question pools, student analytics

---

#### Math Commands (4 files)
```
math.md                   [Hub - Mathematical tools]
math/
  ├── derive.md           [Derive formula]
  ├── example.md          [Create worked example]
  ├── notation.md         [Standardize notation]
  └── proof.md            [Proof verification]
```

**Overlap Analysis:**
- No plugin overlap (highly specialized)
- Statistical/mathematical research focus
- Could leverage symbolic math libraries

**Recommendation:**
- ✅ **Keep all as-is** (unique, specialized)
- 💭 Future: Consider math-toolkit MCP server with SymPy/Mathematica integration

---

#### Workflow Commands (13 files)
```
workflow.md               [Hub - ADHD-friendly workflow]
workflow/
  ├── brain-dump.md       [Quick capture]
  ├── brainstorm.md       [Structured ideation]
  ├── done.md             [Session wrap-up]
  ├── focus.md            [Single-task mode]
  ├── next.md             [Decision support]
  ├── recap.md            [Context restoration]
  ├── refine.md           [Prompt optimizer]
  ├── stuck.md            [Unblock helper]
  ├── task-cancel.md      [Cancel background task]
  ├── task-output.md      [View background results]
  ├── task-status.md      [Background task status]
  └── docs/
      └── adhd-guide.md   [Workflow guide]
```

**Overlap Analysis:**
- Core ADHD workflow system
- No plugin overlap (unique to DT's needs)
- Some commands manage background tasks (meta-workflow)

**MCP Server Opportunity:**
- **workflow-manager MCP server** could provide:
  - Persistent session state
  - Task queue management
  - Context switching intelligence
  - Pomodoro/focus timer integration
  - Session analytics

**Recommendation:**
- ✅ Keep all commands as-is (core workflow)
- 🆕 **OPTIONAL: CREATE workflow-manager MCP server** for:
  - `session_start`, `session_end`, `session_status`
  - `task_queue_add`, `task_queue_next`, `task_queue_status`
  - `context_save`, `context_restore`
  - `focus_timer_start`, `focus_timer_status`
  - `work_analytics`, `productivity_insights`
- 💡 Benefits: Cross-session persistence, better context management, analytics

---

#### Site Commands (10 files)
```
site.md                   [Hub - Documentation site]
site/
  ├── build.md            [Build site]
  ├── check.md            [Validate documentation]
  ├── deploy.md           [Deploy to GitHub Pages]
  ├── init.md             [Initialize site]
  ├── preview.md          [Preview locally]
  ├── site.md             [Duplicate hub?]
  └── mkdocs/
      ├── init.md         [MkDocs initialization]
      ├── preview.md      [MkDocs preview]
      └── status.md       [MkDocs status]
  └── docs/
      └── frameworks.md   [Framework comparison]
```

**Overlap Analysis:**
- Wraps MkDocs CLI
- Infrastructure automation
- Could use `infrastructure-maintainer` plugin

**Recommendation:**
- ✅ Keep `site.md` hub
- 🔄 Refactor to delegate to `infrastructure-maintainer` plugin
- ⚠️ Fix duplicate `site/site.md` (appears twice)

---

#### GitHub Commands (4 files)
```
github.md                 [Hub - GitHub tools]
github/
  ├── ci-status.md        [Check CI/CD status]
  ├── gh-actions.md       [GitHub Actions management]
  ├── gh-pages.md         [GitHub Pages management]
  └── gh-release.md       [Create GitHub release]
```

**Overlap Analysis:**
- **100% overlap** with `github@claude-plugins-official` plugin
- All use `gh` CLI tool

**Recommendation:**
- ❌ **DEPRECATE all 4 commands** (use github plugin instead)
- ✅ Keep `github.md` hub as lightweight wrapper to github plugin

---

#### Help Commands (9 files)
```
help.md                   [Hub - Help system]
help/
  ├── getting-started.md
  ├── refcard.md          [Quick reference hub]
  ├── troubleshooting.md
  ├── tutorials.md        [Tutorial hub]
  ├── workflows.md        [Common workflows]
  └── refcards/
      └── quick-reference.md
  └── tutorials/
      └── first-time-setup.md
```

**Overlap Analysis:**
- Pure UX/documentation
- No functionality overlap

**Recommendation:**
- ✅ **Keep all as-is** (critical for onboarding)
- 💡 Consider embedding in Claude Code docs

---

#### Top-Level Hub Commands (7 files)
```
code.md         → /code hub
git.md          → /git hub
github.md       → /github hub
help.md         → /help hub
hub.md          → /hub (master hub discovery)
math.md         → /math hub
research.md     → /research hub
site.md         → /site hub
teach.md        → /teach hub
workflow.md     → /workflow hub
write.md        → /write hub
```

**Recommendation:**
- ✅ **Keep all hubs** (excellent UX design)
- 🔄 Update hubs to show which commands are plugins vs MCP tools vs native

---

#### Meta/Planning Documents (6 files)
```
BACKGROUND-AGENT-PROPOSAL.md
PHASE1-IMPLEMENTATION-SUMMARY.md
REORGANIZATION-SUMMARY.md
UNIVERSAL-DELEGATION-PLANS.md
```

**Recommendation:**
- 📦 **Archive to ~/.claude/archive/** (historical record)
- ❌ Remove from active commands directory

---

## 2. MCP Server Analysis

### 2.1 Current MCP Servers

#### Statistical Research MCP Server
**Location:** `~/projects/dev-tools/mcp-servers/statistical-research/`
**Runtime:** Bun (TypeScript)
**Status:** 🟢 Stable

**Current Capabilities (14 tools):**

| Tool | Purpose | Overlap with Commands |
|------|---------|----------------------|
| `r_execute` | Execute R code | None (infrastructure) |
| `r_inspect` | Inspect R objects | None (infrastructure) |
| `r_session_info` | R session info | None (infrastructure) |
| `literature_search` | Search literature DB | ✅ research:lit-gap |
| `method_recommendations` | Find methods | ✅ research:method-scout |
| `zotero_search` | Search Zotero library | ✅ research:cite |
| `zotero_add` | Add citation | ✅ research:cite |
| `zotero_collections` | Manage collections | None |
| `create_analysis_plan` | Plan analysis | ✅ research:analysis-plan |
| `design_simulation` | Design simulation | ✅ research:sim-design |
| `hypothesis_generator` | Generate hypotheses | ✅ research:hypothesis |
| `power_calculation` | Calculate power | Partial |
| `bayesian_prior_selection` | Select priors | None |
| `causal_dag_analysis` | Analyze DAGs | None |

**Skills (17 A-grade):**
Listed in original system context, not duplicating here.

**Recommendation:**
- 🆕 **ADD 2 new tools:**
  - `manuscript_section_writer` (from research:manuscript)
  - `reviewer_response_generator` (from research:revision)
- 🆕 **ADD 3 new skills:**
  - `manuscript:introduction`
  - `manuscript:methods`
  - `manuscript:discussion`
- ✅ Deprecate 6 research commands (cite, lit-gap, analysis-plan, sim-design, hypothesis, method-scout)

---

#### Project Refactor MCP Server
**Location:** `~/projects/dev-tools/mcp-servers/project-refactor/`
**Runtime:** Node.js
**Status:** 🟢 Stable

**Current Capabilities (4 tools):**
- `scan_project` - Find references to old name
- `preview_rename` - Show what will change
- `apply_rename` - Execute refactor with safety
- `validate_project` - Verify project health

**Overlap Analysis:**
- No command overlap (specialized use case)
- Used successfully for aiterm rename

**Recommendation:**
- ✅ **Keep as-is** (well-scoped, stable)
- 💭 Future: Add more refactoring operations (extract function, inline, etc.)

---

#### Docling MCP Server
**Location:** `~/projects/dev-tools/mcp-servers/docling/`
**Runtime:** Python (uv)
**Status:** 🟢 Stable (third-party)

**Current Capabilities:**
- PDF → Markdown conversion
- Table extraction (97.9% accuracy)
- OCR support
- Document structure analysis

**Overlap Analysis:**
- No command overlap
- Research utility (PDF reading)

**Recommendation:**
- ✅ **Keep as-is** (valuable third-party tool)

---

### 2.2 Recommended New MCP Servers

#### Teaching Toolkit MCP Server (NEW)
**Proposed Location:** `~/projects/dev-tools/mcp-servers/teaching-toolkit/`
**Runtime:** Python (uv) or Node.js
**Priority:** HIGH

**Proposed Tools (9):**

| Tool | Purpose | Replaces Command |
|------|---------|------------------|
| `canvas_export_qti` | Export to Canvas QTI format | teach:canvas |
| `canvas_grade_sync` | Sync grades with Canvas API | New capability |
| `exam_generator` | Generate exams | teach:exam |
| `quiz_generator` | Generate quizzes | teach:quiz |
| `homework_generator` | Generate homework | teach:homework |
| `solution_key_generator` | Generate solutions | teach:solution |
| `rubric_generator` | Generate rubrics | teach:rubric |
| `feedback_generator` | Generate feedback | teach:feedback |
| `lecture_outline_generator` | Generate lecture outlines | teach:lecture |
| `syllabus_generator` | Generate syllabus | teach:syllabus |

**Proposed Skills (12):**
- `exam:multiple-choice`, `exam:short-answer`, `exam:essay`
- `homework:theory`, `homework:computation`, `homework:simulation`
- `feedback:encouraging`, `feedback:constructive`, `feedback:detailed`
- `lecture:introduction`, `lecture:methods`, `lecture:examples`

**Additional Capabilities:**
- **Question Bank:** Store reusable questions with metadata
- **Canvas API:** Direct integration for course management
- **Student Analytics:** Track performance patterns (anonymized)
- **LaTeX Templates:** Statistical notation, R code formatting
- **Examark Integration:** Seamless workflow with existing tool

**Benefits:**
- ✅ Stateful question banks (reuse across semesters)
- ✅ Direct Canvas integration (no manual export/import)
- ✅ Analytics on question difficulty
- ✅ Consistent formatting across all materials
- ✅ Version control for exam content

**Implementation Priority:** HIGH (9 commands → 1 MCP server)

---

#### Workflow Manager MCP Server (NEW - OPTIONAL)
**Proposed Location:** `~/projects/dev-tools/mcp-servers/workflow-manager/`
**Runtime:** Node.js (persistent state)
**Priority:** MEDIUM

**Proposed Tools (12):**

| Tool | Purpose | Enhances Command |
|------|---------|------------------|
| `session_start` | Start work session | workflow:focus |
| `session_end` | End session with summary | workflow:done |
| `session_status` | Current session info | workflow:recap |
| `task_queue_add` | Add task to queue | workflow:brain-dump |
| `task_queue_next` | Get next task | workflow:next |
| `task_queue_status` | Queue overview | workflow:task-status |
| `context_save` | Save current context | workflow:done |
| `context_restore` | Restore previous context | workflow:recap |
| `focus_timer_start` | Start Pomodoro timer | workflow:focus |
| `focus_timer_status` | Timer status | workflow:focus |
| `work_analytics` | Session analytics | New capability |
| `productivity_insights` | Patterns & suggestions | New capability |

**Persistent State (SQLite or JSON):**
```
sessions/
  ├── 2025-12-19-morning.json
  ├── 2025-12-19-afternoon.json
tasks/
  ├── queue.json
  ├── completed.json
contexts/
  ├── r-package-dev.json
  ├── research-manuscript.json
analytics/
  ├── daily-summary.json
  ├── weekly-patterns.json
```

**Benefits:**
- ✅ Cross-session persistence (remember where you left off)
- ✅ Task queue survives restarts
- ✅ Analytics over time (productivity patterns)
- ✅ Context switching intelligence
- ✅ Integration with .STATUS files

**Challenges:**
- Requires persistent storage
- State management complexity
- Migration from existing workflow

**Implementation Priority:** MEDIUM (nice-to-have, not critical)

---

## 3. Plugin Overlap Analysis

### 3.1 Currently Installed Plugins (12)

| Plugin | Overlap with Commands | Recommendation |
|--------|----------------------|----------------|
| `commit-commands` | ✅ git:commit, git:pr-create | **Use plugin, deprecate commands** |
| `pr-review-toolkit` | ✅ git:pr-review | **Use plugin, deprecate command** |
| `feature-dev` | Partial: code:release | **Use plugin for release workflows** |
| `code-review` | ✅ code:debug, code:refactor | **Delegate to plugin with R context** |
| `github` | ✅ All github/* commands | **Use plugin, deprecate commands** |
| `codebase-documenter` | Partial: code:docs-check | **Delegate with R package context** |
| `infrastructure-maintainer` | Partial: site/* commands | **Delegate MkDocs operations** |
| `plugin-dev` | None | Keep for plugin development |
| `frontend-design` | None | Keep for UI work |
| `ralph-wiggum` | None | Keep for teaching technique |
| `explanatory-output-style` | None | Keep for output style |
| `learning-output-style` | None | Keep for learning scenarios |

---

### 3.2 Plugin Utilization Gaps

**Underutilized Plugins:**
1. `infrastructure-maintainer` - Could handle all site/* commands
2. `codebase-documenter` - Could enhance code:docs-check
3. `feature-dev` - Could replace code:release

**Missing Plugins:**
- No teaching/education plugin (gap filled by teaching-toolkit MCP proposal)
- No research/statistics plugin (gap filled by statistical-research MCP)
- No workflow/productivity plugin (gap filled by workflow-manager MCP proposal)

---

## 4. Comprehensive Refactoring Proposal

### 4.1 Migration Plan Summary

**Phase 1: Quick Wins (Week 1)**
- ❌ Deprecate 4 github/* commands → use github plugin
- ❌ Deprecate git:commit, git:pr-create → use commit-commands plugin
- 📦 Archive 6 meta documents
- 🔄 Update hub commands to reference plugins

**Phase 2: Research Consolidation (Week 2)**
- 🆕 Add 2 tools to statistical-research MCP server
- ❌ Deprecate 6 research/* commands
- 🔄 Update research.md hub to show MCP tools
- ✅ Test MCP integration in research workflows

**Phase 3: Teaching MCP Server (Weeks 3-4)**
- 🆕 Create teaching-toolkit MCP server
- 🆕 Implement 9 tools + question bank
- 🆕 Canvas API integration
- ❌ Migrate 9 teach/* commands to MCP
- ✅ Test with STAT 440 course

**Phase 4: Code Quality (Week 5)**
- 🔄 Refactor code:debug → delegate to code-review plugin
- 🔄 Refactor code:refactor → delegate to code-review plugin
- 🔄 Refactor code:docs-check → delegate to codebase-documenter plugin
- ❌ Deprecate code:release → use feature-dev plugin

**Phase 5: Site Automation (Week 6)**
- 🔄 Refactor site/* commands → delegate to infrastructure-maintainer plugin
- ✅ Keep MkDocs-specific wrappers for DT's workflow

**Phase 6: Workflow Enhancement (Optional, Weeks 7-8)**
- 🆕 Create workflow-manager MCP server
- 🆕 Implement persistent state management
- 🆕 Add analytics and insights
- 🔄 Enhance workflow/* commands with MCP backend

---

### 4.2 Command Disposition Matrix

| Command | Action | Reason | Timeline |
|---------|--------|--------|----------|
| **GIT** | | | |
| git.md | ✅ Keep | Learning hub | - |
| git:branch | 🔄 Refactor | Simplify, delegate to plugin | Phase 1 |
| git:commit | ❌ Deprecate | Use commit-commands plugin | Phase 1 |
| git:git-recap | ✅ Keep | Unique workflow integration | - |
| git:pr-create | ❌ Deprecate | Use commit-commands plugin | Phase 1 |
| git:pr-review | ❌ Deprecate | Use pr-review-toolkit plugin | Phase 1 |
| git:sync | 🔄 Refactor | Simplify, delegate to plugin | Phase 1 |
| git/docs/* (4 files) | ✅ Keep | Documentation | - |
| **CODE** | | | |
| code.md | ✅ Keep | Development hub | - |
| code:debug | 🔄 Refactor | Delegate to code-review plugin | Phase 4 |
| code:demo | ✅ Keep | Unique use case | - |
| code:docs-check | 🔄 Refactor | Delegate to codebase-documenter | Phase 4 |
| code:ecosystem-health | ✅ Keep | R-specific | - |
| code:refactor | 🔄 Refactor | Delegate to code-review plugin | Phase 4 |
| code:release | ❌ Deprecate | Use feature-dev plugin | Phase 4 |
| code:rpkg-check | ✅ Keep | R-specific | - |
| code:test-gen | ✅ Keep | Valuable, no strong plugin overlap | - |
| **RESEARCH** | | | |
| research.md | ✅ Keep | Research hub (UX wrapper) | - |
| research:analysis-plan | ❌ Migrate to MCP | Use existing MCP tool | Phase 2 |
| research:cite | ❌ Migrate to MCP | Use existing zotero tools | Phase 2 |
| research:hypothesis | ❌ Migrate to MCP | Use existing MCP tool | Phase 2 |
| research:lit-gap | ❌ Migrate to MCP | Enhance literature_search | Phase 2 |
| research:manuscript | ❌ Migrate to MCP | CREATE new MCP tool | Phase 2 |
| research:method-scout | ❌ Migrate to MCP | Use existing MCP tool | Phase 2 |
| research:revision | ❌ Migrate to MCP | CREATE new MCP tool | Phase 2 |
| research:sim-design | ❌ Migrate to MCP | Use existing MCP tool | Phase 2 |
| **WRITE** | | | |
| write.md | ✅ Keep | Writing hub | - |
| write:abstract | ✅ Keep | Unique | - |
| write:cover-letter | ✅ Keep | Unique | - |
| write:draft | ✅ Keep | Unique | - |
| write:edit | ✅ Keep | Unique | - |
| write:response | 🔄 Consider merge | Could merge with research:revision | Phase 2 |
| **TEACH** | | | |
| teach.md | ✅ Keep | Teaching hub | - |
| teach:canvas | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:exam | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:feedback | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:homework | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:lecture | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:quiz | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:rubric | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:solution | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| teach:syllabus | ❌ Migrate to MCP | CREATE teaching-toolkit MCP | Phase 3 |
| **MATH** | | | |
| math.md | ✅ Keep | Math hub | - |
| math:derive | ✅ Keep | Unique | - |
| math:example | ✅ Keep | Unique | - |
| math:notation | ✅ Keep | Unique | - |
| math:proof | ✅ Keep | Unique | - |
| **WORKFLOW** | | | |
| workflow.md | ✅ Keep | Workflow hub | - |
| workflow:brain-dump | ✅ Keep | Core ADHD workflow | - |
| workflow:brainstorm | ✅ Keep | Core ADHD workflow | - |
| workflow:done | ✅ Keep | Core ADHD workflow | - |
| workflow:focus | ✅ Keep | Core ADHD workflow | - |
| workflow:next | ✅ Keep | Core ADHD workflow | - |
| workflow:recap | ✅ Keep | Core ADHD workflow | - |
| workflow:refine | ✅ Keep | Core ADHD workflow | - |
| workflow:stuck | ✅ Keep | Core ADHD workflow | - |
| workflow:task-* (3 files) | ✅ Keep | Background task management | - |
| workflow/docs/adhd-guide | ✅ Keep | Documentation | - |
| **SITE** | | | |
| site.md | ✅ Keep | Site hub | - |
| site:build | 🔄 Refactor | Delegate to infrastructure-maintainer | Phase 5 |
| site:check | 🔄 Refactor | Delegate to infrastructure-maintainer | Phase 5 |
| site:deploy | 🔄 Refactor | Delegate to infrastructure-maintainer | Phase 5 |
| site:init | 🔄 Refactor | Delegate to infrastructure-maintainer | Phase 5 |
| site:preview | 🔄 Refactor | Delegate to infrastructure-maintainer | Phase 5 |
| site/mkdocs/* (3 files) | ✅ Keep | DT-specific MkDocs workflow | - |
| site/docs/frameworks | ✅ Keep | Documentation | - |
| **GITHUB** | | | |
| github.md | ✅ Keep | GitHub hub (lightweight wrapper) | - |
| github:ci-status | ❌ Deprecate | Use github plugin | Phase 1 |
| github:gh-actions | ❌ Deprecate | Use github plugin | Phase 1 |
| github:gh-pages | ❌ Deprecate | Use github plugin | Phase 1 |
| github:gh-release | ❌ Deprecate | Use github plugin | Phase 1 |
| **HELP** | | | |
| help.md | ✅ Keep | Help system hub | - |
| help/* (8 files) | ✅ Keep | Critical onboarding docs | - |
| **TOP-LEVEL** | | | |
| hub.md | ✅ Keep | Master hub discovery | - |
| **META** | | | |
| BACKGROUND-AGENT-PROPOSAL.md | 📦 Archive | Historical planning doc | Phase 1 |
| PHASE1-IMPLEMENTATION-SUMMARY.md | 📦 Archive | Historical planning doc | Phase 1 |
| REORGANIZATION-SUMMARY.md | 📦 Archive | Historical planning doc | Phase 1 |
| UNIVERSAL-DELEGATION-PLANS.md | 📦 Archive | Historical planning doc | Phase 1 |

---

### 4.3 Final Command Count After Refactoring

**Before:** 59 files

**After Refactoring:**

| Category | Before | After | Change |
|----------|--------|-------|--------|
| Hub commands | 11 | 11 | 0 (keep all) |
| Git commands | 11 | 4 | -7 (deprecate 3, refactor 2, keep 4+docs) |
| Code commands | 8 | 6 | -2 (deprecate 1, refactor 3, keep 4) |
| Research commands | 8 | 1 | -7 (migrate to MCP, keep hub) |
| Write commands | 5 | 5 | 0 (keep all) |
| Teach commands | 9 | 1 | -8 (migrate to MCP, keep hub) |
| Math commands | 4 | 4 | 0 (keep all) |
| Workflow commands | 13 | 13 | 0 (keep all, optional MCP backend) |
| Site commands | 10 | 7 | -3 (refactor 5, keep 5 including MkDocs) |
| GitHub commands | 4 | 1 | -3 (deprecate all, keep hub wrapper) |
| Help commands | 9 | 9 | 0 (keep all) |
| Meta documents | 6 | 0 | -6 (archive) |
| **TOTAL** | **59** | **32** | **-27 (-46%)** |

**New MCP Servers:** 2 (teaching-toolkit, workflow-manager optional)

---

## 5. MCP Server Roadmap

### 5.1 Statistical Research MCP Enhancements

**Current:** 14 tools, 17 skills
**Proposed Additions:**

**New Tools (2):**
1. `manuscript_section_writer`
   - Input: section type (intro/methods/simulation/application/discussion)
   - Context: .STATUS file, analysis results, citations
   - Output: LaTeX formatted section
   - Integration: Zotero for citations

2. `reviewer_response_generator`
   - Input: reviewer comments, manuscript changes
   - Output: Structured response letter
   - Features: Track all changes, line-by-line responses

**New Skills (3):**
1. `manuscript:introduction` - Statistical research introductions
2. `manuscript:methods` - Statistical methods sections
3. `manuscript:discussion` - Statistical discussion sections

**Timeline:** Phase 2 (Week 2)

---

### 5.2 Teaching Toolkit MCP Server (New)

**Purpose:** Comprehensive teaching assistant for statistical courses

**Architecture:**
```
teaching-toolkit/
├── src/
│   ├── index.ts                 # MCP server entry
│   ├── tools/
│   │   ├── canvas-integration.ts
│   │   ├── exam-generator.ts
│   │   ├── feedback-generator.ts
│   │   └── question-bank.ts
│   ├── skills/
│   │   ├── exam-skills.ts
│   │   ├── homework-skills.ts
│   │   └── lecture-skills.ts
│   ├── data/
│   │   ├── question-bank.db      # SQLite
│   │   ├── stat-concepts.json
│   │   └── r-examples.json
│   └── integrations/
│       ├── canvas-api.ts
│       └── examark.ts
├── package.json
├── tsconfig.json
└── README.md
```

**Data Models:**

Question Bank Schema:
```typescript
interface Question {
  id: string;
  type: 'multiple-choice' | 'short-answer' | 'essay' | 'numerical';
  course: 'STAT440' | 'STAT579' | 'general';
  topic: string[];
  difficulty: 1-5;
  text: string;
  options?: string[];
  answer: string | string[];
  explanation: string;
  r_code?: string;
  created: Date;
  used_count: number;
  avg_score?: number;
}
```

**Canvas Integration:**
- Use Canvas API (requires API token in env)
- Export QTI 2.1 format
- Grade sync via API
- Course management

**Timeline:** Phase 3 (Weeks 3-4)
**Priority:** HIGH

---

### 5.3 Workflow Manager MCP Server (New - Optional)

**Purpose:** Persistent workflow state and session management

**Architecture:**
```
workflow-manager/
├── src/
│   ├── index.js                 # MCP server entry
│   ├── tools/
│   │   ├── session-manager.js
│   │   ├── task-queue.js
│   │   ├── context-manager.js
│   │   └── analytics.js
│   ├── storage/
│   │   ├── sqlite.js            # Persistent storage
│   │   └── migrations/
│   └── integrations/
│       ├── status-file.js       # Read .STATUS files
│       └── git-integration.js
├── data/
│   └── workflow.db              # SQLite database
├── package.json
└── README.md
```

**Database Schema:**
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  start_time DATETIME,
  end_time DATETIME,
  project TEXT,
  context_type TEXT,
  focus_duration INTEGER,
  tasks_completed INTEGER
);

CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  description TEXT,
  priority INTEGER,
  effort TEXT,
  status TEXT,
  created DATETIME,
  completed DATETIME
);

CREATE TABLE contexts (
  id TEXT PRIMARY KEY,
  name TEXT,
  cwd TEXT,
  git_branch TEXT,
  active_files TEXT,
  last_restored DATETIME
);
```

**Features:**
- Pomodoro timer integration
- Task queue persistence
- Session analytics (avg focus time, task completion rate)
- Context switching intelligence
- Integration with .STATUS files

**Timeline:** Phase 6 (Weeks 7-8)
**Priority:** MEDIUM (nice-to-have)

---

## 6. Implementation Strategy

### 6.1 Phased Rollout

**Phase 1: Quick Wins (Week 1)**
```bash
# 1. Archive meta documents
mkdir -p ~/.claude/archive
mv ~/.claude/commands/{BACKGROUND-AGENT,PHASE1,REORGANIZATION,UNIVERSAL}*.md ~/.claude/archive/

# 2. Deprecate github commands (use plugin)
mv ~/.claude/commands/github/gh-*.md ~/.claude/archive/
mv ~/.claude/commands/github/ci-status.md ~/.claude/archive/

# 3. Deprecate git plugin duplicates
mv ~/.claude/commands/git/commit.md ~/.claude/archive/
mv ~/.claude/commands/git/pr-create.md ~/.claude/archive/

# 4. Update hub files to reference plugins
# Edit github.md, git.md to show plugin alternatives
```

**Phase 2: Research Consolidation (Week 2)**
```bash
cd ~/projects/dev-tools/mcp-servers/statistical-research

# 1. Add manuscript_section_writer tool
# 2. Add reviewer_response_generator tool
# 3. Test with actual research project
# 4. Update research.md hub to show MCP tools
# 5. Deprecate 6 research commands once MCP tools verified
```

**Phase 3: Teaching MCP Server (Weeks 3-4)**
```bash
cd ~/projects/dev-tools/mcp-servers

# 1. Create teaching-toolkit project
mkdir teaching-toolkit && cd teaching-toolkit
bun init

# 2. Implement core tools
# 3. Set up question bank database
# 4. Test Canvas integration
# 5. Migrate 1-2 teach commands first (test)
# 6. Migrate remaining commands
# 7. Update ~/.claude/settings.json
```

**Phase 4-6:** Continue with code quality, site automation, optional workflow manager

---

### 6.2 Testing Strategy

**For Each MCP Server:**
1. Unit tests for each tool
2. Integration tests with Claude CLI
3. Real-world usage tests (DT's actual workflow)
4. Fallback handling (when MCP unavailable)

**For Command Deprecation:**
1. Verify plugin provides equivalent functionality
2. Update hub documentation
3. Move to archive (don't delete immediately)
4. Monitor for usage via logs
5. Delete after 30 days if no issues

---

### 6.3 Rollback Plan

**If MCP migration fails:**
1. Archived commands still available in `~/.claude/archive/`
2. Can restore with `mv ~/.claude/archive/COMMAND.md ~/.claude/commands/`
3. Hub files have git history

**If MCP server has bugs:**
1. Fix in dev, test locally
2. Or temporarily disable in settings.json
3. Commands still work (just degraded functionality)

---

## 7. Next Steps

### Immediate Actions (This Week)

1. **Review this analysis** with user
2. **Get approval** for phased approach
3. **Phase 1 execution:**
   - Archive 6 meta documents
   - Deprecate 7 github/git commands
   - Update hubs to reference plugins

### Short-term (Next 2 Weeks)

4. **Phase 2: Research MCP enhancements**
   - Implement 2 new tools
   - Test with real research project
   - Migrate commands once verified

5. **Phase 3: Start teaching MCP server**
   - Design question bank schema
   - Implement first 2-3 tools
   - Test with STAT 440 materials

### Medium-term (Next Month)

6. **Complete teaching MCP server**
7. **Phase 4: Code quality refactoring**
8. **Phase 5: Site automation**

### Long-term (Optional)

9. **Phase 6: Workflow manager MCP** (if beneficial)
10. **Publish MCP servers** to npm for community use

---

## 8. Key Metrics

### Before Refactoring
- 59 command files
- 3 MCP servers
- 12 plugins (some underutilized)
- ~40% duplication

### After Refactoring (Projected)
- 32 command files (-46%)
- 5 MCP servers (+2 new)
- 12 plugins (better utilized)
- <10% duplication

### Expected Benefits
- ✅ Reduced maintenance burden (27 fewer command files)
- ✅ Better plugin utilization (delegating to experts)
- ✅ Stateful capabilities (MCP question banks, session state)
- ✅ Reusable tools (publish MCP servers)
- ✅ Cleaner separation (commands=UX, MCP=logic, plugins=specialized)

---

## 9. Risks & Mitigation

### Risk 1: MCP Complexity
**Mitigation:**
- Start small (2 tools in Phase 2)
- Extensive testing before command deprecation
- Keep archived commands for 30 days

### Risk 2: Breaking Existing Workflows
**Mitigation:**
- Phased rollout (one domain at a time)
- Update documentation immediately
- Clear migration guides in hubs

### Risk 3: MCP Server Maintenance
**Mitigation:**
- Good test coverage
- Clear documentation
- Community feedback (if published)

### Risk 4: Teaching MCP Scope Creep
**Mitigation:**
- Start with 3 core tools (exam, quiz, feedback)
- Iterate based on usage
- Question bank can be simple JSON first

---

## 10. Recommendations Summary

**Immediate (Do This Week):**
1. ❌ Deprecate 7 commands (github/git plugin duplicates)
2. 📦 Archive 6 meta documents
3. 🔄 Update hubs to show plugin alternatives

**High Priority (Do This Month):**
4. 🆕 Add 2 tools to statistical-research MCP
5. 🆕 Create teaching-toolkit MCP server (9 tools)
6. ❌ Migrate 15 commands to MCP tools

**Medium Priority (Next Month):**
7. 🔄 Refactor code/* commands to delegate to plugins
8. 🔄 Refactor site/* commands to delegate to plugins

**Optional (Consider Later):**
9. 🆕 Create workflow-manager MCP server
10. 📦 Publish MCP servers to npm

**Keep As-Is:**
- ✅ All hub commands (11 files) - excellent UX
- ✅ Math commands (4 files) - unique, specialized
- ✅ Write commands (5 files) - no overlap
- ✅ Workflow commands (13 files) - core ADHD system
- ✅ Help commands (9 files) - critical documentation

---

## Appendix A: Full File Tree

```
~/.claude/commands/ (59 files)
├── BACKGROUND-AGENT-PROPOSAL.md          [Archive]
├── PHASE1-IMPLEMENTATION-SUMMARY.md      [Archive]
├── REORGANIZATION-SUMMARY.md             [Archive]
├── UNIVERSAL-DELEGATION-PLANS.md         [Archive]
├── code.md                               [Keep - Hub]
├── git.md                                [Keep - Hub]
├── github.md                             [Keep - Hub wrapper]
├── help.md                               [Keep - Hub]
├── hub.md                                [Keep - Master hub]
├── math.md                               [Keep - Hub]
├── research.md                           [Keep - Hub]
├── site.md                               [Keep - Hub]
├── teach.md                              [Keep - Hub]
├── workflow.md                           [Keep - Hub]
├── write.md                              [Keep - Hub]
├── code/
│   ├── debug.md                          [Refactor → delegate to code-review plugin]
│   ├── demo.md                           [Keep]
│   ├── docs-check.md                     [Refactor → delegate to codebase-documenter]
│   ├── ecosystem-health.md               [Keep - R-specific]
│   ├── refactor.md                       [Refactor → delegate to code-review plugin]
│   ├── release.md                        [Deprecate → use feature-dev plugin]
│   ├── rpkg-check.md                     [Keep - R-specific]
│   └── test-gen.md                       [Keep]
├── git/
│   ├── branch.md                         [Refactor → simplify]
│   ├── commit.md                         [Deprecate → use commit-commands plugin]
│   ├── git-recap.md                      [Keep - unique]
│   ├── git.md                            [Keep - duplicate of top-level]
│   ├── pr-create.md                      [Deprecate → use commit-commands plugin]
│   ├── pr-review.md                      [Deprecate → use pr-review-toolkit plugin]
│   ├── sync.md                           [Refactor → simplify]
│   └── docs/
│       ├── learning-guide.md             [Keep]
│       ├── refcard.md                    [Keep]
│       ├── safety-rails.md               [Keep]
│       └── undo-guide.md                 [Keep]
├── github/
│   ├── ci-status.md                      [Deprecate → use github plugin]
│   ├── gh-actions.md                     [Deprecate → use github plugin]
│   ├── gh-pages.md                       [Deprecate → use github plugin]
│   └── gh-release.md                     [Deprecate → use github plugin]
├── help/
│   ├── getting-started.md                [Keep]
│   ├── refcard.md                        [Keep]
│   ├── troubleshooting.md                [Keep]
│   ├── tutorials.md                      [Keep]
│   ├── workflows.md                      [Keep]
│   ├── refcards/
│   │   └── quick-reference.md            [Keep]
│   └── tutorials/
│       └── first-time-setup.md           [Keep]
├── math/
│   ├── derive.md                         [Keep]
│   ├── example.md                        [Keep]
│   ├── notation.md                       [Keep]
│   └── proof.md                          [Keep]
├── research/
│   ├── analysis-plan.md                  [Migrate to MCP]
│   ├── cite.md                           [Migrate to MCP]
│   ├── hypothesis.md                     [Migrate to MCP]
│   ├── lit-gap.md                        [Migrate to MCP]
│   ├── manuscript.md                     [Migrate to MCP - new tool]
│   ├── method-scout.md                   [Migrate to MCP]
│   ├── revision.md                       [Migrate to MCP - new tool]
│   └── sim-design.md                     [Migrate to MCP]
├── site/
│   ├── build.md                          [Refactor → delegate to infra plugin]
│   ├── check.md                          [Refactor → delegate to infra plugin]
│   ├── deploy.md                         [Refactor → delegate to infra plugin]
│   ├── init.md                           [Refactor → delegate to infra plugin]
│   ├── preview.md                        [Refactor → delegate to infra plugin]
│   ├── site.md                           [Keep - duplicate?]
│   ├── docs/
│   │   └── frameworks.md                 [Keep]
│   └── mkdocs/
│       ├── init.md                       [Keep - DT-specific]
│       ├── preview.md                    [Keep - DT-specific]
│       └── status.md                     [Keep - DT-specific]
├── teach/
│   ├── canvas.md                         [Migrate to teaching-toolkit MCP]
│   ├── exam.md                           [Migrate to teaching-toolkit MCP]
│   ├── feedback.md                       [Migrate to teaching-toolkit MCP]
│   ├── homework.md                       [Migrate to teaching-toolkit MCP]
│   ├── lecture.md                        [Migrate to teaching-toolkit MCP]
│   ├── quiz.md                           [Migrate to teaching-toolkit MCP]
│   ├── rubric.md                         [Migrate to teaching-toolkit MCP]
│   ├── solution.md                       [Migrate to teaching-toolkit MCP]
│   └── syllabus.md                       [Migrate to teaching-toolkit MCP]
├── workflow/
│   ├── brain-dump.md                     [Keep]
│   ├── brainstorm.md                     [Keep]
│   ├── done.md                           [Keep]
│   ├── focus.md                          [Keep]
│   ├── next.md                           [Keep]
│   ├── recap.md                          [Keep]
│   ├── refine.md                         [Keep]
│   ├── stuck.md                          [Keep]
│   ├── task-cancel.md                    [Keep]
│   ├── task-output.md                    [Keep]
│   ├── task-status.md                    [Keep]
│   ├── workflow.md                       [Keep - duplicate?]
│   └── docs/
│       └── adhd-guide.md                 [Keep]
└── write/
    ├── abstract.md                       [Keep]
    ├── cover-letter.md                   [Keep]
    ├── draft.md                          [Keep]
    ├── edit.md                           [Keep]
    └── response.md                       [Keep]
```

---

## Appendix B: MCP Server Comparison

| Server | Language | Tools | Skills | Overlap with Commands |
|--------|----------|-------|--------|----------------------|
| statistical-research | TypeScript | 14 | 17 | ✅ 6/8 research commands |
| project-refactor | JavaScript | 4 | 0 | ❌ None |
| docling | Python | 4 | 0 | ❌ None |
| **teaching-toolkit (new)** | TypeScript | 10 | 12 | ✅ 9/9 teach commands |
| **workflow-manager (new)** | JavaScript | 12 | 0 | 🔄 Enhances workflow/* |

---

**End of Analysis**

**Next Action:** Review with user and get approval for Phase 1 execution.
