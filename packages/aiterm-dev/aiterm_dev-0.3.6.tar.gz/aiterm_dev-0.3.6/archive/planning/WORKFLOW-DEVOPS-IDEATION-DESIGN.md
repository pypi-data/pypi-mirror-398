# Workflow Commands & DevOps Ideation Tools - Design

**Date:** 2025-12-20
**Purpose:** Add conversational planning and ideation assistance to MCP ecosystem
**Integration:** Works with RForge, DevOps, PM, Research, Teaching servers

---

## Philosophy: From Idea to Action

**Problem:** Most tools assume you already know WHAT to build and HOW to build it.

**Reality:** ADHD brains need help with:
1. **Clarifying vague ideas** into concrete specifications
2. **Exploring multiple approaches** before committing
3. **Validating assumptions** before investing time
4. **Connecting ideas** to existing projects/tools

**Solution:** Conversational ideation tools that ASSIST with planning, not just execute plans.

---

## Two Categories

### 1. Workflow Commands
**Purpose:** Chain multiple tools together for common end-to-end processes

**Pattern:** `workflow:<domain>:<process>`

**Examples:**
- `workflow:r-pkg:release` - Complete R package release (check → test → build → docs → CRAN)
- `workflow:paper:submit` - Paper submission (compile → check refs → format → upload)
- `workflow:course:week` - Weekly course prep (lecture → slides → homework → publish)

**Characteristics:**
- High-level orchestration
- Smart defaults (ADHD-friendly)
- Progress visualization
- Checkpoint/resume capability
- Error recovery

### 2. DevOps Ideation Tools
**Purpose:** Help refine raw ideas into actionable specifications

**Pattern:** `devops:ideate:<type>`

**Examples:**
- `devops:ideate:feature` - Take feature idea → propose implementations
- `devops:ideate:architecture` - System design brainstorming
- `devops:ideate:workflow` - Custom workflow design

**Characteristics:**
- Conversational (asks clarifying questions)
- Multi-option proposals
- Trade-off analysis
- ADHD-friendly (visual, structured)
- Saves output to files

---

## Part 1: Workflow Commands (15 Commands)

### Category: R Package Workflows

#### `workflow:r-pkg:release`
**Purpose:** Complete R package release process

**Process:**
```
1. Pre-flight checks (dependencies, version bump)
2. Run comprehensive tests (testthat + R CMD check)
3. Update documentation (roxygen2 + pkgdown)
4. Build package tarball
5. Submit to CRAN (or just prepare)
6. Tag release in git
7. Deploy docs to GitHub Pages
```

**Interactive Points:**
- "Version bump type? (patch/minor/major)"
- "CRAN submission ready? (Y/n)"
- "Create GitHub release? (Y/n)"

**Outputs:**
- `RELEASE-CHECKLIST-v{version}.md` - What was done
- `CRAN-SUBMISSION-v{version}.md` - Submission notes
- Git tag: `v{version}`

**Time Estimate:** 15-30 minutes (vs 2-3 hours manual)

---

#### `workflow:r-pkg:new-version`
**Purpose:** Start a new development version after release

**Process:**
```
1. Increment version (x.y.z → x.y.z.9000)
2. Update NEWS.md with "Development version" section
3. Commit changes
4. Create development branch (optional)
```

**Interactive Points:**
- "Create dev branch? (y/N)"
- "Add initial NEWS items? (Y/n)"

**Outputs:**
- Updated DESCRIPTION, NEWS.md
- Git commit

**Time Estimate:** 2 minutes

---

#### `workflow:r-pkg:cascade-update`
**Purpose:** Update one package in ecosystem, cascade to dependents

**Process:**
```
1. Identify affected packages (dependency graph)
2. Estimate work (RForge impact analysis)
3. Propose sequence (topological sort)
4. For each package:
   a. Run checks
   b. Update if needed
   c. Test locally
5. Generate cascade report
```

**Interactive Points:**
- "Update all dependents automatically? (y/N)"
- "Run reverse dependency checks? (Y/n)"

**Outputs:**
- `CASCADE-REPORT-{date}.md` - What was updated
- Test results for each package

**Time Estimate:** 1-3 hours (vs 1-2 days manual)

---

#### `workflow:r-pkg:quick-fix`
**Purpose:** Fix a bug, test, commit, push (fast iteration)

