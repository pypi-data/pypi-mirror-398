# RForge MCP Server - Design Document

> **STATUS: IMPLEMENTED**
> **Date:** 2025-12-27
> **Version:** v0.1.0 (Released)
> This design document has been implemented in `rforge-mcp`.
> See `~/projects/dev-tools/mcp-servers/rforge/` for the codebase.

**Name:** `rforge` (R Package Forge - Build, Test, Orchestrate)
**Alternative names considered:** r-dev, r-development, statistical-research
**Status:** Design Phase
**Date:** 2025-12-20

---

## 🎯 Mission Statement

**RForge** is an MCP server that orchestrates the entire R package development lifecycle, with special focus on managing multi-package ecosystems like MediationVerse.

**Core Value:** From package creation → testing → documentation → CRAN submission → ecosystem coordination - all automated.

---

## 📊 Your MediationVerse Ecosystem (Context)

```
mediationverse (umbrella) ← Meta-package
    │
    ├── RMediation (core CI)
    ├── mediate (main analysis)
    ├── sensitivity (sensitivity analysis)
    ├── causal-paths (path analysis)
    └── pmed (new package)
         │
         └── Shared Utils (common functions)
```

**Current Pain Points:**
1. Manual cascade management (RMediation change → must update 4+ packages)
2. Documentation drift across packages
3. CRAN submission sequencing complexity
4. Version compatibility matrix tracking
5. Cross-package testing dependencies

---

## 🏗️ RForge Architecture

### Three-Tier Design:

```
┌──────────────────────────────────────────────────────────────┐
│ TIER 1: Single Package Tools (Foundation)                    │
│ - Create, build, test, document individual packages          │
└──────────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────────┐
│ TIER 2: Ecosystem Orchestration (Your Special Need!)         │
│ - Dependency graphing, cascade management, sync              │
└──────────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────────┐
│ TIER 3: Research Workflow (Manuscript Integration)           │
│ - Analysis → Results → Manuscript → Submission               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tool Catalog (45 tools across 3 tiers)

### TIER 1: Single Package Tools (15 tools)

#### Package Lifecycle (`rforge:pkg:*`)

**1. `rforge:pkg:create`** - Scaffold new R package
```typescript
{
  name: string,              // package name
  path: string,              // where to create
  template: "basic" | "tidy" | "mediation",  // template type
  with_vignette: boolean,
  with_tests: boolean,
  license: "MIT" | "GPL-3" | "Apache-2"
}
```

**2. `rforge:pkg:check`** - R CMD check
```typescript
{
  package: string,
  args: string[],           // additional args
  env_vars: object,         // e.g., NOT_CRAN=true
  error_on: "error" | "warning" | "note"
}
```

**3. `rforge:pkg:test`** - Run testthat tests
```typescript
{
  package: string,
  reporter: "progress" | "minimal" | "junit",
  filter: string,           // test name pattern
  stop_on_failure: boolean
}
```

**4. `rforge:pkg:coverage`** - Code coverage
```typescript
{
  package: string,
  type: "package" | "all",
  quiet: boolean,
  line_exclusions: string[]
}
```

**5. `rforge:pkg:build`** - Build package tarball
```typescript
{
  package: string,
  binary: boolean,
  vignettes: boolean,
  manual: boolean
}
```

**6. `rforge:pkg:install`** - Install package locally
```typescript
{
  package: string,
  dependencies: boolean,
  upgrade: "never" | "default" | "always",
  force: boolean
}
```

#### Documentation (`rforge:docs:*`)

**7. `rforge:docs:roxygen`** - Update documentation from code
```typescript
{
  package: string,
  roclets: string[],        // c("rd", "namespace", "vignette")
  load_code: "source" | "installed"
}
```

**8. `rforge:docs:pkgdown-build`** - Build pkgdown site
```typescript
{
  package: string,
  preview: boolean,
  devel: boolean,           // use development version
  new_process: boolean
}
```

**9. `rforge:docs:pkgdown-deploy`** - Deploy to GitHub Pages
```typescript
{
  package: string,
  branch: "gh-pages" | "main",
  commit_message: string,
  clean: boolean
}
```

**10. `rforge:docs:vignette-create`** - Create new vignette
```typescript
{
  package: string,
  name: string,
  title: string,
  engine: "rmarkdown" | "quarto"
}
```

#### Code Quality (`rforge:quality:*`)

**11. `rforge:quality:lint`** - Check code style (lintr)
```typescript
{
  package: string,
  linters: string[],
  cache: boolean
}
```

**12. `rforge:quality:style`** - Auto-format code (styler)
```typescript
{
  package: string,
  scope: "spaces" | "indentation" | "line_breaks" | "tokens",
  strict: boolean,
  dry: boolean              // preview only
}
```

**13. `rforge:quality:spell`** - Spell check
```typescript
{
  package: string,
  vignettes: boolean,
  lang: "en-US" | "en-GB",
  ignore: string[]
}
```

#### CRAN (`rforge:cran:*`)

**14. `rforge:cran:submit`** - Submit to CRAN
```typescript
{
  package: string,
  comments: string,
  check_results: "auto" | "manual",
  email: string
}
```

**15. `rforge:cran:status`** - Check CRAN status
```typescript
{
  packages: string[],
  show_checks: boolean,
  show_incoming: boolean
}
```

---

### TIER 2: Ecosystem Orchestration (20 tools) ⭐⭐⭐

#### Dependency Management (`rforge:deps:*`)

**16. `rforge:deps:scan`** ⭐⭐⭐ - Scan ecosystem and build dependency graph
```typescript
{
  packages: string[] | "all",
  root: string,             // root directory containing packages
  include_suggests: boolean,
  include_external: boolean,
  output_format: "json" | "mermaid" | "graphviz"
}

