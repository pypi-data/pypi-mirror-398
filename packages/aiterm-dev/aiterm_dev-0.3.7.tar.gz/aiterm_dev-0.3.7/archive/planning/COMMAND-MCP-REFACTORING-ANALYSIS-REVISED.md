# Command & MCP Refactoring Analysis - REVISED

**Date:** 2025-12-19 (Revised)
**Based on:** User insight about R MCP consolidation

> **TL;DR:** 59 commands → 32 files (-46%). Key insight: Rename `statistical-research` to `r-development` MCP and consolidate ALL R-related commands into it. This creates a comprehensive R development toolkit.

---

## Executive Summary - REVISED

### Key Insight: R Development MCP Server

The `statistical-research` MCP server is actually an **R Development MCP Server**. It already has:
- R package checking (`check.ts`)
- R testing (`test.ts`)
- R coverage (`coverage.ts`)
- R execution (`execute.ts`)
- R session management (`session.ts`)
- R documentation (`document.ts`)
- R linting (`lint.ts`)

**New Strategy:** Rename to `r-development` and consolidate ALL R-related functionality:
- Research tools (manuscript, citations, literature)
- R package development (ecosystem-health, rpkg-check)
- Documentation site building (MkDocs for R packages)

---

## 1. Current State

### 1.1 Command Inventory

**Total:** 59 command files across 7 domain hubs

| Hub | Files | Primary Focus | R-Related |
|-----|-------|---------------|-----------|
| code/ | 8 | Development tools | ✅ **2 R-specific** (ecosystem-health, rpkg-check) |
| research/ | 8 | Research workflow | ✅ **All R-focused** (statistical research) |
| site/ | 10 | Documentation | ✅ **MkDocs for R packages** |
| git/ | 11 | Git workflows | Partial (R package releases) |
| teach/ | 9 | Teaching | ✅ **Statistical courses** |
| write/ | 5 | Writing | ✅ **Statistical papers** |
| math/ | 4 | Math tools | Complementary |
| workflow/ | 13 | ADHD workflow | Generic |
| github/ | 4 | GitHub | Partial (R package publishing) |
| help/ | 9 | Documentation | Generic |

**R-Related Count:** ~35/59 files (59%) are R-ecosystem related!

---

### 1.2 Current MCP Servers

#### statistical-research MCP
**Current Name:** `statistical-research`
**Better Name:** `r-development` (comprehensive R toolkit)
**Location:** `~/projects/dev-tools/mcp-servers/statistical-research/`
**Runtime:** Bun (TypeScript)

**Current Tools (14):**

| Category | Tools | Description |
|----------|-------|-------------|
| **R Infrastructure** | `r_execute`, `r_inspect`, `r_session_info` | Core R execution |
| **R Package Dev** | `r_check`, `r_test`, `r_coverage`, `r_lint`, `r_document` | Package tools ✅ |
| **Research** | `literature_search`, `method_recommendations` | Literature discovery |
| **Citations** | `zotero_search`, `zotero_add`, `zotero_collections` | Citation management |
| **Statistics** | `create_analysis_plan`, `design_simulation`, `hypothesis_generator` | Statistical planning |
| **Advanced** | `power_calculation`, `bayesian_prior_selection`, `causal_dag_analysis` | Advanced stats |

**Proposed Additions (+6 tools):**

| New Tool | Purpose | Replaces Command |
|----------|---------|------------------|
| `r_ecosystem_health` | Check MediationVerse ecosystem | code:ecosystem-health ✅ |
| `r_package_check_quick` | Quick R package health | code:rpkg-check ✅ |
| `manuscript_section_writer` | Write statistical paper sections | research:manuscript |
| `reviewer_response_generator` | Respond to reviewers | research:revision |
| `pkgdown_build` | Build R package website | site:build (partial) |
| `pkgdown_deploy` | Deploy to GitHub Pages | site:deploy (partial) |

---

## 2. Revised Refactoring Strategy

### 2.1 Rename MCP Server

**Action:** Rename `statistical-research` → `r-development`

**Rationale:**
- More accurately reflects comprehensive R toolkit
- Covers: packages, research, documentation, teaching
- Clearer for external users (not just research)
- Aligns with user's R-heavy workflow

