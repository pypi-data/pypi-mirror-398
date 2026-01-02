# Integration & Overlap Removal Brainstorm

**Generated:** 2025-12-19
**Context:** aiterm v0.1.0 complete, planning consolidation strategy

**Goals:**
1. Integrate zsh-claude-workflow → zsh-configuration
2. Remove overlap between zsh-configuration and aiterm
3. Create clear boundaries and specialization

---

## Current State Analysis

### zsh-claude-workflow
- **Size:** ~5,572 lines across 15 files
- **Commands:** 20 commands (proj-type, claude-ctx, claude-init, etc.)
- **Templates:** 3 CLAUDE.md templates (R pkg, Quarto, research)
- **Core Libraries:** project-detector.sh, claude-context.sh, core.sh
- **Purpose:** Project type detection + CLAUDE.md management
- **Status:** Active, working well, simple and focused

### zsh-configuration
- **Size:** ~15,000+ lines across 18+ function files
- **Commands:** 183 aliases + 108 functions
- **Core Systems:**
  - ADHD helpers (3034 lines - js, why, win, work, finish)
  - Smart dispatchers (841 lines - pb, pv, pt)
  - Multi-editor quadrants (Emacs, VS Code, Cursor, RStudio)
  - Session management (work/finish with tracking)
- **Purpose:** ADHD-optimized developer workflows
- **Status:** Active, massive investment, core productivity system

### aiterm
- **Size:** ~2,000 lines Python + 51 tests
- **Commands:** 15+ CLI commands (detect, switch, profile, claude settings/approvals)
- **Core Features:**
  - Terminal profile switching (iTerm2 escape sequences)
  - Context detection (8 types, Python)
  - Claude Code settings management
  - Auto-approval presets (8 presets)
- **Purpose:** Terminal optimization + Claude Code integration
- **Status:** v0.1.0 complete, 83% test coverage, docs deployed

### Overlap Summary
```
┌────────────────────────────────────────────────────────┐
│ OVERLAP: Context Detection (3 implementations!)       │
├────────────────────────────────────────────────────────┤
│ 1. zsh-claude: project-detector.sh (detects 4 types)  │
│ 2. zsh-config: embedded in work/adhd-helpers          │
│ 3. aiterm: detector.py (detects 8 types)              │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ OVERLAP: Claude Code Integration (2 implementations)  │
├────────────────────────────────────────────────────────┤
│ 1. zsh-claude: CLAUDE.md templates, claude-ctx        │
│ 2. aiterm: settings management, hooks (planned)       │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ OVERLAP: Project Type Awareness (everywhere!)         │
├────────────────────────────────────────────────────────┤
│ 1. zsh-claude: proj-type command                      │
│ 2. zsh-config: work command detects type              │
│ 3. aiterm: context detect command                     │
└────────────────────────────────────────────────────────┘
```

---

## PART 1: Integrate zsh-claude → zsh-config

### Option 1A: Full Merge (Copy Everything) ⚡ QUICK WIN

**Approach:**
1. Copy all zsh-claude commands → `~/.config/zsh/functions/claude-integration.zsh`
2. Copy templates → `~/.config/zsh/templates/claude/`
3. Copy libraries → `~/.config/zsh/lib/` (new directory)
4. Archive zsh-claude-workflow repo
5. Update PATH/aliases in zsh-config

**Structure After Integration:**
```
~/.config/zsh/
├── functions/
│   ├── adhd-helpers.zsh          (existing - 3034 lines)
│   ├── smart-dispatchers.zsh     (existing - 841 lines)
│   ├── claude-integration.zsh    (NEW - from zsh-claude)
│   └── ... (13+ other files)
├── lib/                           (NEW)
│   ├── project-detector.sh        (from zsh-claude)
│   ├── claude-context.sh          (from zsh-claude)
│   └── core.sh                    (from zsh-claude)
├── templates/                     (NEW)
│   └── claude/
│       ├── CLAUDE-rpkg.md
│       ├── CLAUDE-quarto.md
│       └── CLAUDE-research.md
└── .zshrc                         (updated imports)
```

**Commands Available After Merge:**
- `proj-type` - Detect project type ✅
- `claude-ctx` - Show Claude context files ✅
- `claude-init` - Create CLAUDE.md from template ✅
- `claude-show` - Display current CLAUDE.md ✅
- `proj-claude` - Open Claude Code with context ✅
- All existing zsh-config commands (183 aliases, 108 functions) ✅

