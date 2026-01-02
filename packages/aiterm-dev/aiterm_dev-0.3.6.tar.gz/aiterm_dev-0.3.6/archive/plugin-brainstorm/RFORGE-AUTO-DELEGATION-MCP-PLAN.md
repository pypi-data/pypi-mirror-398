# RForge Auto-Delegation - MCP Server Implementation Plan

**Context:** RForge is a TypeScript MCP server (rforge-mcp) at `~/projects/dev-tools/mcp-servers/rforge/`
**Goal:** Add automatic task analysis and background agent delegation to existing MCP tools
**Timeline:** 8 days (Dec 22-30, 2025)
**Architecture:** TypeScript + MCP SDK (not Python CLI)

---

## 🎯 Current State Analysis

### ✅ What Already Exists

**RForge MCP Server (v0.1.0)**
- TypeScript MCP server using `@modelcontextprotocol/sdk`
- 10 tools across 6 categories
- Bun build system (dist/index.js)
- Portable installation (npx rforge-mcp)
- Auto-configuration for Claude Desktop

**Existing Tool Categories:**
```
src/tools/
├── discovery/         # rforge_detect, rforge_status
├── deps/             # rforge_deps, rforge_impact
├── ideation/         # rforge_plan, rforge_quick_fix (NEW!)
├── cascade/          # rforge_cascade_plan (placeholder)
├── docs/             # rforge_doc_check (placeholder)
├── release/          # rforge_release_plan (placeholder)
├── tasks/            # rforge_capture, rforge_complete (placeholder)
└── init/             # Auto-context detection
```

**Key Existing Features:**
- ✅ Context auto-detection (init tool)
- ✅ Pattern-based planning (ideation/plan.ts)
- ✅ Context analysis (utils/context-analysis.ts)
- ✅ Spec generation (utils/spec-generator.ts)
- ✅ 14 passing tests

---

## 🧩 How MCP Servers Work (Important!)

### MCP Architecture Constraints

**MCP servers are STATELESS request/response:**
```typescript
// MCP Tool Pattern
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  // Execute tool synchronously
  const result = await executeTool(name, args);

  // Return result
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
});
```

**Key constraints:**
1. ❌ **No long-running processes** - Each tool call must complete quickly
2. ❌ **No server-side state** - Can't track "running agents" on server
3. ❌ **No progress callbacks** - Can't stream progress to Claude
4. ❌ **No inter-tool coordination** - Each tool call is independent

### What This Means for Auto-Delegation

**Traditional approach (NOT possible in MCP):**
```typescript
// ❌ This won't work - MCP tools must complete quickly
async function rforge_auto_analyze() {
  // Start 5 agents in parallel
  const agents = [impact, tests, docs, cran, health];

  // Wait for all to complete (could take 3 minutes!)
  const results = await Promise.all(agents);  // ❌ Too slow for MCP

  return synthesize(results);
}
```

**MCP-compatible approach (what we CAN do):**
```typescript
// ✅ Option 1: Sequential tool calls (Claude orchestrates)
// Claude: rforge_impact → rforge_tests → rforge_docs → synthesize

// ✅ Option 2: Single fast tool that delegates to background R process
async function rforge_analyze() {
  // Launch R script in background
  exec('Rscript analyze.R &');  // Returns immediately

  // Return task ID
  return { task_id: "abc123", status: "running" };
}

// Then later:
async function rforge_results(task_id) {
  // Check if R script finished, return results
  return readResults(task_id);
}

// ✅ Option 3: Smart single tool that does FAST analysis
async function rforge_quick_impact() {
  // Do fast analysis (< 10 seconds)
  // Return good-enough results
}
```

---

## 💡 Revised Auto-Delegation Strategy

### Strategy: Claude-Side Orchestration + Fast MCP Tools

**Instead of:** MCP server runs background agents (impossible)
**We do:** Claude orchestrates parallel MCP tool calls + shows progress

```
Claude Code Session:
┌─────────────────────────────────────────────────┐
│ User: "Update RMediation bootstrap"             │
│                                                  │
│ Claude (orchestrator):                          │
│  1. Pattern recognition (local)                 │
│  2. Parallel MCP calls:                         │
│     [rforge_impact] ────────→ Result 1          │
│     [rforge_tests]  ────────→ Result 2          │
│     [rforge_docs]   ────────→ Result 3          │
│     [rforge_cran]   ────────→ Result 4          │
│  3. Synthesis (local)                           │
│  4. Show dashboard + results                    │
└─────────────────────────────────────────────────┘
```