**Migration:**
```bash
cd ~/projects/dev-tools/mcp-servers
mv statistical-research r-development
cd r-development
# Update package.json name
# Update ~/.claude/settings.json mcpServers key
```

---

### 2.2 Consolidate R-Related Commands

#### Category 1: R Package Development (2 commands → MCP)

**Commands to Migrate:**
- `code:ecosystem-health` → `r_ecosystem_health` tool
- `code:rpkg-check` → `r_package_check_quick` tool

**Implementation:**
```typescript
// src/tools/r-console/ecosystem-health.ts
export const r_ecosystem_health = {
  name: "r_ecosystem_health",
  description: "Check health of MediationVerse R package ecosystem",
  inputSchema: {
    type: "object",
    properties: {
      packages: {
        type: "array",
        items: { type: "string" },
        default: ["medfit", "probmed", "rmediation", "medrobust", "medsim", "mediationverse"]
      }
    }
  }
}

// Implementation:
// - Run r_check on each package
// - Aggregate test coverage
// - Check dependency graph
// - Verify inter-package consistency
// - Output comprehensive health report
```

```typescript
// src/tools/r-console/package-check.ts (extend existing)
export const r_package_check_quick = {
  name: "r_package_check_quick",
  description: "Quick health check of an R package",
  inputSchema: {
    type: "object",
    properties: {
      path: { type: "string", description: "Path to R package" }
    }
  }
}

// Implementation:
// - Read DESCRIPTION
// - Run r_check (existing tool)
// - Run r_test (existing tool)
// - Run r_coverage (existing tool)
// - Check documentation completeness
// - Output summary report
```

---

#### Category 2: Research Workflow (8 commands → MCP)

**Already in MCP (6 tools):**
- `research:cite` → `zotero_search`, `zotero_add`
- `research:lit-gap` → `literature_search`
- `research:method-scout` → `method_recommendations`
- `research:analysis-plan` → `create_analysis_plan`
- `research:sim-design` → `design_simulation`
- `research:hypothesis` → `hypothesis_generator`

**Need to Add (2 tools):**
- `research:manuscript` → `manuscript_section_writer` (NEW)
- `research:revision` → `reviewer_response_generator` (NEW)

**Action:** Deprecate all 8 research commands, update hub

---

#### Category 3: Documentation Sites (Partial - R packages)

**R Package Documentation Commands:**
- `site:build` → Use `pkgdown::build_site()` (via new `pkgdown_build` tool)
- `site:deploy` → Use `pkgdown::deploy_to_branch()` (via new `pkgdown_deploy` tool)

**Keep for MkDocs (non-R projects):**
- `site:init`, `site:check`, `site:preview`
- `site/mkdocs/*` (MkDocs-specific)

**New MCP Tools:**
```typescript
// src/tools/r-console/pkgdown.ts
export const pkgdown_build = {
  name: "pkgdown_build",
  description: "Build R package documentation site with pkgdown",
  inputSchema: {
    type: "object",
    properties: {
      path: { type: "string" },
      preview: { type: "boolean", default: false }
    }
  }
}

export const pkgdown_deploy = {
  name: "pkgdown_deploy",
  description: "Deploy pkgdown site to GitHub Pages",
  inputSchema: {
    type: "object",
    properties: {
      path: { type: "string" },
      branch: { type: "string", default: "gh-pages" }
    }
  }
}
```

---

#### Category 4: Teaching (9 commands → teaching-toolkit MCP)

**Keep separate MCP server for teaching** (not R-specific, but stats courses):
- Canvas integration
- Question banks
- Exam/quiz generation
- Rubrics

**Rationale:** Teaching toolkit is domain-specific but not R-dev specific.

---

## 3. Revised Disposition Matrix

### Commands by Action