// Returns:
{
  graph: {
    nodes: Package[],
    edges: Dependency[]
  },
  versions: Map<package, version>,
  conflicts: VersionConflict[],
  health_score: number,     // 0-100
  warnings: string[]
}
```

**17. `rforge:deps:impact`** ⭐⭐⭐ - Calculate impact radius
```typescript
{
  package: string,
  change_type: "patch" | "minor" | "major" | "breaking",
  affected_exports: string[],  // which functions changed
  recursive: boolean
}

// Returns:
{
  direct_dependents: string[],
  transitive_dependents: string[],
  affected_vignettes: Array<{package: string, file: string}>,
  affected_tests: Array<{package: string, file: string}>,
  estimated_work_hours: number,
  cascade_sequence: CascadeStep[]
}
```

**18. `rforge:deps:compatibility`** - Check version compatibility
```typescript
{
  scenario: "current" | "proposed",
  proposed_versions: Map<package, version>,  // optional
  check_r_version: boolean,
  check_system_deps: boolean
}
```

**19. `rforge:deps:update`** - Update dependency versions
```typescript
{
  package: string,
  dependencies: Map<package, version>,
  update_description: boolean,
  update_namespace: boolean,
  dry_run: boolean
}
```

#### Cascade Management (`rforge:cascade:*`)

**20. `rforge:cascade:plan`** ⭐⭐⭐ - Generate cascade plan
```typescript
{
  source_package: string,
  change_description: string,
  change_type: "bugfix" | "feature" | "breaking" | "deprecation",
  target_version: string,
  auto_version_bump: boolean
}