**Key insight:** The auto-delegation logic lives in **Claude Code plugins/skills**, not the MCP server!

---

## 🏗️ Architecture: Hybrid Approach

### What Goes Where

**MCP Server (rforge-mcp):**
- ✅ Fast, focused tools (< 10 sec each)
- ✅ Background R process launchers (async)
- ✅ Result checkers (poll for completion)
- ✅ Data analyzers (quick analysis)

**Claude Code Plugin (new!):**
- ✅ Pattern recognition
- ✅ Orchestration (parallel calls)
- ✅ Progress dashboard
- ✅ Results synthesis
- ✅ User interaction

**File structure:**
```
mcp-servers/rforge/          # MCP server (TypeScript)
├── src/tools/
│   ├── ideation/           # Existing
│   ├── analysis/           # NEW - Fast analysis tools
│   │   ├── quick-impact.ts
│   │   ├── quick-tests.ts
│   │   ├── quick-docs.ts
│   │   └── quick-health.ts
│   └── async/              # NEW - Background R launchers
│       ├── launch-analysis.ts
│       ├── check-status.ts
│       └── get-results.ts

~/.claude/plugins/           # Claude Code plugin (NEW!)
└── rforge-orchestrator/
    ├── plugin.json
    ├── agents/
    │   └── orchestrator.ts  # Main orchestration agent
    └── skills/
        └── analyze.md       # /rforge:analyze skill
```

---

## 📅 Revised 8-Day Plan

### Day 1-2: Fast Analysis Tools (MCP Server)

**Goal:** Add 4 fast analysis tools to rforge-mcp

#### Tools to implement:

**1. `rforge_quick_impact` (2 hours)**
```typescript
// src/tools/analysis/quick-impact.ts
export async function quickImpact(args: {
  package_path: string;
  change_description?: string;
}): Promise<QuickImpactResult> {
  // Fast dependency scan (< 5 sec)
  const deps = await parseDESCRIPTION(args.package_path);
  const affected = await findAffectedPackages(deps);

  return {
    affected_count: affected.length,
    affected_packages: affected,
    estimated_hours: affected.length * 2,  // Simple heuristic
    severity: affected.length > 2 ? 'HIGH' : 'MEDIUM'
  };
}
```

**2. `rforge_quick_tests` (2 hours)**
```typescript
// src/tools/analysis/quick-tests.ts
export async function quickTests(args: {
  package_path: string;
}): Promise<QuickTestResult> {
  // Check test files exist
  const testFiles = await glob(`${args.package_path}/tests/**/*.R`);

  // Parse testthat results (if available)
  const lastResults = await readTestResults(args.package_path);

  return {
    test_files_count: testFiles.length,
    last_run: lastResults?.timestamp,
    passing: lastResults?.passing || null,
    coverage: lastResults?.coverage || null,
    recommendation: testFiles.length === 0 ? 'ADD_TESTS' : 'RUN_TESTS'
  };
}
```

