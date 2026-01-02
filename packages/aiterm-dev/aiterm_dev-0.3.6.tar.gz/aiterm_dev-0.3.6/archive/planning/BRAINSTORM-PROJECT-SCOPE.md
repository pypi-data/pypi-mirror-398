# aiterm Project Scope Analysis & Redundancy Review

**Generated:** 2025-12-19
**Context:** aiterm v0.1.0 complete, planning v0.2.0+

---

## Executive Summary

**Finding:** aiterm has **significant overlap** with 3 existing projects but offers **unique value** in its specific niche. Recommend **consolidation strategy** rather than abandonment.

**Key Overlaps:**
1. **zsh-configuration** - ZSH workflow management, ADHD helpers (70% overlap)
2. **zsh-claude-workflow** - Claude context detection (50% overlap)
3. **iterm2-context-switcher** - Terminal profile switching (100% overlap - this IS the old version!)

**Unique Value of aiterm:**
- Python-based (more maintainable than ZSH scripts)
- Cross-terminal potential (not just iTerm2)
- Claude Code-specific optimizations (hooks, MCP, settings management)
- Installable CLI tool (pip/PyPI vs scattered scripts)

---

## Detailed Analysis

### 1. aiterm Core Purpose

**What aiterm DOES:**
- Terminal profile switching based on project context (iTerm2 primarily)
- Claude Code settings/auto-approvals management
- Context detection (8 project types)
- StatusLine customization (planned v0.2)
- Hook management (planned v0.2)
- MCP server integration (planned v0.2)

**Target Users:**
- Primary: DT (power user, R developer, ADHD workflows)
- Secondary: Public (developers using Claude Code + terminal customization)

**Tech Stack:**
- Python 3.10+ (Typer CLI framework)
- iTerm2 escape sequences + Python API
- Rich terminal output
- PyPI distribution

---

### 2. Project Overlap Matrix

| Feature | aiterm | zsh-config | zsh-claude | iterm2-switcher | Verdict |
|---------|--------|------------|------------|-----------------|---------|
| **Terminal profile switching** | ✅ Core | ❌ | ❌ | ✅ **DUPLICATE** | aiterm replaces old version |
| **Context detection (8 types)** | ✅ Core | ✅ (183 aliases) | ✅ (proj-type) | ✅ Old version | **REDUNDANT** - 3 implementations! |
| **Claude Code settings** | ✅ Core | ❌ | ❌ | ❌ | **UNIQUE** |
| **Hook management** | 🟡 v0.2 | ❌ | ❌ | ❌ | **UNIQUE** |
| **MCP server mgmt** | 🟡 v0.2 | ❌ | ❌ | ❌ | **UNIQUE** |
| **ADHD workflows** | ❌ | ✅ **CORE** (108 funcs) | ❌ | ❌ | zsh-config wins |
| **Session management** | ❌ | ✅ (work/finish) | ❌ | ❌ | zsh-config wins |
| **Claude context files** | ❌ | ❌ | ✅ **CORE** (CLAUDE.md) | ❌ | zsh-claude wins |
| **CLAUDE.md templates** | ❌ | ❌ | ✅ (3 templates) | ❌ | zsh-claude wins |
| **Project picker (fzf)** | ❌ | ✅ (pp command) | ❌ | ❌ | zsh-config wins |
| **Desktop app UI** | ❌ | 🟡 In progress (Electron) | ❌ | ❌ | zsh-config unique |
| **Alias system (183+)** | ❌ | ✅ **MASSIVE** | ❌ | ❌ | zsh-config wins |
| **Cross-terminal support** | 🟡 Future | ❌ (macOS only) | ❌ | ❌ (iTerm2 only) | aiterm unique goal |
| **PyPI distribution** | ✅ Ready | ❌ | ❌ | ❌ | aiterm unique |
| **StatusLine builder** | 🟡 v0.2 | ❌ | ❌ | ❌ | **UNIQUE** |

---

## 3. Redundancy Deep Dive

### Problem: Context Detection (3 Implementations!)