| Action | Count | Commands |
|--------|-------|----------|
| **Migrate to R-Development MCP** | **10** | ecosystem-health, rpkg-check, cite, manuscript, revision, lit-gap, method-scout, analysis-plan, sim-design, hypothesis |
| **Migrate to Teaching MCP** | **9** | All teach/* commands |
| **Deprecate (use plugins)** | **11** | Git/GitHub commands |
| **Refactor (delegate to plugins)** | **5** | Code quality commands |
| **Archive** | **6** | Meta planning documents |
| **Keep as-is** | **18** | Hubs, workflow, math, write, help |

**Total Reduction:** 59 → 32 files (-46%)

---

### R-Development MCP Final Tool List (20 tools)

| Category | Tools (20 total) |
|----------|------------------|
| **R Infrastructure (3)** | r_execute, r_inspect, r_session_info |
| **R Package Dev (5)** | r_check, r_test, r_coverage, r_lint, r_document |
| **R Package Health (2)** | r_ecosystem_health ✨ NEW, r_package_check_quick ✨ NEW |
| **R Documentation (2)** | pkgdown_build ✨ NEW, pkgdown_deploy ✨ NEW |
| **Research (2)** | manuscript_section_writer ✨ NEW, reviewer_response_generator ✨ NEW |
| **Literature (2)** | literature_search, method_recommendations |
| **Citations (3)** | zotero_search, zotero_add, zotero_collections |
| **Statistics (3)** | create_analysis_plan, design_simulation, hypothesis_generator |

**Total:** 20 tools (14 existing + 6 new)

---

## 4. Revised Implementation Plan

### Phase 1: Quick Wins (Week 1) ⭐⭐⭐

**Time:** 1-2 hours
**Risk:** Very Low
**Impact:** -13 files

**Actions:**
```bash
# 1. Archive meta documents (6 files)
mkdir -p ~/.claude/archive
mv ~/.claude/commands/{BACKGROUND-AGENT,PHASE1,REORGANIZATION,UNIVERSAL}*.md ~/.claude/archive/

# 2. Deprecate github commands (4 files) → use github plugin
mv ~/.claude/commands/github/*.md ~/.claude/archive/

# 3. Deprecate git plugin duplicates (3 files)
mv ~/.claude/commands/git/{commit,pr-create,pr-review}.md ~/.claude/archive/

# 4. Update git.md and github.md hubs to reference plugins
```

**Result:** 59 → 46 files (-22%)

---

### Phase 2: Rename & Enhance R-Development MCP (Week 2) ⭐⭐⭐

**Time:** 6-8 hours
**Risk:** Medium
**Impact:** Better R toolkit + -10 files

**Actions:**
```bash
cd ~/projects/dev-tools/mcp-servers

# 1. Rename server
mv statistical-research r-development

# 2. Update package.json
cd r-development
# Edit package.json: "name": "r-development"

# 3. Update Claude settings
# Edit ~/.claude/settings.json:
#   "mcpServers": {
#     "r-development": { ... }  # was "statistical-research"
#   }
```

**Add 6 New Tools:**
1. `r_ecosystem_health` (MediationVerse health check)
2. `r_package_check_quick` (quick R package check)
3. `manuscript_section_writer` (write paper sections)
4. `reviewer_response_generator` (respond to reviewers)
5. `pkgdown_build` (build R package site)
6. `pkgdown_deploy` (deploy to GitHub Pages)

**Migrate Commands:**
```bash
# Deprecate 2 code commands
mv ~/.claude/commands/code/{ecosystem-health,rpkg-check}.md ~/.claude/archive/

# Deprecate 8 research commands
mv ~/.claude/commands/research/*.md ~/.claude/archive/
# (Keep research.md hub)

# Update hubs
# Edit code.md, research.md, site.md to reference MCP tools
```

**Result:** 46 → 36 files (-22% additional)

---

### Phase 3: Teaching MCP Server (Weeks 3-4) ⭐⭐⭐

**Same as original plan** - teaching-toolkit MCP with:
- 10 tools (exam, quiz, homework, rubric, etc.)
- SQLite question bank
- Canvas API integration
- Bloom taxonomy tracking

**Result:** 36 → 27 files (-25% additional)

---

### Phase 4: Code Quality Delegation (Week 5) ⭐⭐

**Delegate to plugins:**
- `code:debug` → code-review plugin
- `code:refactor` → code-review plugin
- `code:docs-check` → codebase-documenter plugin
- `code:release` → feature-dev plugin
- `code:test-gen` → Keep (no strong plugin overlap)

**Keep R-specific:**
- `code:demo` → Keep

**Result:** 27 → 23 files (-15% additional)

---

### Phase 5: Site Automation (Week 6) ⭐

**For non-R projects (Python, Node, general):**
- Keep `site/mkdocs/*` commands (MkDocs-specific)
- Delegate generic site commands to infrastructure-maintainer plugin

**For R projects:**
- Use `pkgdown_build` and `pkgdown_deploy` tools from R-development MCP

**Result:** 23 → 20 files (-13% additional)

---

### Phase 6: Workflow Manager MCP (Optional, Weeks 7-8) ⭐

**Same as original plan** - optional workflow-manager MCP for session persistence

**Result:** 20 files (with optional MCP backend enhancement)

---

## 5. Final Command Count (Revised)

### Before Refactoring
- 59 command files
- 3 MCP servers (statistical-research, project-refactor, docling)
- 12 plugins

### After Refactoring

| Component | Before | After | Change |
|-----------|--------|-------|--------|
| Command files | 59 | 32 | -27 (-46%) |
| MCP servers | 3 | 4-5 | +1-2 |
| R-Development MCP tools | 14 | 20 | +6 |

**MCP Servers (Final):**
1. ✨ **r-development** (renamed, 20 tools) - Comprehensive R toolkit
2. **project-refactor** (unchanged, 4 tools)
3. **docling** (unchanged, 4 tools)
4. ✨ **teaching-toolkit** (NEW, 10 tools)
5. **workflow-manager** (NEW, optional, 12 tools)

---

## 6. R-Development MCP Architecture

### Proposed Directory Structure

```
r-development/  (renamed from statistical-research)
├── src/
│   ├── index.ts
│   ├── tools/
│   │   ├── r-console/
│   │   │   ├── execute.ts          [Existing]
│   │   │   ├── inspect.ts          [Existing]
│   │   │   ├── session.ts          [Existing]
│   │   │   ├── check.ts            [Existing]
│   │   │   ├── test.ts             [Existing]
│   │   │   ├── coverage.ts         [Existing]
│   │   │   ├── lint.ts             [Existing]
│   │   │   ├── document.ts         [Existing]
│   │   │   ├── ecosystem-health.ts [NEW] ✨
│   │   │   ├── package-check.ts    [NEW] ✨
│   │   │   └── pkgdown.ts          [NEW] ✨
│   │   ├── research/
│   │   │   ├── analysis-plan.ts    [Existing]
│   │   │   ├── simulation.ts       [Existing]
│   │   │   ├── hypothesis.ts       [Existing]
│   │   │   ├── manuscript.ts       [NEW] ✨
│   │   │   └── reviewer-response.ts [NEW] ✨
│   │   ├── literature/
│   │   │   ├── search.ts           [Existing]
│   │   │   └── methods.ts          [Existing]
│   │   └── citations/
│   │       ├── zotero.ts           [Existing]
│   │       └── bibtex.ts           [Existing]
│   ├── skills/
│   │   ├── r-package-dev.ts        [17 A-grade skills]
│   │   └── statistical-research.ts [More skills]
│   └── utils/
│       └── r-session-manager.ts
├── package.json
└── README.md
```

---

## 7. MCP Server Capabilities Comparison

| Capability | statistical-research (old) | r-development (new) |
|------------|---------------------------|---------------------|
| R execution | ✅ | ✅ |
| R package checking | ✅ | ✅ Enhanced |
| R package health | ❌ | ✅ NEW (ecosystem) |
| R documentation sites | ❌ | ✅ NEW (pkgdown) |
| Research workflows | ✅ | ✅ Enhanced |
| Manuscript writing | ❌ | ✅ NEW |
| Reviewer responses | ❌ | ✅ NEW |
| Literature search | ✅ | ✅ |
| Zotero integration | ✅ | ✅ |
| Statistical planning | ✅ | ✅ |

**Summary:** 14 tools → 20 tools (+43% functionality)

---

## 8. Benefits of R-Development MCP Consolidation

### Technical Benefits
1. **Single R Toolkit** - All R-related operations in one place
2. **Shared R Session** - Tools can share R environment state
3. **Better Testing** - Unified test suite for R functionality
4. **Easier Maintenance** - One MCP to maintain vs scattered commands

### User Experience Benefits
1. **Clear Mental Model** - "R stuff = r-development MCP"
2. **Discovery** - Browse all R tools in one MCP server
3. **Consistency** - Same patterns across all R operations
4. **Performance** - Persistent R session (no startup overhead)

### Ecosystem Benefits
1. **Publishable** - Complete R toolkit for community
2. **Reusable** - Other R developers can use it
3. **Extensible** - Easy to add new R tools
4. **Documentation** - Single comprehensive guide

---

## 9. Migration Checklist

### Week 1: Quick Wins
- [ ] Backup ~/.claude/commands/
- [ ] Archive 6 meta documents
- [ ] Deprecate 4 github commands
- [ ] Deprecate 3 git commands
- [ ] Update git.md and github.md hubs
- [ ] Test git workflows still work
- [ ] **Count:** 59 → 46 files

### Week 2: R-Development MCP
- [ ] Rename statistical-research → r-development
- [ ] Update package.json
- [ ] Update ~/.claude/settings.json
- [ ] Implement r_ecosystem_health tool
- [ ] Implement r_package_check_quick tool
- [ ] Implement manuscript_section_writer tool
- [ ] Implement reviewer_response_generator tool
- [ ] Implement pkgdown_build tool
- [ ] Implement pkgdown_deploy tool
- [ ] Test all 6 new tools with real R projects
- [ ] Deprecate 2 code commands (ecosystem-health, rpkg-check)
- [ ] Deprecate 8 research commands
- [ ] Update code.md, research.md, site.md hubs
- [ ] **Count:** 46 → 36 files

### Week 3-4: Teaching MCP
- [ ] Create teaching-toolkit MCP server
- [ ] Implement 10 teaching tools
- [ ] Set up SQLite question bank
- [ ] Canvas API integration
- [ ] Deprecate 9 teach commands
- [ ] Update teach.md hub
- [ ] **Count:** 36 → 27 files

### Week 5: Code Quality
- [ ] Refactor code:debug → code-review plugin
- [ ] Refactor code:refactor → code-review plugin
- [ ] Refactor code:docs-check → codebase-documenter
- [ ] Deprecate code:release → feature-dev plugin
- [ ] Update code.md hub
- [ ] **Count:** 27 → 23 files

### Week 6: Site Automation
- [ ] Refactor generic site commands → infrastructure-maintainer
- [ ] Keep site/mkdocs/* (MkDocs-specific)
- [ ] Test pkgdown tools for R packages
- [ ] Update site.md hub
- [ ] **Count:** 23 → 20 files

---

## 10. Risk Analysis

### Risk 1: Breaking R Workflows
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Test all 6 new tools with real MediationVerse packages
- Keep archived commands for 30 days
- Phased rollout (test with medfit first, then others)

### Risk 2: MCP Server Rename Confusion
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Clear documentation of rename
- Update all references simultaneously
- Add deprecation notice in old location

### Risk 3: pkgdown Integration Complexity
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Start simple (just wrap pkgdown::build_site())
- Iterate based on usage
- Keep manual pkgdown as fallback

---

## 11. Next Steps

### Immediate (This Session)
1. **Review this revised analysis** with user
2. **Get approval** for R-Development MCP consolidation approach
3. **Decide:** Start with Phase 1 (quick wins) or Phase 2 (R-Development MCP)?

### This Week
**Option A: Phase 1 (Quick Wins)**
- Time: 1-2 hours
- Risk: Very Low
- Immediate cleanup

**Option B: Phase 2 (R-Development MCP)**
- Time: 6-8 hours
- Risk: Medium
- High value (consolidates R ecosystem)

### Next 2 Weeks
- Complete Phase 2 (if not done)
- Plan Phase 3 (Teaching MCP)

---

## 12. Recommendations Summary

**Top Priority:**
1. ✨ **Rename statistical-research → r-development** (better name, clearer purpose)
2. ✨ **Add 6 R-focused tools** (ecosystem-health, pkgdown, manuscript, reviewer)
3. ❌ **Migrate 10 R-related commands to MCP** (consolidation)

**High Value:**
- R-Development MCP becomes comprehensive R toolkit (20 tools)
- Publishable to community (npm package)
- Single mental model for all R operations

**Keep Separate:**
- Teaching MCP (stats courses, but not R-dev specific)
- Workflow MCP (generic ADHD workflow)
- Site MkDocs commands (non-R documentation)

---

**Generated:** 2025-12-19 (Revised based on R consolidation insight)
**Status:** 🟢 Ready for review and approval
**Recommended Start:** Phase 2 (R-Development MCP) - highest value consolidation