**Process:**
```
1. Run affected tests only (smart test selection)
2. If pass: commit with conventional message
3. Push to current branch
4. Update issue/PR if linked
```

**Interactive Points:**
- "Test scope? (affected/all/skip)"
- "Commit message: fix({package}): {description}"
- "Link to issue? (#XXX)"

**Outputs:**
- Git commit + push
- Updated issue status

**Time Estimate:** 30 seconds - 2 minutes

---

#### `workflow:r-pkg:vignette-to-paper`
**Purpose:** Convert package vignette to standalone paper/preprint

**Process:**
```
1. Extract vignette content
2. Convert to appropriate format (Quarto/RMarkdown)
3. Update references (package citations → full citations)
4. Add manuscript metadata
5. Render to PDF/HTML
```

**Interactive Points:**
- "Target format? (Quarto/RMarkdown/LaTeX)"
- "Journal template? (JSS/JASA/Biostatistics/arXiv)"
- "Include package installation code? (y/N)"

**Outputs:**
- `manuscripts/{vignette-name}/` directory
- Rendered manuscript
- Bibliography file

**Time Estimate:** 10-15 minutes

---

### Category: Research Workflows

#### `workflow:paper:from-analysis`
**Purpose:** Turn exploratory analysis into manuscript

**Process:**
```
1. Scan analysis files (R/Python scripts, notebooks)
2. Identify key results (plots, tables, models)
3. Propose manuscript structure
4. Generate template sections
5. Link code → results → manuscript
```

**Interactive Points:**
- "Which analyses to include? (select multiple)"
- "Manuscript type? (Full paper/Short communication/Preprint)"
- "Target journal? (for formatting)"

**Outputs:**
- `manuscripts/{paper-name}/` structure:
  - `manuscript.qmd` (or .Rmd)
  - `analysis/` (linked scripts)
  - `figures/` (auto-generated)
  - `references.bib`
- `MANUSCRIPT-PLAN.md` - Sections outline

**Time Estimate:** 15-20 minutes (vs 2-3 hours manual setup)

---

#### `workflow:paper:submit`
**Purpose:** Prepare manuscript for journal submission

**Process:**
```
1. Render manuscript (PDF + Word if requested)
2. Check references (missing citations, format)
3. Generate submission checklist
4. Check journal requirements (word count, figures, etc.)
5. Create submission package (manuscript + supplements + cover letter)
6. Generate upload-ready files
```

**Interactive Points:**
- "Journal name? (for specific requirements)"
- "Include code/data? (Y/n)"
- "Cover letter template? (default/custom)"

**Outputs:**
- `submission-{journal}-{date}/` directory:
  - Manuscript (PDF + Word)
  - Figures (high-res)
  - Supplements
  - Cover letter
  - Submission checklist
- `SUBMISSION-CHECKLIST-{journal}.md`

**Time Estimate:** 10-15 minutes

---

#### `workflow:research:simulation-study`
**Purpose:** Design and run simulation study from scratch

**Process:**
```
1. Define parameters (sample sizes, effects, scenarios)
2. Generate simulation code template
3. Set up parallel execution
4. Run simulations (with progress tracking)
5. Analyze results (summarize, visualize)
6. Generate report
```

**Interactive Points:**
- "Number of scenarios? (1-20)"
- "Sample sizes? (e.g., 50,100,200)"
- "Replications per scenario? (default: 1000)"
- "Run now or just setup? (run/setup)"

**Outputs:**
- `simulations/{study-name}/` directory:
  - `scenarios.R` - Parameter definitions
  - `simulate.R` - Main simulation code
  - `analyze.R` - Results analysis
  - `results/` - Saved results
  - `SIMULATION-REPORT.html`

**Time Estimate:** 5-10 minutes setup, varies for execution

---

### Category: Teaching Workflows

#### `workflow:course:weekly-prep`
**Purpose:** Prepare all materials for upcoming week

**Process:**
```
1. Check course schedule (get week number)
2. Generate lecture slides from outline
3. Create homework assignment
4. Update course website
5. Prepare Canvas items
6. Send reminder to students (optional)
```

**Interactive Points:**
- "Week number? (auto-detect from date if possible)"
- "Include solutions? (y/N)"
- "Publish to Canvas now? (y/N)"

**Outputs:**
- `week-{N}/` directory:
  - Lecture slides (Quarto/Beamer)
  - Homework (PDF + Rmd source)
  - Solutions (if requested)