**Pros:**
- ✅ Single source for all ZSH workflows
- ✅ No external dependencies (self-contained)
- ✅ Simpler mental model (one project, not three)
- ✅ Can share code between commands easily

**Cons:**
- ❌ zsh-config becomes even larger (15K → 20K+ lines)
- ❌ Loses focused zsh-claude identity
- ❌ Harder to extract/share just Claude features

**Effort:** ⚡ Quick (4-6 hours)

**Steps:**
1. Create `~/.config/zsh/lib/` directory
2. Copy `zsh-claude-workflow/lib/*.sh` → `~/.config/zsh/lib/`
3. Create `~/.config/zsh/functions/claude-integration.zsh`
4. Copy all command logic from `zsh-claude-workflow/commands/`
5. Create `~/.config/zsh/templates/claude/`
6. Copy templates
7. Update `.zshrc` to source new files
8. Test all commands
9. Archive zsh-claude-workflow with redirect README

---

### Option 1B: Selective Merge (Commands Only) 🎯 FOCUSED

**Approach:**
1. Copy ONLY the 20 commands → zsh-config functions
2. Keep templates in zsh-claude repo (symlink from zsh-config)
3. Keep libraries as shared (symlink)
4. zsh-claude becomes a "library" for zsh-config

**Structure After Integration:**
```
~/.config/zsh/
├── functions/
│   ├── claude-integration.zsh    (NEW - commands only)
│   └── ...
├── lib/                           (symlinks)
│   ├── project-detector.sh → ~/projects/dev-tools/zsh-claude-workflow/lib/project-detector.sh
│   ├── claude-context.sh   → ~/projects/dev-tools/zsh-claude-workflow/lib/claude-context.sh
│   └── core.sh             → ~/projects/dev-tools/zsh-claude-workflow/lib/core.sh
└── templates/                     (symlinks)
    └── claude/ → ~/projects/dev-tools/zsh-claude-workflow/templates/

~/projects/dev-tools/zsh-claude-workflow/  (KEPT - becomes library)
├── lib/                           (shared via symlinks)
├── templates/                     (shared via symlinks)
└── README.md                      (updated: "Library for zsh-config")
```

**Pros:**
- ✅ Preserves zsh-claude as shareable library
- ✅ Can extract Claude features for other users
- ✅ Changes to templates/libs benefit both
- ✅ Smaller footprint in zsh-config

**Cons:**
- ❌ Symlink complexity
- ❌ Two projects to maintain (sort of)
- ❌ Confusing mental model (is it merged or not?)

**Effort:** 🔧 Medium (1 day)

---

### Option 1C: Hybrid (Commands in zsh-config, Library Separate) 🏗️ ARCHITECTURAL

**Approach:**
1. Move commands → zsh-config
2. Extract shared libraries → NEW standalone project: `claude-dev-tools`
3. Both zsh-config AND aiterm use `claude-dev-tools`
4. Archive zsh-claude-workflow

**Structure After Integration:**
```
~/projects/dev-tools/claude-dev-tools/  (NEW - shared library)
├── lib/
│   ├── project-detector.sh        (detects 8+ types - JSON output)
│   ├── claude-context.sh          (gathers CLAUDE.md files)
│   └── core.sh                    (utilities)
├── templates/
│   └── claude/                    (CLAUDE.md templates)
└── bin/
    └── detect-project-type        (CLI wrapper for detector)

~/.config/zsh/
├── functions/
│   ├── claude-integration.zsh    (uses claude-dev-tools)
│   └── ...
└── lib/ → ~/projects/dev-tools/claude-dev-tools/lib/  (symlink)

~/projects/dev-tools/aiterm/
├── src/aiterm/
│   └── context/
│       └── detector.py            (calls detect-project-type CLI)
```

**Pros:**
- ✅ DRY principle (single source of truth)
- ✅ Both ZSH and Python can use same detector
- ✅ Shareable with community
- ✅ Clear separation of concerns

**Cons:**
- ❌ New project to maintain
- ❌ More complexity
- ❌ CLI wrapper overhead

**Effort:** 🏗️ Large (2-3 days)

---