**3. `rforge_quick_docs` (1 hour)**
```typescript
// Fast doc drift detection
export async function quickDocs(args: {
  package_path: string;
}): Promise<QuickDocsResult> {
  // Check for NEWS.md, vignettes, README
  const hasNews = await fileExists(`${args.package_path}/NEWS.md`);
  const vignettes = await glob(`${args.package_path}/vignettes/*.Rmd`);

  return {
    has_news: hasNews,
    vignette_count: vignettes.length,
    needs_update: !hasNews,  // Simple heuristic
    recommendation: 'UPDATE_NEWS'
  };
}
```

**4. `rforge_quick_health` (1 hour)**
```typescript
// Overall package health check
export async function quickHealth(args: {
  package_path: string;
}): Promise<QuickHealthResult> {
  // Combine quick checks
  const impact = await quickImpact(args);
  const tests = await quickTests(args);
  const docs = await quickDocs(args);

  const score = calculateHealthScore(impact, tests, docs);

  return {
    overall_score: score,
    impact,
    tests,
    docs,
    grade: scoreToGrade(score)
  };
}
```

**Deliverable:** 4 new MCP tools, < 10 sec each

---

### Day 3-4: Background Analysis Tools (MCP Server)

**Goal:** Tools for launching/checking long-running R analysis

#### Tools to implement:

**1. `rforge_launch_analysis` (3 hours)**
```typescript
// src/tools/async/launch-analysis.ts
import { spawn } from 'child_process';

export async function launchAnalysis(args: {
  package_path: string;
  analysis_type: 'full_check' | 'coverage' | 'performance';
}): Promise<LaunchResult> {
  // Generate unique task ID
  const taskId = generateTaskId();

  // Create R script
  const script = generateRScript(args.analysis_type, args.package_path);
  const scriptPath = `/tmp/rforge-${taskId}.R`;
  await writeFile(scriptPath, script);

  // Launch R in background
  const child = spawn('Rscript', [scriptPath], {
    detached: true,
    stdio: 'ignore'
  });

  child.unref();  // Don't wait for it

  // Save task metadata
  await saveTaskMeta(taskId, {
    pid: child.pid,
    type: args.analysis_type,
    started: new Date(),
    status: 'running'
  });

  return {
    task_id: taskId,
    status: 'launched',
    estimated_duration: estimateDuration(args.analysis_type)
  };
}
```

**2. `rforge_check_status` (1 hour)**
```typescript
// Check if background task is done
export async function checkStatus(args: {
  task_id: string;
}): Promise<StatusResult> {
  const meta = await loadTaskMeta(args.task_id);

  // Check if process still running
  const running = await isProcessRunning(meta.pid);

  if (!running) {
    // Check for results file
    const hasResults = await fileExists(`/tmp/rforge-${args.task_id}-results.json`);

    return {
      status: hasResults ? 'completed' : 'failed',
      duration: Date.now() - meta.started.getTime()
    };
  }

  return {
    status: 'running',
    progress: estimateProgress(meta)
  };
}
```

**3. `rforge_get_results` (1 hour)**
```typescript
// Get results from completed task
export async function getResults(args: {
  task_id: string;
}): Promise<AnalysisResults> {
  const resultsPath = `/tmp/rforge-${args.task_id}-results.json`;

  if (!await fileExists(resultsPath)) {
    throw new Error('Results not ready yet');
  }

  const results = await readJSON(resultsPath);

  // Cleanup
  await cleanup(args.task_id);

  return results;
}
```

**Deliverable:** Async R analysis capability

---

### Day 5-6: Claude Code Plugin (Orchestrator)

**Goal:** Build Claude Code plugin that orchestrates MCP calls

#### Plugin Structure:

**1. Create plugin directory** (30 min)
```bash
mkdir -p ~/.claude/plugins/rforge-orchestrator
cd ~/.claude/plugins/rforge-orchestrator
```

**2. Plugin manifest** (30 min)
```json
// plugin.json
{
  "name": "rforge-orchestrator",
  "version": "0.1.0",
  "description": "Auto-delegation orchestrator for RForge MCP tools",
  "agents": [
    {
      "name": "analyze",
      "description": "Automatically analyze R package changes and delegate to appropriate tools",
      "instructions": "agents/orchestrator.md"
    }
  ],
  "skills": [
    {
      "name": "analyze",
      "command": "rforge:analyze",
      "description": "Quick R package analysis with auto-delegation",
      "instructions": "skills/analyze.md"
    }
  ]
}
```

**3. Orchestrator Agent** (4 hours)
```markdown
<!-- agents/orchestrator.md -->
# RForge Analysis Orchestrator

You are the RForge orchestrator agent. When the user wants to analyze an R package change:

## Pattern Recognition

Analyze the user's request and match to patterns:

1. **Code Change** → Run: impact, tests, docs
2. **New Function** → Run: namespace, similar_code, docs
3. **Bug Fix** → Run: tests, regression
4. **Documentation** → Run: docs_drift, examples
5. **Release** → Run: health, cran, cascade

## Execution Strategy

### Quick Analysis (< 30 seconds)
Use fast tools for immediate feedback:
- rforge_quick_impact
- rforge_quick_tests
- rforge_quick_docs
- rforge_quick_health

### Thorough Analysis (2-5 minutes)
For deeper analysis, use background tools:
1. Launch: rforge_launch_analysis
2. Poll: rforge_check_status (every 10 sec)
3. Retrieve: rforge_get_results

## Parallel Execution

Make tool calls in parallel when possible:
```typescript
// Call these 3 tools simultaneously
await Promise.all([
  mcp.call('rforge_quick_impact', args),
  mcp.call('rforge_quick_tests', args),
  mcp.call('rforge_quick_docs', args)
]);
```

## Progress Display

Show user what's happening:
```
Analyzing RMediation changes...

[████████░░] Impact Analysis    80%  2 packages affected
[██████████] Test Coverage     100%  94% coverage ✓
[█████░░░░░] Documentation      50%  Checking vignettes...
```

## Results Synthesis

Combine results into coherent summary:
```
🎯 IMPACT: MEDIUM
  • 2 packages affected (mediate, sensitivity)
  • Estimated cascade: 4 hours

✅ QUALITY: EXCELLENT
  • Tests: 187/187 passing (94% coverage)
  • No failures detected

⚠️ MAINTENANCE: Minor updates needed
  • NEWS.md needs entry
  • Vignette has old example
```

## Tools Available

- `rforge_quick_impact` - Fast dependency impact
- `rforge_quick_tests` - Fast test status
- `rforge_quick_docs` - Fast doc check
- `rforge_quick_health` - Overall health
- `rforge_launch_analysis` - Background R analysis
- `rforge_check_status` - Poll background task
- `rforge_get_results` - Get background results
- `rforge_plan` - Generate implementation plan
```

**4. Analyze Skill** (2 hours)
```markdown
<!-- skills/analyze.md -->
# /rforge:analyze - Quick Package Analysis

Analyze R package changes with automatic tool delegation.

## Usage
```bash
/rforge:analyze "Update RMediation bootstrap algorithm"
```

## What it does
1. Auto-detects package from current directory
2. Recognizes task pattern (code change, bug fix, etc.)
3. Delegates to appropriate MCP tools in parallel
4. Synthesizes results into actionable summary
5. Suggests next steps

## Output
- Impact assessment (affected packages, effort estimate)
- Quality status (tests, coverage, CRAN)
- Maintenance items (docs, NEWS, vignettes)
- Recommended action plan

## Options
- `--quick` - Fast analysis only (< 30 sec)
- `--thorough` - Include background R analysis (2-5 min)
- `--package <path>` - Explicit package path
```

**Deliverable:** Working Claude Code plugin

---

### Day 7: Progress Dashboard (Plugin UI)

**Goal:** Add live progress display to orchestrator agent

#### Implementation:

**1. Create dashboard module** (3 hours)
```typescript
// plugins/rforge-orchestrator/lib/dashboard.ts
export class AnalysisDashboard {
  private tasks: Map<string, TaskStatus> = new Map();

  addTask(name: string, status: TaskStatus) {
    this.tasks.set(name, status);
  }

  updateProgress(name: string, progress: number) {
    const task = this.tasks.get(name);
    if (task) {
      task.progress = progress;
    }
  }

  render(): string {
    const lines = ["Analyzing RMediation changes...", ""];

    for (const [name, status] of this.tasks) {
      const bar = this.progressBar(status.progress);
      const emoji = status.status === 'done' ? '✓' : '...';

      lines.push(`${bar} ${name} ${emoji}`);
    }

    return lines.join('\n');
  }

  private progressBar(progress: number): string {
    const filled = Math.floor(progress / 10);
    const empty = 10 - filled;
    return `[${' '.repeat(filled)}█${' '.repeat(empty)}]`;
  }
}
```

**2. Integrate with orchestrator** (2 hours)
```markdown
<!-- Update agents/orchestrator.md -->

## Progress Display

Use the dashboard to show live progress:

```typescript
const dashboard = new AnalysisDashboard();

// Add tasks
dashboard.addTask('Impact Analysis', { status: 'running', progress: 0 });
dashboard.addTask('Test Coverage', { status: 'running', progress: 0 });
dashboard.addTask('Documentation', { status: 'running', progress: 0 });

// Show initial state
console.log(dashboard.render());

// Make parallel calls and update progress
const results = await Promise.all([
  mcp.call('rforge_quick_impact').then(r => {
    dashboard.updateProgress('Impact Analysis', 100);
    return r;
  }),
  // ...
]);

// Show final state
console.log(dashboard.render());
```
```

**Deliverable:** Live progress dashboard in Claude

---

### Day 8: Integration, Testing & Packaging

**Goal:** End-to-end testing, documentation, and initial packaging

#### Tasks:

**1. Integration tests** (3 hours)
```typescript
// Test orchestrator with real RMediation package
describe('RForge Orchestrator', () => {
  test('analyzes code change correctly', async () => {
    const result = await orchestrate({
      task: 'Update bootstrap algorithm',
      package: '/path/to/RMediation'
    });

    expect(result.pattern).toBe('code_change');
    expect(result.tools_called).toContain('rforge_quick_impact');
    expect(result.synthesis).toHaveProperty('impact');
  });

  test('runs tools in parallel', async () => {
    const start = Date.now();
    await orchestrate({ task: 'Update code', package: testPkg });
    const duration = Date.now() - start;

    // Should be < 15 sec (if sequential would be 30+ sec)
    expect(duration).toBeLessThan(15000);
  });
});
```

**2. Documentation** (2 hours)
- Update rforge-mcp README with new tools
- Create orchestrator plugin README
- Write usage examples

**3. Bug fixes** (1 hour)
- Fix any issues found
- Improve error handling
- Polish UX

**4. Create install.sh script** (1 hour)
```bash
# Create .github/install.sh in plugin repo
#!/bin/bash
set -e
# (Full script in RFORGE-PLUGIN-PACKAGING-BRAINSTORM.md)
```

**5. Test installation** (30 min)
```bash
# Test locally
bash install.sh

# Test from GitHub (after push)
curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
```

**Deliverable:** Complete working system + install script

---

## 🎯 Success Criteria

### Functional Requirements
✅ User types one command in Claude → auto-delegation happens
✅ 3-5 MCP tools called in parallel
✅ Live progress shown in Claude interface
✅ Results synthesized into clear summary
✅ Works for all 5 patterns
✅ Fast analysis: < 30 sec
✅ Thorough analysis: < 5 min

### MCP Server Requirements
✅ All new tools complete in < 10 sec (fast tools)
✅ Background tools launch and return immediately
✅ Tools are stateless and idempotent
✅ Error handling for missing R packages

### Plugin Requirements
✅ Pattern recognition accurate (80%+)
✅ Parallel execution working
✅ Progress dashboard updates
✅ Synthesis quality high
✅ ADHD-friendly UX

### Packaging Requirements
✅ Install script works (one-command install)
✅ Handles rforge-mcp dependency automatically
✅ Verifies installation success
✅ Clear next steps shown to user
✅ Works on macOS/Linux

---

## 📦 Dependencies

### RForge MCP Server (package.json)
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "execa": "^8.0.0"  // NEW - for spawning R processes
  }
}
```

### Claude Code Plugin
```json
{
  "dependencies": {
    "@anthropic/claude-sdk": "^1.0.0"  // For MCP calls
  }
}
```

### R Environment
- R >= 4.0.0
- devtools
- testthat
- covr

---

## 🔄 Workflow Example

### User Experience:

```
User: "Update RMediation bootstrap algorithm"

Claude (using rforge-orchestrator plugin):

🔍 Pattern recognized: CODE_CHANGE
📊 Delegating to 4 tools...

Analyzing...
[████████░░] Impact Analysis    80%  2 packages affected
[██████████] Test Coverage     100%  94% coverage ✓
[██████░░░░] Documentation      70%  Checking vignettes...
[████░░░░░░] Health Check       40%  Running checks...

✅ Analysis complete!

🎯 IMPACT: MEDIUM
  • 2 packages affected (mediate, sensitivity)
  • Estimated cascade: 4 hours over 2 days

✅ QUALITY: EXCELLENT
  • Tests: 187/187 passing (94% coverage)
  • CRAN: Clean, no warnings

⚠️ MAINTENANCE: 2 items
  • NEWS.md needs entry (auto-fixable)
  • Vignette example outdated (auto-fixable)

📋 NEXT STEPS:
  1. Implement bootstrap algorithm change (3 hours)
  2. Auto-fix documentation (5 min)
  3. Run cascade for dependent packages (4 hours)

Generate detailed plan? [Y/n]
```

---

## 🎨 Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│              Claude Code Session                     │
│                                                      │
│  User: "Update RMediation bootstrap"                │
│                                                      │
│  ┌──────────────────────────────────────────┐      │
│  │   RForge Orchestrator Plugin             │      │
│  │                                           │      │
│  │  1. Pattern Recognition (local)          │      │
│  │  2. Tool Selection (local)               │      │
│  │  3. Progress Dashboard (local)           │      │
│  │  4. Results Synthesis (local)            │      │
│  └───────────────┬──────────────────────────┘      │
│                  │                                   │
│                  │ Parallel MCP calls                │
│                  ▼                                   │
└──────────────────┼───────────────────────────────────┘
                   │
      ┌────────────┼────────────┬────────────┐
      │            │            │            │
      ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  MCP     │ │  MCP     │ │  MCP     │ │  MCP     │
│ rforge_  │ │ rforge_  │ │ rforge_  │ │ rforge_  │
│ quick_   │ │ quick_   │ │ quick_   │ │ quick_   │
│ impact   │ │ tests    │ │ docs     │ │ health   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
      │            │            │            │
      └────────────┴────────────┴────────────┘
                   │
                   ▼
            Results returned
            to orchestrator
```

---

## 🚀 Launch Checklist

**Day 8 Pre-Launch:**
- [ ] All 4 fast tools working (< 10 sec each)
- [ ] 3 async tools working (launch/status/results)
- [ ] Orchestrator plugin installed
- [ ] Pattern recognition tested
- [ ] Parallel execution verified
- [ ] Progress dashboard showing
- [ ] Synthesis quality good
- [ ] Documentation complete
- [ ] Install script created and tested

**Launch:**
- [ ] Publish rforge-mcp updates to npm
- [ ] Push plugin to GitHub (create repo if needed)
- [ ] Test install script from GitHub
- [ ] Test with real RMediation work
- [ ] Gather feedback
- [ ] Iterate

**Week 2 (Post-Launch):**
- [ ] Create Homebrew formula
- [ ] Add to data-wise/homebrew-tap
- [ ] Test Homebrew installation
- [ ] Update README with all install methods
- [ ] Announce on relevant channels

---

## 📊 Comparison: Original vs Revised Plan

| Aspect | Original Plan | Revised Plan |
|--------|--------------|--------------|
| **Language** | Python CLI | TypeScript MCP |
| **Architecture** | Standalone tool | MCP server + Claude plugin |
| **Agents** | Server-side background | Claude-side orchestration |
| **Progress** | Server TUI | Claude interface |
| **State** | Server manages | Stateless tools |
| **Execution** | Long-running server | Fast tool calls |
| **Integration** | New project | Extends existing rforge-mcp |
| **Packaging** | Not planned | Multi-channel (script/Homebrew/npm) |
| **Distribution** | Manual | One-command install |
| **Timeline** | 8 days | 8 days + packaging |
| **Value** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (uses existing!) |

---

## 💡 Key Insights

### Why This Approach is Better

1. **Leverages existing work** - RForge MCP already has 10 tools
2. **Follows MCP patterns** - Stateless, fast tools
3. **Claude does orchestration** - Better suited for it
4. **Simpler** - No need for complex server-side state
5. **More flexible** - Claude can adapt orchestration logic
6. **Faster to implement** - Building on solid foundation

### ADHD-Friendly Benefits

1. **Quick feedback** - Fast tools return in < 10 sec
2. **Visible progress** - Claude shows dashboard
3. **Incremental results** - See results as tools complete
4. **Interrupt-friendly** - Claude handles interruption
5. **Clear synthesis** - Results combined coherently

---

## 🔜 Next Steps

Ready to start implementation?

**Day 1 Tasks:**
1. Add `rforge_quick_impact` to src/tools/analysis/
2. Add `rforge_quick_tests` to src/tools/analysis/
3. Test both tools with RMediation
4. Update MCP server index.ts to export new tools

**Estimated:** 4-5 hours
**Deliverable:** 2 working fast analysis tools

Let's build this! 🚀

---

## 📦 Packaging & Distribution Strategy

### Plugin Distribution (Multi-Channel)

**Phase 1 (Week 1): Install Script** ⭐ PRIMARY
```bash
curl -fsSL https://rforge.dev/install.sh | bash
```

**What it does:**
1. Checks/installs rforge-mcp (if not present)
2. Downloads plugin from GitHub
3. Extracts to ~/.claude/plugins/rforge-orchestrator
4. Verifies installation
5. Shows next steps

**Why this approach:**
- One-command installation
- Handles dependencies automatically
- Works on macOS/Linux
- ADHD-friendly (minimal steps)

**Phase 2 (Week 2): Homebrew Formula** ⭐ SECONDARY
```bash
brew tap data-wise/rforge
brew install rforge-orchestrator-plugin
```

**Why add Homebrew:**
- macOS standard (matches aiterm distribution)
- Elegant update mechanism (brew upgrade)
- Dependency management built-in
- Already have data-wise/homebrew-tap repo

**Phase 3 (Month 2): Advanced**
- NPM package: `npm install -g @rforge/orchestrator-plugin`
- Update skill: `/rforge:update`
- Auto-update checker

**See:** `RFORGE-PLUGIN-PACKAGING-BRAINSTORM.md` for full analysis

---

**Generated:** 2025-12-21
**Updated:** 2025-12-21 (added packaging strategy)
**Location:** ~/projects/dev-tools/mcp-servers/rforge/
**Architecture:** TypeScript MCP + Claude Code Plugin
**Timeline:** 8 days (Dec 22-30) + packaging (ongoing)