- Updated course website
- Canvas ready files

**Time Estimate:** 15-20 minutes (vs 1-2 hours manual)

---

#### `workflow:course:exam-create`
**Purpose:** Create exam with solutions and rubric

**Process:**
```
1. Select topics from course outline
2. Generate question bank
3. Create exam (balanced difficulty)
4. Generate solutions
5. Create grading rubric
6. Prepare Canvas quiz (optional)
```

**Interactive Points:**
- "Exam type? (Midterm/Final/Quiz)"
- "Number of questions? (default: topic-based)"
- "Include Canvas import? (Y/n)"
- "Difficulty distribution? (Easy/Medium/Hard %)"

**Outputs:**
- `exams/{exam-name}/` directory:
  - Exam (PDF, student version)
  - Solutions (PDF, instructor version)
  - Grading rubric
  - Canvas import file (.qti)
- `EXAM-METADATA.md` - Topics covered, learning outcomes

**Time Estimate:** 20-30 minutes

---

### Category: Dev-Tools Workflows

#### `workflow:mcp:new-server`
**Purpose:** Scaffold new MCP server from template

**Process:**
```
1. Choose server type (TypeScript/Python/Bun)
2. Generate directory structure
3. Create initial tools (from templates)
4. Set up testing
5. Add to MCP configs (Desktop + Browser)
6. Generate documentation
```

**Interactive Points:**
- "Server name? (lowercase, dash-separated)"
- "Language? (TypeScript/Python/Bun)"
- "Initial tools? (list or generate later)"
- "Add to configs now? (Y/n)"

**Outputs:**
- `~/projects/dev-tools/mcp-servers/{server-name}/` directory
- Updated configs (settings.json, MCP_SERVER_CONFIG.json)
- `README.md` with usage instructions
- Initial tool templates

**Time Estimate:** 5-10 minutes

---

#### `workflow:mcp:add-tool`
**Purpose:** Add new tool to existing MCP server

**Process:**
```
1. Analyze existing server structure
2. Generate tool template (matches server patterns)
3. Add to tool registry
4. Generate tests
5. Update documentation
```

**Interactive Points:**
- "Tool name? (e.g., pkg_check)"
- "Tool description?"
- "Input parameters? (describe or auto-generate)"
- "Generate tests? (Y/n)"

**Outputs:**
- New tool file (TypeScript/Python)
- Test file
- Updated README/docs

**Time Estimate:** 3-5 minutes

---

#### `workflow:cli:new-command`
**Purpose:** Add new command to CLI tool (like aiterm)

**Process:**
```
1. Analyze CLI structure (Typer/Click/etc.)
2. Generate command template
3. Add to command registry
4. Generate tests
5. Update --help documentation
```

**Interactive Points:**
- "Command name? (e.g., profile switch)"
- "Command arguments?"
- "Subcommands? (y/N)"

**Outputs:**
- Command file
- Test file
- Updated CLI help

**Time Estimate:** 3-5 minutes

---

### Category: Documentation Workflows

#### `workflow:docs:deploy`
**Purpose:** Build and deploy documentation site

**Process:**
```
1. Detect doc system (MkDocs/pkgdown/Quarto)
2. Build documentation
3. Check for broken links
4. Deploy to GitHub Pages
5. Update README badges
```

**Interactive Points:**
- "Check links first? (Y/n)"
- "Deploy now or just build? (deploy/build)"

**Outputs:**
- Built documentation site
- Deployment log
- Updated README (if badges added)

**Time Estimate:** 2-5 minutes

---

#### `workflow:docs:reference-from-code`
**Purpose:** Generate API reference from code comments

**Process:**
```
1. Scan codebase for exported functions
2. Extract docstrings/roxygen comments
3. Generate reference pages
4. Link to usage examples
5. Build site
```

**Interactive Points:**
- "Include internal functions? (y/N)"
- "Group by category or file? (category/file)"

**Outputs:**
- Reference documentation pages
- Updated site structure

**Time Estimate:** 5-10 minutes

---

### Category: Cross-Domain Workflows

#### `workflow:project:archive`
**Purpose:** Archive completed project (research/teaching/dev)

**Process:**
```
1. Check git status (warn if uncommitted changes)
2. Create archive tag
3. Generate project summary
4. Move to archive directory
5. Update master dashboard
6. Optional: Create DOI (Zenodo)
```