### ⭐ RECOMMENDATION for Part 1: **Option 1A (Full Merge)**

**Why:**
- Simplest approach (4-6 hours)
- You already maintain zsh-config actively
- zsh-claude is small enough to absorb (5K lines)
- Reduces cognitive load (one less project)
- ADHD-friendly (fewer repos to remember)

**Implementation Plan:**
```bash
# Week 1, Day 1-2
1. Create directories in zsh-config
2. Copy files (lib, commands, templates)
3. Update .zshrc imports
4. Test all 20 commands
5. Archive zsh-claude-workflow
6. Update documentation

# Result:
- zsh-config has 200+ commands (183 existing + 20 from zsh-claude)
- Single source for all ZSH workflows
- zsh-claude archived with redirect
```

---

## PART 2: Remove Overlap Between zsh-config and aiterm

### The Core Question: What Should Each Tool Do?

**Current Overlap:**
1. Context detection (both do it)
2. Project type awareness (both do it)
3. Terminal optimization (aiterm does it, zsh-config could do it)
4. Claude Code integration (both touch it)

**Key Insight:** They serve **different user types**:
- **zsh-config** = DT's personal ADHD productivity system (ZSH scripts)
- **aiterm** = Public tool for terminal + Claude Code optimization (Python, PyPI)

---

### Option 2A: aiterm as CLI for zsh-config 🔗 INTEGRATION

**Approach:**
1. zsh-config remains the "source of truth" for YOUR workflows
2. aiterm becomes the "installable CLI" for PUBLIC users
3. aiterm's Python implementation is the "backend" for zsh-config commands

**Division of Labor:**
```
┌─────────────────────────────────────────────────────────┐
│ zsh-config (Your Personal System)                      │
├─────────────────────────────────────────────────────────┤
│ - ADHD workflows (js, why, win, work, finish)          │
│ - Session management                                    │
│ - Dashboards (dash, tst, rst)                          │
│ - 183 aliases + 108 functions                          │
│ - Claude integration commands (from zsh-claude)        │
│ - Desktop app (Electron - in progress)                 │
│                                                         │
│ CALLS aiterm for:                                      │
│ - Terminal profile switching (aiterm switch)           │
│ - Context detection (aiterm detect --json)             │
│ - Claude settings (aiterm claude settings show)        │
└─────────────────────────────────────────────────────────┘
                        ↓ uses
┌─────────────────────────────────────────────────────────┐
│ aiterm (Public Tool - Python, PyPI)                    │
├─────────────────────────────────────────────────────────┤
│ - Terminal profile switching (iTerm2, Warp, Alacritty) │
│ - Context detection (8+ types, JSON output)            │
│ - Claude Code settings management                       │
│ - Hook management (v0.2)                               │
│ - MCP server integration (v0.2)                        │
│ - StatusLine builder (v0.2)                            │
│ - CLAUDE.md init (borrowed templates from zsh-claude)  │
│                                                         │
│ CAN BE USED BY:                                        │
│ - External users (pip install aiterm)                  │
│ - Your zsh-config (calls aiterm CLI)                   │
│ - Other shell configs (bash, fish)                     │
└─────────────────────────────────────────────────────────┘
```

**Integration Points:**

**1. `work` command calls `aiterm switch`**
```zsh
# In ~/.config/zsh/functions/adhd-helpers.zsh

work() {
    local project=$1
    cd ~/projects/$project

    # Use aiterm for terminal profile switching
    if command -v aiterm &>/dev/null; then
        aiterm switch --quiet
    fi

    # Rest of work command logic (session tracking, etc.)
    # ...
}
```

**2. Context detection uses aiterm**
```zsh
# In ~/.config/zsh/functions/claude-integration.zsh

proj-type() {
    if command -v aiterm &>/dev/null; then
        # Use aiterm's Python implementation (more reliable)
        aiterm detect --json | jq -r '.type'
    else
        # Fallback to shell implementation
        _detect_project_type_shell
    fi
}
```

**3. Claude settings management delegated**
```zsh
claude-approvals() {
    if command -v aiterm &>/dev/null; then
        aiterm claude approvals "$@"
    else
        echo "Install aiterm for Claude settings management: pip install aiterm"
    fi
}
```