// Returns:
{
  sequence: Array<{
    package: string,
    current_version: string,
    new_version: string,
    action: "update_dep" | "retest" | "rebuild_docs" | "release",
    estimated_hours: number,
    dependencies: string[]    // what must complete first
  }>,
  critical_path: string[],
  total_estimated_days: number,
  risks: Risk[]
}
```

**21. `rforge:cascade:execute`** - Execute cascade plan
```typescript
{
  plan_id: string,
  dry_run: boolean,
  auto_commit: boolean,
  create_prs: boolean,
  pr_template: string,
  notify: boolean
}
```

**22. `rforge:cascade:track`** - Track cascade progress
```typescript
{
  plan_id: string,
  show_completed: boolean,
  show_blocked: boolean
}
```

#### Version Management (`rforge:version:*`)

**23. `rforge:version:bump`** - Bump version across packages
```typescript
{
  packages: string[],
  bump_type: "patch" | "minor" | "major" | "dev",
  sync_news: boolean,
  sync_description: boolean,
  git_tag: boolean
}
```

**24. `rforge:version:sync`** - Synchronize version references
```typescript
{
  packages: string[],
  update_cross_refs: boolean,
  update_badges: boolean,
  update_readme: boolean
}
```

**25. `rforge:version:matrix`** - Generate compatibility matrix
```typescript
{
  packages: string[],
  include_r_versions: boolean,
  include_system_deps: boolean,
  format: "markdown" | "html" | "latex"
}
```

#### Documentation Orchestration (`rforge:docs-eco:*`)

**26. `rforge:docs-eco:unified-site`** ⭐⭐ - Build unified pkgdown site
```typescript
{
  packages: string[],
  output_dir: string,
  shared_navbar: boolean,
  cross_package_search: boolean,
  dependency_diagrams: boolean,
  compatibility_matrix: boolean
}
```

**27. `rforge:docs-eco:sync-news`** - Synchronize NEWS.md
```typescript
{
  source_package: string,
  version: string,
  changes: ChangeEntry[],
  cross_reference_in: string[],  // packages to reference this
  auto_commit: boolean
}
```

**28. `rforge:docs-eco:check-drift`** ⭐⭐ - Detect documentation drift
```typescript
{
  packages: string[],
  check_vignettes: boolean,
  check_examples: boolean,
  check_readme: boolean,
  check_badges: boolean
}

// Returns:
{
  drift_items: Array<{
    package: string,
    file: string,
    issue: string,
    severity: "error" | "warning" | "info",
    auto_fixable: boolean
  }>,
  summary: {
    total_issues: number,
    auto_fixable: number,
    manual_review: number
  }
}
```

**29. `rforge:docs-eco:fix-drift`** - Auto-fix documentation drift
```typescript
{
  drift_report_id: string,
  auto_fix_badges: boolean,
  auto_fix_versions: boolean,
  auto_fix_links: boolean,
  dry_run: boolean
}
```

#### Release Coordination (`rforge:release:*`)

**30. `rforge:release:plan`** ⭐⭐⭐ - Plan multi-package release
```typescript
{
  packages: string[] | "all",
  release_type: "patch" | "minor" | "major",
  target: "github" | "cran" | "both",
  target_date: string,
  respect_dependencies: boolean
}

// Returns:
{
  release_sequence: ReleaseStep[],
  cran_submission_order: Array<{
    day: number,
    package: string,
    action: "submit" | "expect_acceptance" | "monitor"
  }>,
  pre_release_checklist: ChecklistItem[],
  post_release_tasks: Task[],
  risks: Risk[],
  estimated_timeline_days: number
}
```

**31. `rforge:release:cran-sequence`** - Calculate CRAN submission order
```typescript
{
  packages: string[],
  buffer_days: number,      // days between submissions
  check_reverse_deps: boolean
}
```

**32. `rforge:release:announce`** - Generate release announcement
```typescript
{
  packages: string[],
  version: string,
  highlights: string[],
  channels: ("blog" | "twitter" | "mastodon" | "r-bloggers")[]
}
```

#### Health Monitoring (`rforge:health:*`)

**33. `rforge:health:ecosystem`** ⭐⭐⭐ - Full ecosystem health check
```typescript
{
  packages: string[] | "all",
  check_tests: boolean,
  check_coverage: boolean,
  check_cran_status: boolean,
  check_github_actions: boolean,
  check_reverse_deps: boolean
}