**Interactive Points:**
- "Archive reason? (Completed/Paused/Cancelled)"
- "Create DOI? (y/N)"
- "Keep in git? (Y/n)"

**Outputs:**
- Git tag: `archive-{date}`
- `PROJECT-SUMMARY.md`
- Moved to archive/ directory
- Updated dashboard

**Time Estimate:** 3-5 minutes

---

## Part 2: DevOps Ideation Tools (10 Tools)

### Core Ideation Tool

#### `devops:ideate:feature`
**Purpose:** Take raw feature idea → refined specification with options

**Conversation Flow:**
```
1. User provides raw idea (1-2 sentences)
2. Tool asks clarifying questions:
   - What problem does this solve?
   - Who will use it?
   - What's the success criteria?
   - What's your time budget? (quick/medium/long)
   - Any constraints? (tech stack, dependencies)
3. Analyzes context:
   - Similar features in codebase?
   - Existing tools/libraries?
   - ADHD-friendly approaches?
4. Proposes 3-4 implementation options:
   - Option A: Quick & Simple (minimal features, fast)
   - Option B: Balanced (good features, reasonable time)
   - Option C: Comprehensive (full featured, more time)
   - Option D: Creative (unconventional approach)
5. For each option:
   - What you get
   - What you don't get
   - Time estimate
   - Complexity (⭐-⭐⭐⭐⭐⭐)
   - ADHD-friendliness (🧠 rating)
6. Generates specification document
```

**Interactive Points:**
- Entire flow is conversational
- User can ask "why?" at any point
- Can request hybrid approaches
- Can deep-dive into any option

**Outputs:**
- `FEATURE-SPEC-{feature-name}-{date}.md`:
  ```markdown
  # Feature: {Name}

  ## Problem Statement
  {what problem this solves}

  ## User Story
  {who uses it and why}

  ## Options Analysis

  ### Option A: Quick & Simple ⚡
  **Time:** 1-2 hours
  **Complexity:** ⭐⭐
  **ADHD:** 🧠🧠🧠🧠🧠 (excellent)

  **What you get:**
  - Core functionality
  - Clear, simple interface
  - Quick iteration

  **What you don't get:**
  - Advanced features
  - Extensive error handling
  - Multiple formats

  **Implementation notes:**
  {specific guidance}

  ### Option B: Balanced ⚖️
  ...

  ## Recommended Approach
  {AI recommendation with reasoning}

  ## Next Steps
  1. [ ] Choose option
  2. [ ] Review implementation notes
  3. [ ] Start with...
  ```

**Example Session:**
```
User: "I want a tool to quickly create R package skeletons"

Tool: "Great idea! Let me ask a few questions to refine this:

1. What problem does this solve for you?
   → Typing same boilerplate is annoying, forget best practices

2. Who will use it? (just you / your team / public)
   → Just me for now

3. What's your time budget for building this?
   → Quick (1-2 hours) if possible

4. Any constraints?
   → Must work with my existing R workflow, ADHD-friendly

5. Success looks like...?
   → Type one command, get working package structure in 30 seconds

Analyzing...
✓ Found similar: usethis package (but heavy)
✓ Found: Your existing R package templates
✓ ADHD consideration: Minimal decisions, fast feedback

Here are 4 approaches:

**Option A: Shell Script Wrapper ⚡**
Time: 30 minutes
Complexity: ⭐
ADHD: 🧠🧠🧠🧠🧠

Wrap existing tools (usethis + your templates)
Pros: Fast, leverages existing code
Cons: Not portable, shell-only

**Option B: R Function**
Time: 1-2 hours
...

**Option C: MCP Tool**
Time: 3-4 hours
...

**Option D: Template Repository**
Time: 15 minutes
...

Which approach interests you? Or should I explain trade-offs?"
```

**Time Estimate:** 5-15 minute conversation

---

#### `devops:ideate:architecture`
**Purpose:** System design brainstorming with trade-off analysis

**Conversation Flow:**
```
1. User describes system need
2. Tool asks:
   - Scale requirements? (personal/team/public)
   - Performance needs? (fast/moderate/doesn't matter)
   - Maintainability priority? (quick hack/long-term)
   - Integration points? (what connects to this?)
3. Proposes architectural patterns:
   - Monolith vs Microservices
   - Sync vs Async
   - Client-Server vs Standalone
   - (with ADHD-friendly explanations)
4. For each pattern:
   - Visual diagram (ASCII art)
   - Pros/cons
   - When to use
   - Complexity vs flexibility trade-off
```