**Implementation 1: iterm2-context-switcher (OLD - aiterm's predecessor)**
- Location: `~/projects/dev-tools/iterm2-context-switcher/zsh/iterm2-integration.zsh`
- Lines: 186
- Status: **DEPRECATED** (aiterm replaces this)
- Detection: R pkg, Python, Node, Quarto, Production, AI-Session, MCP, Dev-Tools

**Implementation 2: zsh-claude-workflow**
- Location: `~/projects/dev-tools/zsh-claude-workflow/lib/project-detector.sh`
- Purpose: Detect project type for CLAUDE.md template selection
- Detection: R package, Quarto, research, dev-tool
- Status: **ACTIVE** (used by `proj-type`, `proj-info`, `claude-ctx`)

**Implementation 3: zsh-configuration**
- Location: `~/.config/zsh/functions/adhd-helpers.zsh` (3034 lines!)
- Purpose: ADHD workflow system (work/finish/dash/pp)
- Detection: Embedded in `work` command, project-specific dashboards
- Status: **ACTIVE** (primary workflow system)

**Implementation 4: aiterm (NEW)**
- Location: `~/projects/dev-tools/aiterm/src/aiterm/context/detector.py`
- Purpose: Terminal profile switching
- Detection: 8 types (Python implementation)
- Status: **ACTIVE** (v0.1.0 released)

**Reality Check:**
You have **4 systems** detecting the same 8 project types in 3 different languages (ZSH, Python) for 3 different purposes!

---

## 4. Overlap Analysis by Project

### A. zsh-configuration (MASSIVE OVERLAP - 70%)

**What it does:**
- 183 aliases + 108 functions for developer productivity
- ADHD-optimized workflows (work/finish/dash/pp/js/why/win)
- Session management with automatic tracking
- Desktop app UI (Electron - in progress)
- Multi-editor support (Emacs, VS Code, Cursor, RStudio)
- Cross-project integration (shared project-detector.zsh)

**Overlap with aiterm:**
- ✅ Context detection (work command embeds detection)
- ✅ Project type awareness (dashboards per project type)
- ✅ Workflow automation (similar to terminal profile switching)
- ❌ Different focus: zsh-config = ADHD workflows, aiterm = terminal+Claude optimization

**Recommendation:**
- **Keep both** - complementary purposes
- **aiterm should integrate WITH zsh-config** (not replace)
- Example: `work` command could call `aiterm switch` to set terminal profile

---

### B. zsh-claude-workflow (MODERATE OVERLAP - 50%)

**What it does:**
- Project type detection for Claude context
- Gather CLAUDE.md files and project structure
- Template system for creating CLAUDE.md
- Commands: proj-type, proj-info, claude-ctx, claude-init

**Overlap with aiterm:**
- ✅ Project type detection (duplicate implementation!)
- ✅ Claude Code integration goal (different aspects)
- ❌ Different focus: zsh-claude = context files, aiterm = settings/hooks/terminal

**Recommendation:**
- **Merge context detection** - use aiterm's Python implementation
- **Keep zsh-claude for CLAUDE.md management**
- **aiterm v0.2 should add:** `aiterm claude init` (create CLAUDE.md from template)
- **Integration:** zsh-claude could call `aiterm context detect` instead of shell scripts

---

### C. iterm2-context-switcher (100% OVERLAP - OLD VERSION!)

**What it does:**
- Terminal profile switching (iTerm2 escape sequences)
- Context detection (8 types)
- Status bar variables

**Overlap with aiterm:**
- ✅ **COMPLETE DUPLICATE** - this is literally what aiterm replaced!

**Recommendation:**
- **ARCHIVE iterm2-context-switcher** - mark as deprecated
- **Add README redirect** to aiterm
- **Migration guide** for any remaining users
- **aiterm IS the new version** (Python rewrite)

---

## 5. Strategic Options

### Option A: Consolidate Everything into aiterm ⚡ QUICK WIN

**Approach:**
1. Archive iterm2-context-switcher (✅ aiterm replaces it)
2. Extract project-detector from zsh-claude → make it a shared library
3. Have aiterm, zsh-claude, and zsh-config all use the same detector
4. Add CLAUDE.md management to aiterm v0.2

**Pros:**
- Single source of truth for context detection
- Python-based (more maintainable)
- PyPI installable (easier distribution)

**Cons:**
- Requires refactoring zsh-claude and zsh-config
- Python dependency for shell scripts (not ideal)

**Effort:** 🔧 Medium (2-3 days)

---

### Option B: Keep Projects Separate, Define Boundaries 🏗️ STRATEGIC

**Approach:**
1. **aiterm** = Terminal optimization + Claude Code settings/hooks/MCP
2. **zsh-config** = ADHD workflows + session mgmt + aliases (keep as-is)
3. **zsh-claude** = CLAUDE.md management + context files (keep as-is)
4. **Shared library:** Extract `project-detector` as standalone tool

**Clear Boundaries:**
```
┌─────────────────────────────────────────┐
│ zsh-configuration                       │
│ - ADHD workflows (work/finish/dash)     │
│ - 183 aliases + 108 functions           │
│ - Desktop app (Electron)                │
│ - Session tracking                      │
└─────────────────────────────────────────┘
                ↓ calls
┌─────────────────────────────────────────┐
│ aiterm                                   │
│ - Terminal profile switching            │
│ - Claude Code settings management       │
│ - Hook management (v0.2)                │
│ - MCP integration (v0.2)                │
│ - StatusLine builder (v0.2)             │
└─────────────────────────────────────────┘
                ↓ uses
┌─────────────────────────────────────────┐
│ zsh-claude-workflow                     │
│ - CLAUDE.md templates                   │
│ - Context file gathering                │
│ - Claude context display                │
└─────────────────────────────────────────┘
                ↓ all use
┌─────────────────────────────────────────┐
│ project-detector (SHARED LIBRARY)       │
│ - Context detection (8 types)           │
│ - Git status                            │
│ - Project metadata                      │
└─────────────────────────────────────────┘
```

**Pros:**
- Respects existing investments (zsh-config has 5000+ lines!)
- Clear separation of concerns
- Each tool focuses on its strength

**Cons:**
- Slight duplication remains
- Users need multiple tools
- Integration overhead

**Effort:** 🔧 Medium (1-2 weeks to create shared library)

---

### Option C: Merge aiterm Features into zsh-configuration 🔄 SIMPLIFY

**Approach:**
1. Add Claude Code settings management to zsh-config
2. Add terminal profile switching to zsh-config
3. Archive aiterm as a failed experiment

**Pros:**
- Single mega-tool
- All ADHD workflows + terminal optimization in one place

**Cons:**
- zsh-config is already MASSIVE (3000+ lines in adhd-helpers alone!)
- Loses Python benefits (type safety, testing, distribution)
- Harder to maintain as complexity grows
- Not pip-installable (barrier for external users)

**Effort:** 🏗️ Large (3-4 weeks)

---

### Option D: Kill aiterm, Use Existing Tools 💀 NUCLEAR

**Approach:**
1. Archive aiterm
2. Keep using zsh-config + zsh-claude
3. Accept duplication

**Pros:**
- No refactoring needed
- Existing tools work

**Cons:**
- Wasted v0.1.0 effort (51 tests, 83% coverage, full docs!)
- No solution for Claude Code hook/MCP management
- Terminal profile switching lost (iterm2-switcher deprecated)

**Effort:** ⚡ Quick (1 day to archive)

---

## 6. Recommendation: Hybrid Approach (Best of Both Worlds)

### Strategy: "aiterm as Foundation, Integration with Ecosystem"

**Phase 1: Immediate (v0.1.0 - DONE!)**
1. ✅ Keep aiterm v0.1.0 as-is (terminal switching + Claude settings)
2. ✅ Archive iterm2-context-switcher (redirect to aiterm)

**Phase 2: Integration (v0.2.0 - Next 2 weeks)**
3. Create `project-detector` as shared CLI tool
   - `detect-project-type` command (returns JSON)
   - Used by aiterm, zsh-claude, zsh-config
   - Single source of truth
4. aiterm adds:
   - Hook management (`aiterm claude hooks list|install|test`)
   - MCP server integration (`aiterm mcp list|test|install`)
   - CLAUDE.md management (`aiterm claude init` - borrowed from zsh-claude)

**Phase 3: Cross-Project Integration (v0.3.0)**
5. zsh-config `work` command calls `aiterm switch` automatically
6. zsh-claude `claude-init` uses `aiterm claude init` under the hood
7. All three projects use shared `project-detector`

**Phase 4: Specialization (v1.0.0)**
8. **aiterm** = Terminal + Claude Code optimization (PyPI package, 10+ users)
9. **zsh-config** = ADHD workflows + Desktop app (your personal system)
10. **zsh-claude** = CLAUDE.md management (lightweight, focused)

### Why This Works

**Preserves Strengths:**
- aiterm: Python (testable, distributable, cross-platform potential)
- zsh-config: ADHD workflows (massive investment, works well)
- zsh-claude: CLAUDE.md templates (simple, focused)

**Reduces Duplication:**
- Shared `project-detector` tool (DRY principle)
- Cross-calling (work → aiterm switch)
- Unified context detection

**Growth Path:**
- aiterm can grow to multi-terminal, public users
- zsh-config stays personal, ADHD-optimized
- All three benefit from shared foundation

---

## 7. Concrete Next Steps

### Immediate (Week 1)
- [ ] **Archive iterm2-context-switcher**
  - Add README: "DEPRECATED - Use aiterm instead"
  - Create migration guide
  - Mark repo as archived on GitHub

### Short-term (Week 2-3) - v0.2.0
- [ ] **Extract shared project-detector**
  - Create `~/projects/dev-tools/project-detector/`
  - CLI: `detect-project-type [path]` → JSON output
  - Used by aiterm, zsh-claude, zsh-config
  - 8 project types + extensible

- [ ] **aiterm v0.2.0 features**
  - Hook management (use existing templates from IDEAS.md)
  - MCP integration (foundation in zsh-configuration/zsh/functions/mcp-utils.zsh)
  - CLAUDE.md init (borrow templates from zsh-claude-workflow)

- [ ] **Integration points**
  - zsh-config `work` command calls `aiterm switch`
  - Document how tools work together

### Medium-term (Month 2) - v0.3.0+
- [ ] **Cross-project refactoring**
  - zsh-claude uses aiterm for detection
  - zsh-config uses aiterm for terminal switching
  - All use shared project-detector

- [ ] **Public release prep**
  - PyPI package for aiterm
  - Homebrew formula
  - External user testing (10+ users)

---

## 8. Decision Matrix

| Criterion | Option A: Consolidate | Option B: Boundaries | Option C: Merge to zsh | Option D: Kill aiterm | **HYBRID** |
|-----------|----------------------|---------------------|----------------------|---------------------|------------|
| **Reduces duplication** | ✅✅✅ High | ✅✅ Medium | ✅✅✅ High | ❌ None | ✅✅ Medium-High |
| **Preserves existing work** | ✅✅ Good | ✅✅✅ Excellent | ❌ Poor | ❌ Terrible | ✅✅✅ Excellent |
| **Maintainability** | ✅✅✅ Python | ✅✅ Clear boundaries | ❌ Monolith | ✅ Fewer projects | ✅✅✅ Best of both |
| **Public distribution** | ✅✅✅ PyPI | ✅✅ aiterm only | ❌ ZSH scripts | ❌ None | ✅✅✅ PyPI ready |
| **ADHD workflows** | ⚠️ Needs port | ✅✅✅ Intact | ✅✅✅ Intact | ✅✅✅ Intact | ✅✅✅ Intact |
| **Effort required** | 🔧 Medium (2-3 weeks) | 🔧 Medium (1-2 weeks) | 🏗️ Large (3-4 weeks) | ⚡ Quick (1 day) | 🔧 Medium (2-3 weeks) |
| **Risk** | ⚠️ Medium | ✅ Low | ⚠️ High | ⚠️ High | ✅ Low |
| **Cross-platform potential** | ✅✅✅ Yes | ✅✅ aiterm only | ❌ macOS/ZSH only | ❌ None | ✅✅✅ Yes |

**Winner:** 🏆 **HYBRID APPROACH**

---

## 9. Success Metrics

### v0.2.0 Success (2 weeks)
- [ ] project-detector shared library created
- [ ] aiterm hooks management working
- [ ] aiterm MCP integration working
- [ ] zsh-config `work` → `aiterm switch` integration
- [ ] iterm2-context-switcher archived

### v1.0.0 Success (3 months)
- [ ] 10+ external aiterm users
- [ ] PyPI package published
- [ ] Zero duplication in context detection (shared library)
- [ ] All three projects integrate cleanly
- [ ] Documentation shows how tools work together

---

## 10. Final Recommendation

**DO NOT kill aiterm.** It has unique value:
1. **Python-based** (better than 3000-line shell scripts)
2. **Claude Code optimization** (hooks, MCP, settings - no other tool does this)
3. **Public distribution ready** (PyPI - zsh-config is personal)
4. **Cross-platform potential** (multi-terminal support coming)

**DO create boundaries:**
1. **aiterm** = Terminal + Claude Code optimization
2. **zsh-config** = ADHD workflows + session management
3. **zsh-claude** = CLAUDE.md file management
4. **Shared library** = project-detector (DRY)

**DO integrate:**
- `work` → `aiterm switch` (auto-profile switching)
- `aiterm claude init` → uses zsh-claude templates
- All tools → shared `project-detector`

**Timeline:**
- Week 1: Archive iterm2-context-switcher ✅
- Week 2-3: v0.2.0 (hooks + MCP + shared detector)
- Month 2-3: v0.3.0 (cross-integration)
- Month 4+: v1.0.0 (public release)

---

## Appendix: Questions to Consider

1. **Should project-detector be in Python or ZSH?**
   - Python: Better for aiterm users (pip install)
   - ZSH: Better for zsh-config/zsh-claude (no Python dependency)
   - **Recommendation:** Python CLI that outputs JSON (both can use it)

2. **Should aiterm absorb zsh-claude entirely?**
   - Yes: Fewer projects to maintain
   - No: zsh-claude is simple, focused, works
   - **Recommendation:** Keep separate, share code via library

3. **What about the Desktop app in zsh-config?**
   - Could it replace aiterm CLI?
   - No - different audiences (GUI vs CLI)
   - They can coexist

4. **Should obsidian-cli-ops integrate too?**
   - No - different domain (knowledge management)
   - Already has 394 tests, active development
   - Keep focused on Obsidian

---

**Last Updated:** 2025-12-19
**Status:** 🟡 Awaiting decision on hybrid approach
**Next Action:** Discuss with DT, choose strategy, execute Week 1 tasks