// Returns:
{
  overall_score: number,    // 0-100
  package_scores: Map<package, {
    tests: "passing" | "failing" | "unknown",
    coverage: number,
    cran_status: "ok" | "warning" | "error" | "archived",
    ci_status: "passing" | "failing" | "unknown",
    issues_open: number,
    last_commit: Date,
    health_grade: "A" | "B" | "C" | "D" | "F"
  }>,
  warnings: Warning[],
  recommendations: Recommendation[]
}
```

**34. `rforge:health:ci-status`** - Check CI/CD status
```typescript
{
  packages: string[],
  platforms: ("ubuntu" | "macos" | "windows" | "all")[],
  show_logs: boolean
}
```

**35. `rforge:health:reverse-deps`** - Check reverse dependencies
```typescript
{
  package: string,
  check_cran: boolean,
  check_bioconductor: boolean,
  run_checks: boolean
}
```

---

### TIER 3: Research Workflow (10 tools)

#### Analysis Integration (`rforge:analysis:*`)

**36. `rforge:analysis:run`** - Execute R analysis
```typescript
{
  script: string,
  packages_load: string[],
  output_format: "text" | "html" | "rmd",
  save_workspace: boolean
}
```

**37. `rforge:analysis:notebook`** - Create analysis notebook
```typescript
{
  title: string,
  packages: string[],
  template: "basic" | "mediation" | "simulation",
  output: "html" | "pdf" | "both"
}
```

**38. `rforge:analysis:reproduce`** - Reproduce analysis
```typescript
{
  notebook: string,
  check_dependencies: boolean,
  match_r_version: boolean,
  match_package_versions: boolean
}
```

#### Manuscript Integration (`rforge:manuscript:*`)

**39. `rforge:manuscript:results`** - Extract results for manuscript
```typescript
{
  analysis_file: string,
  format: "latex" | "markdown" | "docx",
  include_tables: boolean,
  include_figures: boolean,
  significant_only: boolean
}
```

**40. `rforge:manuscript:write`** - Draft manuscript section
```typescript
{
  section: "introduction" | "methods" | "results" | "discussion",
  analysis_file: string,
  references: string[],      // Zotero keys
  journal_style: "JASA" | "Biostatistics" | "Psychological Methods"
}
```

**41. `rforge:manuscript:cite`** - Manage citations
```typescript
{
  packages: string[],
  format: "bibtex" | "natbib" | "biblatex",
  include_r_citation: boolean,
  output_file: string
}
```

#### Simulation Studies (`rforge:sim:*`)

**42. `rforge:sim:design`** - Design simulation study
```typescript
{
  estimands: string[],
  sample_sizes: number[],
  effect_sizes: number[],
  n_replications: number,
  parallel: boolean
}
```

**43. `rforge:sim:run`** - Execute simulation
```typescript
{
  design_file: string,
  cores: number,
  progress: boolean,
  save_seed: boolean
}
```

**44. `rforge:sim:analyze`** - Analyze simulation results
```typescript
{
  results_file: string,
  metrics: ("bias" | "rmse" | "coverage" | "power")[],
  create_plots: boolean,
  output_format: "html" | "pdf"
}
```

#### Reproducibility (`rforge:repro:*`)

**45. `rforge:repro:lock`** - Create lockfile for reproducibility
```typescript
{
  packages: string[],
  include_r_version: boolean,
  include_system_info: boolean,
  output: string
}
```

---

## 🎨 Naming Convention

**Pattern:** `rforge:<category>:<action>`

**Categories:**
- `pkg` - Single package operations
- `docs` - Single package documentation
- `quality` - Code quality tools
- `cran` - CRAN operations
- `deps` - Dependency management
- `cascade` - Cascade management
- `version` - Version management
- `docs-eco` - Ecosystem documentation
- `release` - Release coordination
- `health` - Health monitoring
- `analysis` - R analysis execution
- `manuscript` - Manuscript integration
- `sim` - Simulation studies
- `repro` - Reproducibility

---

## 🔄 Example Workflows

### Workflow 1: Update RMediation Algorithm

**User:** "I'm updating `ci_mediation()` in RMediation to use a new bootstrap algorithm"

**RForge Response:**
```
rforge:deps:impact({
  package: "RMediation",
  change_type: "minor",
  affected_exports: ["ci_mediation"]
})

┌─ IMPACT ANALYSIS ──────────────────────────────────────────┐
│ Change: RMediation::ci_mediation() - MINOR                 │
│                                                             │
│ Direct Dependents: 3 packages                              │
│   • mediate (uses in mediate_ci())                         │
│   • sensitivity (uses in sens_ci())                        │
│   • pmed (uses in pmed_ci())                               │
│                                                             │
│ Affected Files:                                            │
│   • mediate/tests/testthat/test-ci.R (expects will change) │
│   • sensitivity/vignettes/intro.Rmd (output will differ)   │
│   • RMediation/vignettes/algorithms.Rmd (needs update)     │
│                                                             │
│ Estimated Work: 4-6 hours                                  │
│                                                             │
│ Cascade Plan Available: rforge:cascade:plan               │
└────────────────────────────────────────────────────────────┘