**Pros:**
- ✅ Clear separation (personal vs public)
- ✅ zsh-config uses best-of-breed aiterm features
- ✅ aiterm benefits from zsh-config's ADHD insights
- ✅ No duplication (aiterm is the implementation)
- ✅ External users can `pip install aiterm` independently

**Cons:**
- ❌ zsh-config depends on aiterm (Python dependency)
- ❌ Complexity (two projects talking to each other)
- ❌ aiterm must stay backward compatible for zsh-config

**Effort:** 🔧 Medium (3-4 days)

**Steps:**
1. aiterm v0.2: Add `--json` output to all commands
2. Update zsh-config commands to call `aiterm` when available
3. Keep shell fallbacks for when aiterm not installed
4. Test integration thoroughly
5. Document the architecture

---

### Option 2B: Complete Separation (No Overlap) 🎯 FOCUSED

**Approach:**
1. Remove ALL context detection from zsh-config (delegate to aiterm)
2. Remove ALL terminal profile logic from zsh-config (delegate to aiterm)
3. zsh-config focuses ONLY on ADHD workflows + session management
4. aiterm focuses ONLY on terminal + Claude Code optimization

**Division of Labor:**
```
zsh-config ONLY does:
- ADHD workflows (js, why, win)
- Session management (work, finish, dash)
- Aliases (183 shortcuts)
- Desktop app UI

zsh-config DOES NOT do:
- Context detection (removed - use aiterm)
- Terminal profiles (removed - use aiterm)
- Claude settings (removed - use aiterm)

aiterm ONLY does:
- Terminal profile switching
- Context detection
- Claude Code integration (settings, hooks, MCP)
- StatusLine builder

aiterm DOES NOT do:
- ADHD workflows (that's zsh-config)
- Session tracking (that's zsh-config)
- Aliases (that's zsh-config)
```

**How They Integrate:**
- zsh-config `work` command REQUIRES aiterm to be installed
- `work` → calls `aiterm switch` (no fallback)
- User installs both: `pip install aiterm` + zsh-config setup

**Pros:**
- ✅ Crystal clear boundaries
- ✅ Zero overlap
- ✅ Each tool does ONE thing well
- ✅ Easy to explain ("aiterm = terminal, zsh-config = workflows")

**Cons:**
- ❌ zsh-config REQUIRES aiterm (hard dependency)
- ❌ Users must install both
- ❌ No graceful degradation if aiterm missing

**Effort:** 🏗️ Large (1 week)

**Steps:**
1. Remove context detection from zsh-config (delete code)
2. Update all commands to call `aiterm detect`
3. Add dependency check to zsh-config install script
4. Update documentation (clear requirements)
5. Test on fresh machine

---

### Option 2C: Keep Overlap, Define Primary Owner 🔄 PRAGMATIC

**Approach:**
1. Accept that some overlap is OKAY
2. Define "primary owner" for each feature
3. Less-primary tool can have simplified version OR call primary tool

**Primary Ownership:**
```
FEATURE                          PRIMARY OWNER    SECONDARY
─────────────────────────────────────────────────────────────
Context detection                aiterm          zsh-config (calls aiterm)
Terminal profile switching       aiterm          zsh-config (calls aiterm)
Claude Code settings             aiterm          -
Claude Code hooks                aiterm          -
MCP integration                  aiterm          -
StatusLine builder               aiterm          -
CLAUDE.md management            zsh-config       aiterm (v0.2 - uses zsh templates)
ADHD workflows                   zsh-config       -
Session management               zsh-config       -
Aliases (183)                    zsh-config       -
Desktop app                      zsh-config       -
Project picker (pp, fzf)         zsh-config       -
```

**Rules:**
1. If feature has primary owner, use that implementation
2. Secondary can have SIMPLE version as fallback
3. Primary owner maintains comprehensive docs

**Example - Context Detection:**
- **Primary:** aiterm (Python, tested, JSON output)
- **Secondary:** zsh-config has shell fallback for when aiterm not installed
- **Rule:** If aiterm available, use it. Otherwise, basic shell version.

**Pros:**
- ✅ Pragmatic (acknowledges reality)
- ✅ Graceful degradation
- ✅ No hard dependencies
- ✅ Best-of-breed (use best implementation)

**Cons:**
- ❌ Some overlap remains
- ❌ Maintenance burden (keep both in sync)
- ❌ Confusing (which version am I using?)