**Outputs:**
- `ARCHITECTURE-{system-name}-{date}.md`
- Visual diagrams
- Technology recommendations
- Migration path (if updating existing)

**Example:**
```
User: "I need to organize my MCP servers better"

Tool: "Let me understand the requirements:

1. How many servers? (current and planned)
   → 6 now, maybe 10 eventually

2. Do they need to talk to each other?
   → Yes! RForge needs DevOps feedback

3. Priority? (speed to build / maintainability / flexibility)
   → Maintainability (I'll use this for years)

4. ADHD concerns?
   → Must be simple to add new servers, clear naming

Here are 3 architectural approaches:

**Option A: Hub-and-Spoke 🌟**
```
     ┌─────────┐
     │   Hub   │ ← Central coordinator
     └────┬────┘
     ┌────┴────┐
  ┌──┴──┐   ┌──┴──┐
  │RForge│   │DevOps│
  └─────┘   └─────┘
```

Pros: Clear communication path, easy debugging
Cons: Hub is single point of failure
ADHD: 🧠🧠🧠🧠 (good - one mental model)

**Option B: Peer-to-Peer**
...

**Option C: Layered**
...

Which pattern fits your mental model?"
```

**Time Estimate:** 10-20 minute conversation

---

#### `devops:ideate:workflow`
**Purpose:** Design custom workflows for repetitive processes

**Conversation Flow:**
```
1. User describes current manual process
2. Tool asks:
   - How often do you do this? (daily/weekly/monthly)
   - What's most annoying part?
   - What can't be automated? (requires human judgment)
   - What ADHD challenges? (too many steps, easy to forget, etc.)
3. Identifies automation opportunities
4. Proposes workflow with:
   - Automated steps (highlighted)
   - Decision points (requires human input)
   - Escape hatches (for errors)
   - Progress visualization
5. Generates workflow script/template
```

**Outputs:**
- `WORKFLOW-{name}-{date}.md` - Specification
- Implementation template (bash/Python/etc.)
- Checklist version (manual fallback)

**Example:**
```
User: "I always forget steps when releasing R packages to CRAN"

Tool: "Let's capture this workflow. Walk me through what you currently do:

1. What's the first thing you do?
   → Run R CMD check

2. Then?
   → Update NEWS, version in DESCRIPTION
   → Run tests
   → Build pkgdown
   → Submit to CRAN

3. What do you often forget?
   → Updating citation file
   → Checking reverse dependencies
   → Tagging in git

4. What requires your judgment?
   → Writing NEWS entries
   → Deciding on version bump

5. ADHD challenge?
   → Too many manual steps, lose track

Analyzing...
✓ 12 steps total
✓ 8 can be automated
✓ 4 require human input
✓ 2 commonly forgotten (citation, git tag)

Proposed workflow:

**Automated Steps:**
1. ✅ Run R CMD check
2. ❓ Bump version (asks: patch/minor/major)
3. ✅ Update citation
4. ❓ Update NEWS (opens editor with template)
5. ✅ Run tests
6. ✅ Check reverse dependencies
7. ✅ Build pkgdown
8. ❓ Review submission (shows what will happen)
9. ✅ Submit to CRAN
10. ✅ Tag in git
11. ✅ Deploy docs
12. ✅ Create GitHub release

**Progress Visualization:**
[=====>          ] 5/12 - Checking reverse dependencies...

**Escape Hatches:**
- Ctrl+C at any point → saves state
- Can resume with `workflow:resume`

Want me to generate the implementation?"
```

**Time Estimate:** 10-15 minute conversation

---

#### `devops:ideate:refactor`
**Purpose:** Plan code refactoring with risk analysis

**Conversation Flow:**
```
1. User points to code that needs refactoring
2. Tool analyzes:
   - Code complexity
   - Test coverage
   - Dependencies (who uses this?)
   - Change frequency (git history)
3. Asks:
   - What's the pain point? (hard to maintain/slow/confusing)
   - Risk tolerance? (can't break anything / some breakage OK)
   - Time budget?
4. Proposes refactoring strategies:
   - Strangler Fig (gradual replacement)
   - Big Bang (rewrite all at once)
   - Extract & Isolate (pull out specific parts)
5. For each strategy:
   - Steps required
   - Risk level (🔴🟡🟢)
   - Rollback plan
   - Test requirements
```