Generate cascade plan? (y/n)
```

**If yes:**
```
rforge:cascade:plan({
  source_package: "RMediation",
  change_description: "New bootstrap algorithm for ci_mediation()",
  change_type: "feature",
  target_version: "2.1.0"
})

┌─ CASCADE PLAN ─────────────────────────────────────────────┐
│                                                             │
│ Step 1: RMediation 2.0.1 → 2.1.0 (Day 1)                  │
│   Action: Implement change + update tests + update vignette│
│   Time: 4 hours                                            │
│                                                             │
│ Step 2: mediate 1.5.0 → 1.5.1 (Day 2)                     │
│   Action: Update dependency, adjust tests                  │
│   Time: 1 hour                                             │
│                                                             │
│ Step 3: sensitivity 0.8.0 → 0.8.1 (Day 2)                 │
│   Action: Update dependency, update vignette example       │
│   Time: 1.5 hours                                          │
│                                                             │
│ Step 4: pmed 0.1.0 → 0.1.1 (Day 2)                        │
│   Action: Update dependency, retest                        │
│   Time: 0.5 hours                                          │
│                                                             │
│ Step 5: mediationverse 1.1.0 → 1.2.0 (Day 3)              │
│   Action: Update all version pins                         │
│   Time: 0.5 hours                                          │
│                                                             │
│ Step 6: Unified Documentation Rebuild (Day 3)             │
│   Action: Rebuild pkgdown sites, update NEWS cross-refs   │
│   Time: 1 hour                                             │
│                                                             │
│ Total: 8.5 hours across 3 days                            │
│                                                             │
│ [Execute Plan] [Save to Apple Notes] [Export Checklist]   │
└────────────────────────────────────────────────────────────┘
```

### Workflow 2: CRAN Release for 3 Packages

**User:** "I want to release RMediation, mediate, and sensitivity to CRAN"

**RForge Response:**
```
rforge:release:plan({
  packages: ["RMediation", "mediate", "sensitivity"],
  release_type: "minor",
  target: "cran"
})

┌─ RELEASE PLAN ─────────────────────────────────────────────┐
│                                                             │
│ Pre-Release Checklist:                                      │
│   ☐ All tests passing (rforge:health:ecosystem)           │
│   ☐ R CMD check clean (rforge:pkg:check for each)         │
│   ☐ NEWS.md updated (rforge:docs-eco:sync-news)           │
│   ☐ Version bumps coordinated (rforge:version:bump)       │
│   ☐ pkgdown sites rebuilt (rforge:docs:pkgdown-build)     │
│   ☐ Reverse deps checked (rforge:health:reverse-deps)     │
│                                                             │
│ CRAN Submission Sequence:                                   │
│   Day 0: Submit RMediation 2.1.0                           │
│   Day 3: Expected acceptance ✓                             │
│   Day 4: Submit mediate 1.6.0 & sensitivity 0.9.0          │
│   Day 7: Expected acceptance ✓                             │
│   Day 8: Submit mediationverse 1.2.0                       │
│                                                             │
│ Total Timeline: ~10 days                                    │
│                                                             │
│ Post-Release:                                               │
│   • Generate announcement (rforge:release:announce)        │
│   • Update website badges                                  │
│   • Tweet release notes                                    │
│                                                             │
│ [Start Pre-Release Checks] [Export to Apple Notes]         │
└────────────────────────────────────────────────────────────┘
```

### Workflow 3: Ecosystem Health Check

**User:** "How's the health of MediationVerse?"

**RForge Response:**
```
rforge:health:ecosystem({
  packages: "all",
  check_tests: true,
  check_coverage: true,
  check_cran_status: true
})