**Effort:** 🔧 Medium (2-3 days)

---

### ⭐ RECOMMENDATION for Part 2: **Option 2A (aiterm as CLI for zsh-config)**

**Why:**
- Best balance of DRY principle and practicality
- zsh-config benefits from aiterm's Python robustness
- aiterm gets real-world usage from your workflows
- External users can use aiterm standalone
- Graceful degradation (fallbacks when aiterm missing)

**Implementation Plan:**
```bash
# Week 2-3
1. aiterm v0.2: Add --json flag to all commands
2. aiterm v0.2: Add CLAUDE.md init (use zsh-claude templates)
3. Update zsh-config to prefer aiterm when available
4. Keep shell fallbacks for core features
5. Test integration (with and without aiterm)
6. Document architecture in both repos

# Result:
- zsh-config "enhanced" by aiterm when present
- aiterm usable standalone (pip install)
- Clear architectural diagram
```

---

## PART 3: Consolidated Architecture (Final State)

### The End Goal: Three-Layer System

```
┌────────────────────────────────────────────────────────────────┐
│ LAYER 1: User-Facing Workflows (zsh-config)                   │
├────────────────────────────────────────────────────────────────┤
│ Your personal ADHD-optimized productivity system              │
│                                                                │
│ Commands:                                                      │
│ - work/finish (session management)                            │
│ - js/why/win (ADHD helpers)                                   │
│ - dash/tst/rst (dashboards)                                   │
│ - pp (project picker)                                         │
│ - 183 aliases + 108 functions                                 │
│ - Desktop app (Electron UI)                                   │
│ - Claude commands (from zsh-claude):                          │
│   - claude-ctx, claude-init, claude-show                      │
│   - proj-type, proj-info, proj-claude                         │
│                                                                │
│ Technologies: ZSH, Electron, fzf                              │
│ Distribution: Personal (dotfiles)                             │
└────────────────────────────────────────────────────────────────┘
                            ↓ uses
┌────────────────────────────────────────────────────────────────┐
│ LAYER 2: Terminal & Claude Optimization (aiterm)              │
├────────────────────────────────────────────────────────────────┤
│ Public CLI tool for terminal optimization                     │
│                                                                │
│ Commands:                                                      │
│ - aiterm detect (context detection - JSON output)             │
│ - aiterm switch (terminal profile switching)                  │
│ - aiterm claude settings|approvals (Claude Code mgmt)         │
│ - aiterm claude hooks (v0.2 - hook management)                │
│ - aiterm mcp (v0.2 - MCP server integration)                  │
│ - aiterm statusbar (v0.2 - builder)                           │
│ - aiterm claude init (v0.2 - CLAUDE.md from templates)        │
│                                                                │
│ Technologies: Python 3.10+, Typer, Rich                       │
│ Distribution: PyPI (pip install aiterm)                       │
└────────────────────────────────────────────────────────────────┘
                            ↓ both use
┌────────────────────────────────────────────────────────────────┐
│ LAYER 3: Shared Resources (in zsh-config after merge)         │
├────────────────────────────────────────────────────────────────┤
│ - CLAUDE.md templates (R pkg, Quarto, research)               │
│ - Project detector rules (8+ types)                           │
│ - Git utilities                                                │
│ - Core helper functions                                        │
└────────────────────────────────────────────────────────────────┘
```

### Project Boundaries After Consolidation

| Project | Purpose | Technologies | Users | Size |
|---------|---------|--------------|-------|------|
| **zsh-configuration** | DT's ADHD workflows + all Claude commands | ZSH, Electron | DT (primary) | ~20K lines (15K + 5K from zsh-claude) |
| **aiterm** | Terminal + Claude Code optimization | Python, PyPI | Public + DT | ~5K lines (v0.2+) |
| **zsh-claude-workflow** | ARCHIVED (merged into zsh-config) | - | - | - |
| **iterm2-context-switcher** | ARCHIVED (replaced by aiterm) | - | - | - |

---

## PART 4: Implementation Roadmap

### Phase 1: Merge zsh-claude → zsh-config (Week 1)