**Outputs:**
- `REFACTOR-PLAN-{component}-{date}.md`
- Risk assessment
- Step-by-step guide
- Testing checklist

**Time Estimate:** 10-20 minute conversation

---

#### `devops:ideate:integration`
**Purpose:** Design integration between systems/tools

**Conversation Flow:**
```
1. User describes what needs to connect
2. Tool asks:
   - Data flow direction? (A→B, B→A, bidirectional)
   - Real-time or batch?
   - Error handling needs?
   - Authentication/security?
3. Analyzes both systems (APIs, data formats, etc.)
4. Proposes integration patterns:
   - Direct API calls
   - Message queue
   - Webhook/events
   - Shared database
   - File-based
5. For each pattern:
   - Architecture diagram
   - Implementation complexity
   - Failure modes
   - Maintenance burden
```

**Outputs:**
- `INTEGRATION-{systemA}-{systemB}-{date}.md`
- Code examples
- Error handling guide

**Time Estimate:** 15-25 minute conversation

---

### Specialized Ideation Tools

#### `devops:ideate:naming`
**Purpose:** Help choose consistent, ADHD-friendly names

**Conversation Flow:**
```
1. User describes what needs naming (tool/command/server/etc.)
2. Tool asks:
   - What does it do? (1 sentence)
   - Who uses it?
   - What category? (R/research/teaching/dev-tools)
   - Any naming constraints? (length, existing patterns)
3. Analyzes existing naming in project
4. Proposes 5-7 name options with:
   - Rationale
   - Pros/cons
   - Autocomplete-friendliness score
   - Memorability score (ADHD consideration)
5. Can iterate based on feedback
```

**Outputs:**
- `NAMING-OPTIONS-{date}.md`
- Selected name + rationale

**Example:**
```
User: "Need to name a tool that checks R package dependencies"

Tool: "Let me understand:

1. What does it do exactly?
   → Scans DESCRIPTION, finds all dependencies, checks if installed

2. Who uses it?
   → Me, maybe other MediationVerse developers

3. Context?
   → RForge MCP server

4. Existing pattern?
   → Yes: rforge:pkg:test, rforge:deps:scan

Here are naming options:

**Option 1: `rforge:deps:check`**
Pros: Matches existing pattern, clear
Cons: "check" is generic
Autocomplete: ⭐⭐⭐⭐⭐ (follows pattern)
Memory: 🧠🧠🧠🧠 (verb matches meaning)

**Option 2: `rforge:deps:verify`**
Pros: More specific than "check"
Cons: Slightly longer
Autocomplete: ⭐⭐⭐⭐⭐
Memory: 🧠🧠🧠 (less common word)

**Option 3: `rforge:deps:status`**
...

Recommendation: `rforge:deps:check`
Reason: Follows established pattern, matches user mental model

Sound good?"
```

**Time Estimate:** 3-5 minute conversation

---

#### `devops:ideate:testing-strategy`
**Purpose:** Design testing approach for project

**Conversation Flow:**
```
1. User describes codebase
2. Tool asks:
   - Current test coverage? (none/some/good)
   - Risk areas? (what breaks would hurt most)
   - Time budget for testing?
   - CI/CD setup? (yes/no/planned)
3. Analyzes codebase structure
4. Proposes testing strategy:
   - Test pyramid (unit/integration/e2e ratios)
   - What to test first (high-value tests)
   - What to skip (low ROI)
   - Test framework recommendations
5. Generates testing roadmap
```

**Outputs:**
- `TESTING-STRATEGY-{date}.md`
- Test templates
- Priority order (ADHD: start with quick wins)

**Time Estimate:** 10-15 minute conversation

---

#### `devops:ideate:docs-structure`
**Purpose:** Design documentation organization

**Conversation Flow:**
```
1. User describes project
2. Tool asks:
   - Audience? (users/developers/both)
   - Complexity? (simple tool / complex system)
   - ADHD considerations? (need quick-start / searchable / etc.)
3. Analyzes existing docs (if any)
4. Proposes documentation structure:
   - Quick-start (5 minutes to value)
   - Tutorials (learn by doing)
   - How-to guides (solve specific problems)
   - Reference (complete details)
   - Explanation (understand concepts)
5. Templates for each doc type
```