┌─ MEDIATIONVERSE HEALTH ────────────────────────────────────┐
│ Overall Score: 87/100 (B+) ✅                              │
│                                                             │
│ RMediation:       95/100 (A)  ✅                           │
│   Tests: 187/187 passing                                   │
│   Coverage: 94%                                            │
│   CRAN: OK (last check: 2025-12-15)                       │
│   CI: Passing (Ubuntu, macOS, Windows)                    │
│                                                             │
│ mediate:          89/100 (B+) ✅                           │
│   Tests: 142/142 passing                                   │
│   Coverage: 88%                                            │
│   CRAN: OK (last check: 2025-12-18)                       │
│   CI: Passing (all platforms)                             │
│                                                             │
│ sensitivity:      85/100 (B)  ⚠️                           │
│   Tests: 98/100 passing ⚠️ 2 failures                     │
│   Coverage: 82%                                            │
│   CRAN: Warning (NOTE about documentation)                 │
│   CI: Failing on Windows ❌                                │
│                                                             │
│ pmed:             78/100 (C+) ⚠️                           │
│   Tests: 45/45 passing                                     │
│   Coverage: 65% ⚠️ below 70% threshold                    │
│   CRAN: Not submitted yet                                  │
│   CI: Passing (Ubuntu only)                                │
│                                                             │
│ Recommendations:                                            │
│   1. Fix sensitivity Windows CI failure (PRIORITY)         │
│   2. Increase pmed coverage to 70%+                        │
│   3. Address sensitivity CRAN NOTE                         │
│                                                             │
│ [View Detailed Report] [Generate Fix Plan] [Track Issues]  │
└────────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Rename + Core Tools**
- Rename `statistical-research` → `rforge`
- Implement Tier 1 tools (15 tools)
- Test with single package workflow

**Deliverable:** Can develop/test/document a single R package

### Phase 2: Ecosystem Layer (Week 3-4)

**Dependency + Cascade Management**
- Implement dependency scanning
- Implement impact analysis
- Implement cascade planning

**Deliverable:** Can manage MediationVerse cascades

### Phase 3: Documentation + Release (Week 5)

**Unified Docs + CRAN Coordination**
- Implement unified documentation
- Implement release planning
- Implement CRAN sequencing

**Deliverable:** Can coordinate multi-package releases

### Phase 4: Research Integration (Week 6)

**Manuscript + Analysis Tools**
- Implement analysis tools
- Implement manuscript integration
- Implement simulation tools

**Deliverable:** Full research workflow automation

---

## 💡 ADHD-Friendly Features

### Feature 1: Smart Defaults ⭐⭐⭐

All tools have sensible defaults:
```bash
rforge:pkg:check       # Automatically uses current package
rforge:deps:scan       # Automatically finds ecosystem root
rforge:health:ecosystem  # Checks everything by default
```

### Feature 2: Progress Visualization ⭐⭐⭐

Every long-running operation shows progress:
```
rforge:health:ecosystem

Checking MediationVerse Ecosystem...
[████████░░] 80% (4/5 packages)
Currently: Running tests for pmed...
```

### Feature 3: Cascade Preview ⭐⭐⭐

Always preview before execute:
```
Cascade Plan:
  1. RMediation 2.1.0 ✓ Ready
  2. mediate 1.5.1    → Waiting for #1
  3. sensitivity 0.8.1 → Waiting for #1

Execute? (y/n/save for later)
```

### Feature 4: Checkpoint System ⭐⭐

Save progress on long workflows:
```
Cascade 50% complete - checkpoint saved
Resume anytime with: rforge:cascade:resume <id>
```

---

## 🔗 Integration with Other Servers

| Server | Integration | Example |
|--------|-------------|---------|
| **devops** | CI/CD for R packages | `devops:ci-setup` → creates GitHub Actions for `rforge:pkg:check` |
| **research** | Manuscript writing | `research:write` → uses `rforge:analysis:results` |
| **pm** | Project coordination | `pm:plan-session` → suggests `rforge:health:ecosystem` |
| **github** MCP | Repository operations | `rforge:release:announce` → uses GitHub MCP to create release |

---

## 📊 State Management

RForge maintains state for:
- Ecosystem dependency graph
- Active cascade plans
- Release schedules
- Health check history
- Coverage trends

**Stored in:** `~/.rforge/state.json`

---

## ❓ Next Decisions

1. **Name confirmation:** `rforge` or different name?
2. **Priority tier:** Start with Tier 1, 2, or both?
3. **MediationVerse specifics:** Confirm all 6 package names?
4. **Integration scope:** How deep should research workflow go?
5. **First use case:** What workflow would you use TOMORROW?

**Let's refine this design together!** 🚀