**Tasks:**
- [ ] Create `~/.config/zsh/lib/` directory
- [ ] Copy `zsh-claude-workflow/lib/*.sh` → `~/.config/zsh/lib/`
- [ ] Create `~/.config/zsh/functions/claude-integration.zsh`
- [ ] Copy all 20 commands from zsh-claude
- [ ] Create `~/.config/zsh/templates/claude/`
- [ ] Copy 3 CLAUDE.md templates
- [ ] Update `.zshrc` to source new files:
  ```zsh
  # Claude Integration (merged from zsh-claude-workflow)
  source $ZDOTDIR/functions/claude-integration.zsh
  ```
- [ ] Test all 20 commands (proj-type, claude-ctx, etc.)
- [ ] Update zsh-config README with new commands
- [ ] Archive zsh-claude-workflow repo:
  - Add README redirect: "MERGED into zsh-configuration"
  - Mark repo as archived on GitHub
  - Add migration guide for any external users

**Deliverable:**
- ✅ All 20 zsh-claude commands available in zsh-config
- ✅ Single ZSH project for all workflows
- ✅ zsh-claude archived with clear redirect

**Effort:** ⚡ 1 day (4-6 hours)

---

### Phase 2: Define aiterm v0.2 Scope (Week 2)

**Tasks:**
- [ ] Add `--json` output flag to ALL aiterm commands:
  ```bash
  aiterm detect --json
  # {"type": "r-package", "name": "medfit", "git_branch": "main", ...}

  aiterm claude settings --json
  # {"autoApprovals": [...], "statusLine": {...}}
  ```
- [ ] Add CLAUDE.md management to aiterm:
  - `aiterm claude init` - Create CLAUDE.md from template
  - Uses templates from zsh-config `~/.config/zsh/templates/claude/`
  - Symlink or copy templates into aiterm package
- [ ] Implement hook management:
  - `aiterm claude hooks list`
  - `aiterm claude hooks install <name>`
  - `aiterm claude hooks test <name>`
- [ ] Implement MCP integration:
  - `aiterm mcp list`
  - `aiterm mcp test <server>`
  - `aiterm mcp install <server>`
- [ ] Write integration docs:
  - How zsh-config uses aiterm
  - How to use aiterm standalone
  - API reference (--json outputs)

**Deliverable:**
- ✅ aiterm v0.2.0 with hooks + MCP + JSON output
- ✅ Integration-ready API
- ✅ Comprehensive docs

**Effort:** 🏗️ 1-2 weeks

---

### Phase 3: Integration (Week 3-4)

**Tasks:**
- [ ] Update zsh-config `work` command:
  ```zsh
  work() {
      local project=$1
      cd ~/projects/$project

      # Auto-switch terminal profile using aiterm
      if command -v aiterm &>/dev/null; then
          aiterm switch --quiet
      else
          echo "⚠️  Tip: Install aiterm for auto terminal profiles"
      fi

      # Rest of work logic...
  }
  ```
- [ ] Update `proj-type` to prefer aiterm:
  ```zsh
  proj-type() {
      if command -v aiterm &>/dev/null; then
          aiterm detect --json | jq -r '.type'
      else
          # Fallback: use shell implementation
          _detect_project_type_shell
      fi
  }
  ```
- [ ] Add aiterm installation check to zsh-config:
  ```zsh
  # In .zshrc or functions
  _check_aiterm() {
      if ! command -v aiterm &>/dev/null; then
          echo "💡 Tip: Install aiterm for enhanced features:"
          echo "   pip install aiterm"
          echo ""
      fi
  }
  ```
- [ ] Create architectural diagram (ASCII art for docs)
- [ ] Write integration guide for zsh-config README
- [ ] Test on fresh machine (with and without aiterm)

**Deliverable:**
- ✅ zsh-config enhanced by aiterm when present
- ✅ Graceful degradation when aiterm absent
- ✅ Clear documentation of integration

**Effort:** 🔧 3-5 days

---

### Phase 4: Cleanup & Polish (Week 5)

**Tasks:**
- [ ] Archive iterm2-context-switcher:
  - Add README: "DEPRECATED - Use aiterm instead"
  - Create migration guide
  - Mark repo as archived
- [ ] Update all project READMEs with new architecture
- [ ] Create cross-project documentation:
  - `~/projects/dev-tools/INTEGRATION-MAP.md`
  - Shows how all devtools projects work together
