# Command & MCP Refactoring Action Plan - REVISED

**Date:** 2025-12-19 (Revised for R-Development MCP consolidation)
**Based on:** COMMAND-MCP-REFACTORING-ANALYSIS-REVISED.md

> **TL;DR:** Rename `statistical-research` → `r-development` MCP and consolidate ALL R-related commands (10 files) into a comprehensive 20-tool R development toolkit.

---

## 📊 Current State Summary

**Inventory:**
- 59 custom command files (7 domain hubs)
- 3 custom MCP servers (statistical-research, project-refactor, docling)
- 12 plugins installed
- ~40% duplication
- **KEY INSIGHT:** 59% of commands (35/59) are R-ecosystem related!

**Problems:**
- Git commands duplicate `commit-commands` plugin
- R-related commands scattered (code/, research/, site/)
- statistical-research MCP misnamed (it's comprehensive R-dev toolkit)
- Teaching commands lack stateful capabilities
- Meta planning docs clutter command directory

---

## 🎯 Goals - REVISED

1. **Consolidate R ecosystem** - All R commands → r-development MCP
2. **Reduce duplication** from 40% to <10%
3. **Better plugin utilization** - delegate to specialized plugins
4. **Rename MCP for clarity** - statistical-research → r-development
5. **Enable sharing** - publish r-development MCP to community

---

## 📋 6-Phase Implementation Plan - REVISED

### Phase 1: Quick Wins (Week 1) ⭐⭐⭐

**Time:** 1-2 hours
**Risk:** Very Low
**Impact:** Immediate cleanup, -13 files

**Actions:**

```bash
# 1. Backup everything first
cp -r ~/.claude/commands ~/.claude/commands-backup-2025-12-19

# 2. Create archive directory
mkdir -p ~/.claude/archive

# 3. Archive Meta Documents (6 files)
mv ~/.claude/commands/BACKGROUND-AGENT-PROPOSAL.md ~/.claude/archive/
mv ~/.claude/commands/PHASE1-IMPLEMENTATION-SUMMARY.md ~/.claude/archive/
mv ~/.claude/commands/REORGANIZATION-SUMMARY.md ~/.claude/archive/
mv ~/.claude/commands/UNIVERSAL-DELEGATION-PLANS.md ~/.claude/archive/
# (+ 2 more meta docs)

# 4. Deprecate GitHub Commands (4 files) - use github plugin
mv ~/.claude/commands/github/ci-status.md ~/.claude/archive/
mv ~/.claude/commands/github/gh-actions.md ~/.claude/archive/
mv ~/.claude/commands/github/gh-pages.md ~/.claude/archive/
mv ~/.claude/commands/github/gh-release.md ~/.claude/archive/

# 5. Deprecate Git Plugin Duplicates (3 files)
mv ~/.claude/commands/git/commit.md ~/.claude/archive/
mv ~/.claude/commands/git/pr-create.md ~/.claude/archive/
mv ~/.claude/commands/git/pr-review.md ~/.claude/archive/

# 6. Update Git Hub to Reference Plugins
# Edit ~/.claude/commands/git.md
```

**Edit `~/.claude/commands/git.md`:**
```markdown
## Git Workflows

### Quick Actions
- `/commit` → Use `commit-commands:commit` plugin ✨
- `/pr-create` → Use `commit-commands:commit-push-pr` plugin ✨
- `/pr-review` → Use `pr-review-toolkit:review-pr` plugin ✨

### Still Available
- `/git-recap` - Git activity summary
- `/branch` - Branch management
- `/sync` - Smart git sync

### Documentation
- `/git:learning-guide` - Learn git commands
- `/git:refcard` - Quick reference
- `/git:safety-rails` - Safety guide
- `/git:undo-guide` - Emergency undo reference
```

**Edit `~/.claude/commands/github.md`:**
```markdown
## GitHub Tools

### All Operations via Plugin
Use `github@claude-plugins-official` plugin for:
- CI/CD status checks
- GitHub Actions management
- GitHub Pages deployment
- Release creation

### Quick Commands
- `/gh-actions` → Use github plugin
- `/gh-pages` → Use github plugin
- `/gh-release` → Use github plugin
- `/ci-status` → Use github plugin

Or use `gh` CLI directly via shell commands.
```

**Result:**
- 59 → 46 files (-22%)
- 0 functionality lost (plugins cover everything)
- Cleaner command directory

---

### Phase 2: R-Development MCP Consolidation (Week 2) ⭐⭐⭐

**Time:** 8-10 hours
**Risk:** Medium
**Impact:** Comprehensive R toolkit + -10 files

**Part A: Rename MCP Server**

```bash
cd ~/projects/dev-tools/mcp-servers

# 1. Rename directory
mv statistical-research r-development

# 2. Update package.json
cd r-development
# Edit package.json:
#   "name": "r-development"
#   "description": "Comprehensive R development toolkit MCP server"

# 3. Update Claude settings
# Edit ~/.claude/settings.json
```

**Edit `~/.claude/settings.json`:**
```json
{
  "mcpServers": {
    "r-development": {  // RENAMED from "statistical-research"
      "command": "bun",
      "args": [
        "run",
        "/Users/dt/projects/dev-tools/mcp-servers/r-development/src/index.ts"
      ],
      "env": {
        "R_LIBS_USER": "~/R/library"
      }
    },
    "project-refactor": { /* unchanged */ },
    "docling": { /* unchanged */ }
  }
}
```

**Part B: Add 6 New Tools**

**Tool 1: r_ecosystem_health**
```typescript
// src/tools/r-console/ecosystem-health.ts
import { z } from "zod";

export const r_ecosystem_health = {
  name: "r_ecosystem_health",
  description: "Comprehensive health check of MediationVerse R package ecosystem",
  inputSchema: z.object({
    packages: z.array(z.string()).default([
      "medfit", "probmed", "rmediation", "medrobust", "medsim", "mediationverse"
    ]),
    check_deps: z.boolean().default(true),
    check_coverage: z.boolean().default(true)
  })
};

// Implementation:
async function r_ecosystem_health_impl(params) {
  const results = {};

  for (const pkg of params.packages) {
    // Run r_check on each package
    const checkResult = await r_check({ package: pkg });

    // Run r_test on each package
    const testResult = await r_test({ package: pkg });

    // Run r_coverage on each package
    const coverageResult = await r_coverage({ package: pkg });

    results[pkg] = {
      check: checkResult,
      tests: testResult,
      coverage: coverageResult
    };
  }

  // Analyze dependency graph
  if (params.check_deps) {
    results.dependencies = await check_dependency_graph(params.packages);
  }

  // Generate health report
  return generate_health_report(results);
}
```

**Tool 2: r_package_check_quick**
```typescript
// src/tools/r-console/package-check.ts (extend existing)
export const r_package_check_quick = {
  name: "r_package_check_quick",
  description: "Quick health check of an R package",
  inputSchema: z.object({
    path: z.string().default("."),
    check_docs: z.boolean().default(true)
  })
};

// Implementation:
async function r_package_check_quick_impl(params) {
  // 1. Read DESCRIPTION
  const desc = await read_description(params.path);

  // 2. Run r_check (existing tool)
  const checkResult = await r_check({ package: params.path });

  // 3. Run r_test (existing tool)
  const testResult = await r_test({ package: params.path });

  // 4. Run r_coverage (existing tool)
  const coverage = await r_coverage({ package: params.path });

  // 5. Check documentation (if requested)
  let docs = null;
  if (params.check_docs) {
    docs = await check_documentation(params.path);
  }

  return {
    package: desc.Package,
    version: desc.Version,
    check: checkResult,
    tests: testResult,
    coverage: coverage,
    documentation: docs,
    overall_status: calculate_status(checkResult, testResult, coverage)
  };
}
```

**Tool 3 & 4: pkgdown Tools**
```typescript
// src/tools/r-console/pkgdown.ts
export const pkgdown_build = {
  name: "pkgdown_build",
  description: "Build R package documentation site with pkgdown",
  inputSchema: z.object({
    path: z.string().default("."),
    preview: z.boolean().default(false),
    dest_dir: z.string().default("docs")
  })
};

export const pkgdown_deploy = {
  name: "pkgdown_deploy",
  description: "Deploy pkgdown site to GitHub Pages",
  inputSchema: z.object({
    path: z.string().default("."),
    branch: z.string().default("gh-pages")
  })
};

// Implementation:
async function pkgdown_build_impl(params) {
  const rCode = `
    pkgdown::build_site(
      pkg = "${params.path}",
      preview = ${params.preview},
      dest_dir = "${params.dest_dir}"
    )
  `;
  return await r_execute({ code: rCode });
}

async function pkgdown_deploy_impl(params) {
  const rCode = `
    pkgdown::deploy_to_branch(
      pkg = "${params.path}",
      branch = "${params.branch}"
    )
  `;
  return await r_execute({ code: rCode });
}
```

**Tool 5: manuscript_section_writer**
```typescript
// src/tools/research/manuscript.ts
export const manuscript_section_writer = {
  name: "manuscript_section_writer",
  description: "Draft manuscript sections for statistical research papers",
  inputSchema: z.object({
    section: z.enum([
      "introduction", "methods", "simulation",
      "application", "results", "discussion"
    ]),
    analysis_file: z.string().optional(),
    references: z.array(z.string()).optional(),
    style: z.enum(["JSS", "JASA", "Biostatistics"]).default("JASA")
  })
};

// Implementation integrates with:
// - R analysis results
// - Zotero citations
// - LaTeX formatting
```

**Tool 6: reviewer_response_generator**
```typescript
// src/tools/research/reviewer-response.ts
export const reviewer_response_generator = {
  name: "reviewer_response_generator",
  description: "Generate point-by-point responses to reviewer comments",
  inputSchema: z.object({
    review_file: z.string(),
    manuscript_file: z.string(),
    response_template: z.enum(["formal", "detailed", "concise"]).default("detailed")
  })
};

// Implementation:
// - Parse reviewer comments
// - Track manuscript changes
// - Generate structured response letter
// - Link to specific manuscript locations
```

**Part C: Migrate Commands**

```bash
# Deprecate 2 code commands (R-specific)
mv ~/.claude/commands/code/ecosystem-health.md ~/.claude/archive/
mv ~/.claude/commands/code/rpkg-check.md ~/.claude/archive/

# Deprecate 8 research commands (all → MCP)
mv ~/.claude/commands/research/cite.md ~/.claude/archive/
mv ~/.claude/commands/research/manuscript.md ~/.claude/archive/
mv ~/.claude/commands/research/revision.md ~/.claude/archive/
mv ~/.claude/commands/research/lit-gap.md ~/.claude/archive/
mv ~/.claude/commands/research/method-scout.md ~/.claude/archive/
mv ~/.claude/commands/research/analysis-plan.md ~/.claude/archive/
mv ~/.claude/commands/research/sim-design.md ~/.claude/archive/
mv ~/.claude/commands/research/hypothesis.md ~/.claude/archive/

# Keep research.md hub, update to show MCP tools
```

**Part D: Update Hubs**

**Edit `~/.claude/commands/code.md`:**
```markdown
## Development Tools

### R Package Development (via r-development MCP)
- `/ecosystem-health` → Use `r_ecosystem_health` tool ✨
- `/rpkg-check` → Use `r_package_check_quick` tool ✨

### Code Quality (via plugins)
- `/debug` → Use code-review plugin
- `/refactor` → Use code-review plugin
- `/docs-check` → Use codebase-documenter plugin
- `/release` → Use feature-dev plugin

### Still Available
- `/demo` - Code demonstration
- `/test-gen` - Generate tests
```

**Edit `~/.claude/commands/research.md`:**
```markdown
## Research Tools (via r-development MCP)

All research capabilities now available through MCP server tools:

### Literature & Planning
- `/cite` → Use `zotero_search`, `zotero_add` tools
- `/lit-gap` → Use `literature_search` tool
- `/method-scout` → Use `method_recommendations` tool
- `/analysis-plan` → Use `create_analysis_plan` tool
- `/sim-design` → Use `design_simulation` tool
- `/hypothesis` → Use `hypothesis_generator` tool

### Manuscript Writing (NEW!)
- `/manuscript` → Use `manuscript_section_writer` tool ✨
- `/revision` → Use `reviewer_response_generator` tool ✨

Access all tools through r-development MCP server.
```

**Edit `~/.claude/commands/site.md`:**
```markdown
## Documentation Sites

### R Package Documentation (via r-development MCP)
- `/build` (for R packages) → Use `pkgdown_build` tool ✨
- `/deploy` (for R packages) → Use `pkgdown_deploy` tool ✨

### MkDocs Documentation (Python/Node/General)
- `/mkdocs:init` - Initialize MkDocs site
- `/mkdocs:preview` - Preview MkDocs site
- `/mkdocs:status` - MkDocs site status

### Site Operations (via infrastructure-maintainer plugin)
- General site building/deployment for non-R projects
```

**Result:**
- 46 → 36 files (-22% additional)
- r-development MCP: 14 → 20 tools (+43%)
- All R operations consolidated

---

### Phase 3: Teaching MCP Server (Weeks 3-4) ⭐⭐⭐

**Time:** 8-12 hours
**Risk:** Medium
**Impact:** Revolutionary teaching workflow, -9 files

**(Same as original plan - see REFACTORING-ACTION-PLAN.md for details)**

**Teaching Toolkit MCP Server:**
- 10 tools (exam, quiz, homework, rubric, feedback, lecture, syllabus, solution, canvas_export, canvas_grade)
- SQLite question bank with:
  - Bloom taxonomy levels
  - Usage tracking
  - Difficulty ratings
  - Topic tagging
- Canvas API integration

**Create Server:**
```bash
cd ~/projects/dev-tools/mcp-servers
mkdir teaching-toolkit && cd teaching-toolkit
bun init
# (Implementation details in original plan)
```

**Migrate Commands:**
```bash
mv ~/.claude/commands/teach/*.md ~/.claude/archive/
# Keep teach.md hub
```

**Result:** 36 → 27 files (-25% additional)

---

### Phase 4: Code Quality Tools (Week 5) ⭐⭐

**Time:** 4-6 hours
**Risk:** Low
**Impact:** Better code review, -4 files

**Delegate to Plugins:**
```bash
# Deprecate commands that plugins handle better
mv ~/.claude/commands/code/debug.md ~/.claude/archive/      # → code-review plugin
mv ~/.claude/commands/code/refactor.md ~/.claude/archive/   # → code-review plugin
mv ~/.claude/commands/code/docs-check.md ~/.claude/archive/ # → codebase-documenter
mv ~/.claude/commands/code/release.md ~/.claude/archive/    # → feature-dev plugin
```

**Keep:**
- `code:demo` (unique workflow)
- `code:test-gen` (no strong plugin overlap)

**Update `code.md` hub** to reference plugins.

**Result:** 27 → 23 files (-15% additional)

---

### Phase 5: Site Automation (Week 6) ⭐

**Time:** 4-6 hours
**Risk:** Low
**Impact:** Cleaner site management, -3 files

**Strategy:**
- R packages → Use `pkgdown_build`, `pkgdown_deploy` from r-development MCP ✨
- MkDocs sites → Keep `/mkdocs:*` commands (DT-specific workflow)
- Generic sites → Delegate to infrastructure-maintainer plugin

**Refactor:**
```bash
# Deprecate generic site commands (delegate to plugin)
mv ~/.claude/commands/site/init.md ~/.claude/archive/
mv ~/.claude/commands/site/check.md ~/.claude/archive/
mv ~/.claude/commands/site/build.md ~/.claude/archive/  # (generic only, not R)
mv ~/.claude/commands/site/deploy.md ~/.claude/archive/ # (generic only, not R)
mv ~/.claude/commands/site/preview.md ~/.claude/archive/

# Keep MkDocs-specific
# site/mkdocs/init.md
# site/mkdocs/preview.md
# site/mkdocs/status.md
```

**Result:** 23 → 20 files (-13% additional)

---

### Phase 6: Workflow Manager MCP (Optional, Weeks 7-8) ⭐

**Time:** 8-10 hours (optional)
**Risk:** High (ADHD workflow is critical)
**Impact:** Session persistence

**(Same as original plan)**

**Result:** 20 files (with optional MCP backend)

---

## 📊 Projected Final State

### Before Refactoring

| Component | Count | Notes |
|-----------|-------|-------|
| Command files | 59 | Scattered, duplicated |
| MCP servers | 3 | statistical-research (misnamed), project-refactor, docling |
| Plugins | 12 | Underutilized |
| Duplication | ~40% | Many commands duplicate plugins |
| R-related commands | 35 | Scattered across code/, research/, site/ |

### After Refactoring

| Component | Count | Change | Notes |
|-----------|-------|--------|-------|
| Command files | 32 | -27 (-46%) | Consolidated, organized |
| MCP servers | 4-5 | +1-2 | r-development (renamed+enhanced), teaching-toolkit (new), workflow-manager (optional) |
| r-development MCP tools | 20 | +6 (+43%) | Comprehensive R toolkit |
| Plugins | 12 | Better utilized | Clear delegation |
| Duplication | <10% | -75% | Plugin delegation |
| R-related commands | 0 | All in MCP | Consolidated |

**MCP Server Breakdown:**

| Server | Tools | Purpose | Status |
|--------|-------|---------|--------|
| **r-development** | 20 | Comprehensive R toolkit | Renamed + 6 new tools ✨ |
| project-refactor | 4 | Safe project refactoring | Unchanged |
| docling | 4 | PDF → Markdown | Unchanged |
| **teaching-toolkit** | 10 | Teaching workflow | NEW ✨ |
| **workflow-manager** | 12 | Session persistence | NEW (optional) ✨ |

---

## 🎯 Success Criteria

### Phase 1 Success ✅
- [ ] 13 files archived (6 meta + 4 github + 3 git)
- [ ] Git/GitHub hubs updated to reference plugins
- [ ] All git workflows still work
- [ ] Command count: 59 → 46

### Phase 2 Success ✅
- [ ] MCP server renamed: statistical-research → r-development
- [ ] 6 new R tools implemented and tested
- [ ] 10 commands archived (2 code + 8 research)
- [ ] code.md, research.md, site.md hubs updated
- [ ] All R workflows still work (test with MediationVerse)
- [ ] Command count: 46 → 36
- [ ] r-development MCP tool count: 14 → 20

### Phase 3 Success ✅
- [ ] teaching-toolkit MCP server created
- [ ] 10 teaching tools implemented
- [ ] SQLite question bank operational
- [ ] Canvas API integration working
- [ ] 9 teach commands archived
- [ ] teach.md hub updated
- [ ] Command count: 36 → 27

### Phases 4-6 Success ✅
- [ ] Code quality commands delegated to plugins
- [ ] Site automation completed
- [ ] Optional workflow-manager MCP (if implemented)
- [ ] Final command count: 20-23 files

---

## ⚠️ Risks & Mitigation - REVISED

### Risk 1: Breaking R Workflows
**Likelihood:** Medium
**Impact:** HIGH (R is core to DT's work)
**Mitigation:**
- Test all 6 new tools with real MediationVerse packages before deprecating commands
- Use medfit package as test case (most mature)
- Keep archived commands for 60 days (not 30) for R tools
- Rollback plan ready

### Risk 2: MCP Server Rename
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Update all references in one session
- Test MCP connection after rename
- Clear documentation of change
- Add README explaining rename

### Risk 3: pkgdown Integration
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Start simple (just wrap pkgdown R functions)
- Test with one package first (medfit)
- Manual pkgdown always works as fallback
- Iterate based on real usage

### Risk 4: Time Investment
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Each phase is independent
- Can pause after any phase
- Quick wins in Phase 1 build confidence

---

## 📅 Recommended Timeline

**Week 1: Phase 1 (Quick Wins)**
- Monday: Archive meta docs
- Tuesday: Deprecate git/github commands
- Wednesday: Update hubs, test
- Thursday: Buffer/catch issues
- Friday: Document outcomes

**Week 2: Phase 2 (R-Development MCP)** ⭐ HIGH VALUE
- Monday: Rename MCP server, update configs
- Tuesday: Implement r_ecosystem_health tool
- Wednesday: Implement r_package_check_quick, pkgdown tools
- Thursday: Implement manuscript, reviewer tools
- Friday: Test all tools, migrate commands, update hubs

**Week 3-4: Phase 3 (Teaching MCP)**
- Week 3: Create teaching-toolkit MCP, implement 5 core tools
- Week 4: Question bank, Canvas integration, migrate commands

**Week 5-7: Phases 4-6 (Optional Refinements)**
- Week 5: Code quality delegation
- Week 6: Site automation
- Week 7: Optional workflow-manager MCP

---

## 🚀 Next Actions

### Immediate (Today)

**Decision Point:**

**Option A: Start Phase 1 (Quick Wins)** - Low risk, builds momentum
- Time: 1-2 hours
- Result: 59 → 46 files
- Validates approach

**Option B: Start Phase 2 (R-Development MCP)** - High value, R consolidation ⭐ RECOMMENDED
- Time: 8-10 hours (can split across multiple sessions)
- Result: Comprehensive R toolkit (20 tools)
- Biggest impact for DT's workflow

**Option C: Do Both** - Phase 1 this session, Phase 2 this week
- Phase 1: 1-2 hours today
- Phase 2: 2-3 sessions this week
- Best momentum

### If Proceeding with Phase 1:

```bash
# Create backup
cp -r ~/.claude/commands ~/.claude/commands-backup-2025-12-19

# Create archive directory
mkdir -p ~/.claude/archive

# Start archiving (see Phase 1 details above)
```

### If Proceeding with Phase 2:

```bash
# Rename MCP server
cd ~/projects/dev-tools/mcp-servers
mv statistical-research r-development

# Start implementing new tools (see Phase 2 details above)
```

---

## 📚 Reference Documents

- **Revised Analysis:** `COMMAND-MCP-REFACTORING-ANALYSIS-REVISED.md` (this document)
- **Original Analysis:** `COMMAND-MCP-REFACTORING-ANALYSIS.md` (for comparison)
- **Session Summary:** `SESSION-SUMMARY-2025-12-19.md`
- **Project Status:** `.STATUS`
- **MCP Server Index:** `~/projects/dev-tools/_MCP_SERVERS.md`
- **Standards:** `STANDARDS-SUMMARY.md`

---

## 🎓 Key Insights

**Insight 1: R-Development is the Core**
59% of commands (35/59) are R-ecosystem related. Consolidating them into one comprehensive MCP server creates:
- Single mental model ("R stuff = r-development MCP")
- Shared R session (performance)
- Publishable toolkit (community value)

**Insight 2: statistical-research Was Misnamed**
The MCP server already has r_check, r_test, r_coverage, r_lint, r_document - it's clearly an R development toolkit, not just research.

**Insight 3: MkDocs vs pkgdown**
R packages use pkgdown (R-based), other projects use MkDocs (Python-based). Need both, delegated differently:
- R packages → pkgdown_build/deploy tools in r-development MCP
- Other projects → MkDocs commands OR infrastructure-maintainer plugin

---

**Generated:** 2025-12-19 (Revised for R-Development MCP consolidation)
**Status:** 🟢 Ready to execute
**Recommended Start:** Phase 2 (R-Development MCP) for maximum value, or Phase 1+2 combo