**Outputs:**
- `DOCS-STRUCTURE-{date}.md`
- Templates for each doc type
- Table of contents outline

**Time Estimate:** 10-15 minute conversation

---

#### `devops:ideate:performance`
**Purpose:** Analyze and propose performance improvements

**Conversation Flow:**
```
1. User describes performance problem
2. Tool asks:
   - Current performance? (numbers if possible)
   - Target performance?
   - Bottleneck known? (yes/no/maybe)
   - Constraints? (can't change X, must keep Y)
3. Analyzes code (if provided)
4. Proposes optimization strategies:
   - Quick wins (low-hanging fruit)
   - Medium effort (refactoring)
   - Long-term (architecture changes)
5. For each strategy:
   - Expected speedup
   - Implementation difficulty
   - Risks
```

**Outputs:**
- `PERFORMANCE-PLAN-{date}.md`
- Profiling guide
- Implementation priority

**Time Estimate:** 15-20 minute conversation

---

#### `devops:ideate:migration`
**Purpose:** Plan migration from old to new system

**Conversation Flow:**
```
1. User describes current and target systems
2. Tool asks:
   - Data volume?
   - Downtime tolerance? (none/hours/days)
   - Rollback requirement?
   - User impact?
3. Analyzes migration complexity
4. Proposes migration strategies:
   - Big Bang (all at once)
   - Phased (gradual cutover)
   - Parallel Run (old + new simultaneously)
   - Dark Launch (new hidden behind flag)
5. For each strategy:
   - Timeline
   - Risk level
   - Rollback plan
   - Testing requirements
```

**Outputs:**
- `MIGRATION-PLAN-{old}-to-{new}-{date}.md`
- Rollback procedures
- Testing checklist

**Time Estimate:** 20-30 minute conversation

---

#### `devops:ideate:error-handling`
**Purpose:** Design error handling strategy

**Conversation Flow:**
```
1. User describes system/component
2. Tool asks:
   - What can go wrong? (known failure modes)
   - User impact of failures?
   - Recovery requirements? (automatic/manual/notify)
   - ADHD consideration? (need clear error messages)
3. Identifies failure scenarios
4. Proposes error handling approach:
   - Fail fast vs fail safe
   - Retry strategies
   - Error messages (ADHD-friendly)
   - Logging/monitoring
5. Generates error handling patterns
```

**Outputs:**
- `ERROR-HANDLING-{component}-{date}.md`
- Error message templates
- Logging strategy

**Time Estimate:** 10-15 minute conversation

---

## Implementation Notes

### Technical Architecture

**All ideation tools follow same pattern:**

```typescript
interface IdeationTool {
  // 1. Gather context
  async gatherContext(userInput: string): Promise<Context>

  // 2. Ask clarifying questions
  async askQuestions(context: Context): Promise<Requirements>

  // 3. Analyze & propose options
  async generateOptions(requirements: Requirements): Promise<Option[]>

  // 4. User selects/refines
  async refineOptions(options: Option[], feedback: string): Promise<Option[]>

  // 5. Generate specification
  async generateSpec(selectedOption: Option): Promise<Specification>

  // 6. Save to file
  async saveSpec(spec: Specification): Promise<FilePath>
}
```

### ADHD-Friendly Features

**All tools include:**

1. **Progress Indicators**
   ```
   [●●●○○] Step 3 of 5: Analyzing options...
   ```

2. **Clear Milestones**
   ```
   ✓ Context gathered
   ✓ Requirements clear
   → Generating options...
   ```

3. **Escape Hatches**
   - Save state at any point
   - Resume later
   - Go back to previous step

4. **Visual Hierarchy**
   - Headers, bullets, tables
   - Emoji for quick scanning
   - Color coding (if terminal supports)

5. **Quick Summaries**
   - TL;DR at top
   - Recommended option highlighted
   - Time estimates for each option

### Integration with Existing Tools

**Workflow commands use existing tools:**
- `workflow:r-pkg:release` → calls `rforge:pkg:check`, `rforge:pkg:build`, etc.
- `workflow:paper:submit` → calls `research:compile`, `research:check-refs`, etc.
- Cross-server coordination built-in

**Ideation tools prepare for workflow commands:**
- `devops:ideate:feature` → can generate `workflow` command spec
- Specifications include implementation templates
- Direct path from ideation → execution

### File Locations