- [ ] Add "Related Projects" section to each README:
  ```markdown
  ## Related Projects

  - **aiterm**: Terminal optimization (pip install aiterm)
  - **zsh-configuration**: ADHD workflows (dotfiles)
  - **obsidian-cli-ops**: Knowledge management (pip install obs-cli)
  - **mcp-servers**: MCP server collection
  ```
- [ ] Test full workflow:
  - Install aiterm (`pip install aiterm`)
  - Set up zsh-config (existing setup script)
  - Verify integration works
  - Document any gotchas

**Deliverable:**
- ✅ Clean, documented architecture
- ✅ Archived legacy projects
- ✅ Integration map for all devtools

**Effort:** 🔧 2-3 days

---

## PART 5: Quick Wins vs Long-term

### ⚡ Quick Wins (This Week)

**1. Merge zsh-claude → zsh-config (Day 1-2)**
- Copy files
- Update .zshrc
- Test commands
- Archive repo
- **Impact:** Single ZSH project, -1 repo to maintain
- **Effort:** 4-6 hours

**2. Archive iterm2-context-switcher (Day 2)**
- Add README redirect
- Mark repo archived
- **Impact:** Clear that aiterm is the replacement
- **Effort:** 30 minutes

**3. Add --json to aiterm (Day 3-4)**
- Simple feature flag
- JSON.dumps() existing data structures
- **Impact:** Makes aiterm integration-ready
- **Effort:** 2-3 hours

### 🏗️ Long-term Projects (Weeks 2-5)

**1. aiterm v0.2.0 (Hook + MCP) (Week 2-3)**
- Comprehensive feature addition
- **Impact:** Makes aiterm production-ready
- **Effort:** 1-2 weeks

**2. zsh-config Integration (Week 3-4)**
- Update commands to call aiterm
- Add fallbacks
- **Impact:** Best-of-breed implementation
- **Effort:** 3-5 days

**3. Documentation & Polish (Week 5)**
- Cross-project docs
- Migration guides
- **Impact:** Professional, maintainable ecosystem
- **Effort:** 2-3 days

---

## PART 6: Trade-offs & Considerations

### Trade-off 1: Simplicity vs Power

**Simplicity:**
- Merge everything into zsh-config
- One giant ZSH project
- No external dependencies

**Power:**
- Separate aiterm as Python CLI
- Better testing, distribution
- Multi-platform potential

**Decision:** Go with Power (keep aiterm separate)
- **Why:** Python's benefits outweigh simplicity
- **Mitigation:** Good docs make integration clear

---

### Trade-off 2: DRY vs Redundancy