**All proposals saved to:**
- `~/PROPOSALS/` - Master directory for all proposals
- `{project}/proposals/` - Project-specific (if in project context)

**Naming convention:**
```
{CATEGORY}-{NAME}-{DATE}.md

Examples:
FEATURE-SPEC-auto-cascade-2025-12-20.md
ARCHITECTURE-mcp-organization-2025-12-20.md
WORKFLOW-r-pkg-release-2025-12-20.md
```

---

## Usage Examples

### Example 1: New Feature Ideation

```bash
# User has vague idea
$ devops:ideate:feature

"I want something to make R package development faster"

# Tool asks questions, proposes 4 options
# User selects Option B (balanced approach)

# Generated:
~/PROPOSALS/FEATURE-SPEC-quick-pkg-setup-2025-12-20.md

# Contains:
- Problem statement
- 4 implementation options (detailed)
- Recommended approach: MCP tool
- Next steps: ["Create MCP tool skeleton", "Test with one package", ...]
```

### Example 2: Workflow Automation

```bash
# User wants to automate weekly teaching prep
$ workflow:course:weekly-prep

Week number? [auto-detected: 14]
Include solutions? [y/N] y
Publish to Canvas now? [y/N] n

→ Generating lecture slides...
→ Creating homework assignment...
→ Generating solutions...
→ Building PDF files...
→ Updating course website...

✓ Complete!

Files created:
- teaching/stat-440/week-14/lecture-slides.pdf
- teaching/stat-440/week-14/homework-14.pdf
- teaching/stat-440/week-14/homework-14-solutions.pdf

Next: Review materials, then run `workflow:course:publish`
```

### Example 3: Architecture Design

```bash
# User needs to reorganize MCP servers
$ devops:ideate:architecture

"I need to organize my MCP servers better"

# 5-minute conversation
# Tool proposes 3 architectural patterns
# User selects layered approach

# Generated:
~/PROPOSALS/ARCHITECTURE-mcp-layered-2025-12-20.md

# Contains:
- Visual diagrams (ASCII art)
- Server responsibilities
- Communication patterns
- Implementation plan (phased)
- Migration strategy from current state
```

---

## Success Criteria

**For Workflow Commands:**
- [ ] Save 50%+ time on common processes
- [ ] Zero missed steps (no more forgotten git tags!)
- [ ] ADHD-friendly (progress bars, clear next steps)
- [ ] Resume capability (interrupted workflow → pickup where left off)

**For Ideation Tools:**
- [ ] Raw idea → specification in 10-15 minutes
- [ ] Multiple options always provided (no analysis paralysis)
- [ ] Saved to files (no lost thoughts!)
- [ ] ADHD-friendly (visual, structured, clear recommendations)
- [ ] Leads to action (not just brainstorming)

---

## Phased Implementation

### Phase 1: Core Ideation (Week 1)
- `devops:ideate:feature` (most important!)
- `devops:ideate:workflow`
- `devops:ideate:naming`

### Phase 2: High-Value Workflows (Week 2)
- `workflow:r-pkg:release`
- `workflow:r-pkg:cascade-update`
- `workflow:paper:from-analysis`

### Phase 3: Teaching & Dev-Tools (Week 3)
- `workflow:course:weekly-prep`
- `workflow:course:exam-create`
- `workflow:mcp:new-server`

### Phase 4: Advanced Ideation (Week 4)
- `devops:ideate:architecture`
- `devops:ideate:refactor`
- `devops:ideate:testing-strategy`

### Phase 5: Remaining Workflows (Ongoing)
- All other workflow commands
- All other ideation tools
- Cross-integration refinement

---

## Open Questions

1. **Conversation State:**
   - How to persist multi-turn conversations?
   - Resume interrupted ideation sessions?

2. **Option Ranking:**
   - How to score ADHD-friendliness objectively?
   - Time estimates accuracy?

3. **Integration:**
   - How tightly to couple ideation → workflow execution?
   - Auto-generate workflow commands from specs?

4. **Learning:**
   - Track which options users choose?
   - Improve recommendations over time?

---

## Next Steps

1. **Review this design** - Does it match your vision?
2. **Prioritize tools** - Which ideation/workflow tools are most valuable to you?
3. **Prototype one** - Start with `devops:ideate:feature` (most universally useful)
4. **Iterate** - Refine based on actual usage

**Status:** Design complete, ready for feedback! 🚀