**DRY (Don't Repeat Yourself):**
- Single context detector (aiterm)
- zsh-config always calls aiterm
- Zero duplication

**Redundancy:**
- Keep shell fallbacks in zsh-config
- Works without aiterm installed
- Some duplication

**Decision:** Choose Redundancy (with primary owner)
- **Why:** Graceful degradation is ADHD-friendly
- **Rule:** aiterm is primary, shell is fallback

---

### Trade-off 3: Personal vs Public

**Personal (zsh-config only):**
- Optimize for DT's workflow
- Don't worry about external users
- Can be messy, idiosyncratic

**Public (aiterm focus):**
- Clean, documented, tested
- PyPI distribution
- General-purpose

**Decision:** Both have value
- **zsh-config:** Personal, ADHD-optimized, allowed to be messy
- **aiterm:** Public, clean, well-tested

---

## PART 7: Success Metrics

### Week 1 Success
- [ ] zsh-claude merged into zsh-config (all 20 commands working)
- [ ] iterm2-context-switcher archived
- [ ] Single source of truth for ZSH workflows

### v0.2.0 Success (Week 2-3)
- [ ] aiterm has --json output for all commands
- [ ] Hook management implemented
- [ ] MCP integration implemented
- [ ] CLAUDE.md init added (using zsh templates)

### Integration Success (Week 4)
- [ ] zsh-config calls aiterm for terminal switching
- [ ] zsh-config calls aiterm for context detection
- [ ] Graceful fallbacks work without aiterm
- [ ] Documentation complete

### Public Release Success (Month 2-3)
- [ ] 10+ external aiterm users
- [ ] PyPI package stable
- [ ] Zero overlap (clear boundaries)
- [ ] Integration map documented

---

## PART 8: Risks & Mitigations

### Risk 1: Integration Complexity
**Risk:** zsh-config + aiterm integration fails, causes breakage
**Mitigation:**
- Keep shell fallbacks
- Test on fresh machine
- Gradual rollout (work command first, others later)

### Risk 2: Python Dependency
**Risk:** Users don't want to install Python for ZSH config
**Mitigation:**
- Make aiterm optional (enhanced features, not required)
- Shell fallbacks work without Python
- Clear docs on benefits of installing aiterm

### Risk 3: Maintenance Burden
**Risk:** Two projects (zsh-config + aiterm) = double the work
**Mitigation:**
- Clear boundaries (aiterm = implementation, zsh-config = workflows)
- aiterm well-tested (51 tests, 83% coverage)
- Integration layer is thin (just CLI calls)

---

## PART 9: Alternative Futures

### Alternative A: Kill aiterm, ZSH-only

**Scenario:**
- Decide Python was a mistake
- Port aiterm features back to ZSH
- Single mega zsh-config project

**When to choose:**
- If Python dependency becomes painful
- If external users don't materialize
- If maintenance burden too high

**Cost:** Lose testing, distribution, cross-platform potential

---

### Alternative B: Kill zsh-config, aiterm-only

**Scenario:**
- Port ADHD workflows to Python
- aiterm becomes mega-tool
- Distribute via PyPI

**When to choose:**
- If you want to share ADHD workflows publicly
- If ZSH becomes limiting
- If you want cross-shell support

**Cost:** Massive rewrite (15K+ lines), lose ZSH ecosystem

---

### Alternative C: Desktop App Dominates

**Scenario:**
- zsh-config's Electron app becomes primary interface
- CLI becomes secondary
- aiterm integrates as backend for app

**When to choose:**
- If GUI becomes more important than CLI
- If ADHD workflows benefit from visual interface
- If you want to ship to non-developers

**Cost:** Large development effort, different skills needed

---

## PART 10: Final Recommendations

### Recommended Path: **Hybrid Integration**

**Phase 1 (This Week):**
1. ✅ Merge zsh-claude → zsh-config (Option 1A)
   - Full merge, archive zsh-claude repo
   - **Effort:** 1 day
   - **Impact:** -1 project, single ZSH source

2. ✅ Archive iterm2-context-switcher
   - Add redirect README
   - **Effort:** 30 minutes
   - **Impact:** Clear succession

**Phase 2 (Week 2-3):**
3. ✅ Develop aiterm v0.2.0 (Option 2A backend)
   - Hooks, MCP, --json output, CLAUDE.md init
   - **Effort:** 1-2 weeks
   - **Impact:** Production-ready aiterm

**Phase 3 (Week 3-4):**
4. ✅ Integrate zsh-config + aiterm (Option 2A)
   - work → aiterm switch
   - proj-type → aiterm detect
   - Keep shell fallbacks
   - **Effort:** 3-5 days
   - **Impact:** Best-of-breed implementation

**Phase 4 (Week 5):**
5. ✅ Documentation & Polish
   - Integration map
   - Migration guides
   - Cross-project docs
   - **Effort:** 2-3 days
   - **Impact:** Professional ecosystem

### Final Architecture

```
zsh-configuration (20K lines)
├── ADHD workflows (js, why, win, work, finish)
├── Claude commands (20 from zsh-claude)
├── 183 aliases + 108 functions
├── Desktop app (Electron)
└── Calls aiterm for terminal + Claude optimization

aiterm (5K+ lines Python)
├── Terminal profile switching (iTerm2, Warp, etc.)
├── Context detection (8+ types, JSON)
├── Claude Code management (settings, hooks, MCP)
├── StatusLine builder
└── CLAUDE.md init (using zsh-config templates)

Projects Archived:
- zsh-claude-workflow (merged into zsh-config)
- iterm2-context-switcher (replaced by aiterm)
```

### Success Criteria

**Immediate (Week 1):**
- Single ZSH project for all workflows
- Clear project boundaries

**Short-term (Month 1):**
- aiterm v0.2.0 released
- Integration working smoothly
- Zero duplication in context detection

**Long-term (Month 3):**
- 10+ external aiterm users
- Documentation ecosystem complete
- Clear mental model for all projects

---

**Last Updated:** 2025-12-19
**Status:** 🟡 Awaiting approval to execute
**Next Action:** Review plan, choose Phase 1 start date
