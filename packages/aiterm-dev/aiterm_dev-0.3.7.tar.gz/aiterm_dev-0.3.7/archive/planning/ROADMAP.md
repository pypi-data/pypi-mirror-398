# ROADMAP

## Current Status: v0.2.1 ✅ RELEASED

**Latest Release:** v0.2.1 (Dec 26, 2025)
**PyPI:** https://pypi.org/project/aiterm-dev/
**Homebrew:** `brew install data-wise/tap/aiterm`
**Docs:** https://data-wise.github.io/aiterm/

### Release History
| Version | Date | Highlights |
|---------|------|------------|
| v0.2.1 | 2025-12-26 | PyPI publishing, Homebrew fix, 9 REFCARDs |
| v0.2.0 | 2025-12-24 | 4 feature systems (hooks, commands, MCP, docs) |
| v0.1.0 | 2025-12-16 | Initial release, core CLI |

### Next: v0.3.0 (Planned)
- Gemini CLI support
- IDE integrations (Positron, Zed, VS Code)
- Workflow automation enhancements

---

# Historical: Week 1 MVP ✅ COMPLETE

**Goal:** Transform aiterm → aiterm CLI tool

**Timeline:** 7 days (COMPLETED 2025-12-16)
**Target Version:** v0.1.0-dev
**User:** DT (primary user testing)
**Status:** 100% complete ✅ - Tagged and ready for release

---

## Day 1-2: Project Setup & Architecture ✅

### Tasks

- [x] ✅ Create IDEAS.md
- [x] ✅ Create ROADMAP.md
- [x] ✅ Update all documentation
- [x] ✅ Set up Python project structure
  ```
  aiterm/
  ├── pyproject.toml          # setuptools config
  ├── src/aiterm/
  │   ├── __init__.py
  │   ├── cli/                # CLI commands
  │   │   └── main.py
  │   ├── terminal/           # Terminal detection
  │   │   ├── __init__.py
  │   │   └── iterm2.py
  │   ├── context/            # Context detection
  │   │   └── detector.py
  │   ├── claude/             # Claude Code integration
  │   │   └── settings.py
  │   └── utils/
  ├── tests/                  # 51 tests, 83% coverage
  └── templates/
      └── commands/           # 6 hub commands
  ```
- [x] ✅ Initialize git (pivoted existing repo)
- [x] ✅ Set up pip/setuptools for dependencies
- [x] ✅ Install Typer, Rich, Questionary, PyYAML

### Deliverable ✅
- [x] Clean project structure
- [x] `pip install -e .` works
- [x] Basic CLI runs: `aiterm --version`

---

## Day 3-4: Core Terminal Integration ✅

### Tasks

#### Migrate Existing Code ✅
- [x] ✅ Port `zsh/iterm2-integration.zsh` → Python module
- [x] ✅ Extract context detection logic (8 types):
  - R packages (DESCRIPTION)
  - Python (pyproject.toml)
  - Node.js (package.json)
  - Quarto (_quarto.yml)
  - Emacs (init.el, Cask)
  - Production paths
  - AI sessions
  - Dev-tools
- [x] ✅ Port profile definitions
- [x] ✅ Migrate test suite → pytest (51 tests)

#### New CLI Commands ✅
- [x] ✅ `aiterm init` - Interactive setup (placeholder)
- [x] ✅ `aiterm doctor` - Diagnostics (working)
- [x] ✅ `aiterm detect` - Context detection shortcut
- [x] ✅ `aiterm switch` - Detect and apply context
- [x] ✅ `aiterm context detect|show|apply` - Full context commands
- [x] ✅ `aiterm profile list` - List available profiles

### Deliverable ✅
- [x] `aiterm init` shows setup placeholder
- [x] `aiterm doctor` shows status
- [x] Profile switching works (iTerm2 escape sequences)
- [x] Context detection works (all 8 types)

---

## Day 5: Claude Code Integration ✅

### Tasks

#### Settings Management ✅
- [x] ✅ Read Claude Code settings file
  - Location: `~/.claude/settings.json` and `.claude/settings.local.json`
  - Parse JSON, validate structure
  - ClaudeSettings dataclass

- [x] ✅ `aiterm claude settings` - Display settings
- [x] ✅ `aiterm claude backup` - Timestamped backup

#### Auto-Approval Presets ✅
- [x] ✅ Define 8 preset templates:
  - safe-reads, git-ops, github-cli
  - python-dev, node-dev, r-dev
  - web-tools, minimal

- [x] ✅ `aiterm claude approvals add <preset>` - Add preset permissions
- [x] ✅ `aiterm claude approvals list` - Show current permissions
- [x] ✅ `aiterm claude approvals presets` - List available presets

### Deliverable ✅
- [x] Can read/write Claude Code settings
- [x] Auto-approval presets working (8 presets)
- [x] Settings backup feature with timestamps

---

## Day 6: Testing & Documentation ✅

### Tasks

#### Testing ✅
- [x] ✅ Port existing tests → pytest (expanded)
- [x] ✅ Add CLI command tests (test_cli.py)
- [x] ✅ Add context detection tests (test_context.py)
- [x] ✅ Add iTerm2 module tests (test_iterm2.py)
- [x] ✅ Add Claude settings tests (test_claude_settings.py)
- [x] ✅ **Result:** 51 tests, 83% coverage

#### Documentation ✅
- [x] ✅ Update README.md (v0.1 features, installation)
- [x] ✅ Update CHANGELOG.md (release notes)
- [x] ✅ Command reference in README
- [x] ✅ Installation guide (uv/pipx)

### Deliverable ✅
- [x] All tests passing (51/51)
- [x] Documentation complete
- [x] Ready for personal use

---

## Day 7: Polish & Dogfooding ✅

### Tasks

#### Polish ✅
- [x] ✅ Rich output (colors, tables, panels)
- [x] ✅ Error handling with helpful messages
- [x] ✅ Input validation (preset names, paths)
- [x] ✅ Shell completion support (Typer built-in)

#### Real-World Testing 🟡
- [x] ✅ Install on dev machine (`pip install -e .`)
- [ ] 🟡 Use for 1 full day (awaiting PR merge)
- [x] ✅ Track issues via GitHub
- [x] ✅ Fix critical bugs during development

#### Prepare for v0.2 ✅
- [x] ✅ Document next features in IDEAS.md
- [x] ✅ Plan: hook management, MCP integration, Gemini support

### Deliverable ✅
- [x] v0.1.0-dev ready (awaiting PR merge)
- [ ] 🟡 DT using daily (after release)
- [x] ✅ No regressions from old system
- [x] ✅ Plan for v0.2 ready (see IDEAS.md)

---

## Success Criteria for MVP ✅

### Must Have ✅
- [x] ✅ CLI installs cleanly (`pip install -e .`, `uv tool install`, `pipx install`)
- [x] ✅ `aiterm init` sets up terminal (placeholder ready)
- [x] ✅ `aiterm doctor` shows accurate status
- [x] ✅ Context switching works (all 8 types)
- [x] ✅ Profile switching works
- [x] ✅ Can manage Claude Code auto-approvals (8 presets)
- [x] ✅ Tests pass (83% coverage, 51 tests)
- [x] ✅ Documentation exists (README, CHANGELOG)

### Should Have ✅
- [x] ✅ Fast startup (< 500ms)
- [x] ✅ Good error messages
- [x] ✅ Shell completion (Typer)
- [x] ✅ Rich CLI output (tables, panels)

### Nice to Have 🟡
- [ ] Interactive prompts (questionary available)
- [ ] Config file support (planned v0.2)
- [ ] Undo/rollback features (planned v0.2)
- [ ] Verbose/debug modes (planned v0.2)

---

## Risks & Mitigations

### Risk: iTerm2 API complexity
**Mitigation:** Start with escape sequences (already working), add Python API later

### Risk: Claude Code settings format changes
**Mitigation:** Version detection, backwards compatibility

### Risk: Scope creep
**Mitigation:** Stick to this roadmap, defer to Phase 2

### Risk: Testing on single machine
**Mitigation:** VM testing, ask colleague to test

---

## Post-MVP: v0.2.0 Roadmap

### Focus Areas for v0.2.0 (Phase 2)

**Core Goals:** Deep Claude Code integration and developer productivity

#### 1. Hook Management System
- Install and manage Claude Code hooks (9 types available)
- Template library for common hook patterns
- Interactive hook creator/editor
- Hook validation and testing

#### 2. MCP Integration
- Discover and configure MCP servers
- Test MCP server connections
- Manage server permissions
- Generate server configs from templates

#### 3. StatusLine Builder
- Interactive statusLine script generator
- Theme templates (cool-blues, forest-greens, purple-charcoal)
- Real-time preview
- Session data integration (cost tracking, duration, changes)

#### 4. Workflow Commands & Documentation Automation (Phase 2.6)
**Status:** Planning complete, implementation planned
**Created:** `/workflow:done` command (474 lines)

**Core Features:**
- Session completion with git-based activity detection
- Automatic .STATUS file updates
- Commit message generation
- ADHD-optimized 30-second fast path

**Enhancement Roadmap (3 Phases):**
1. **Detection & Warnings** (3-4 hours)
   - CLAUDE.md staleness detection (git diff)
   - Orphaned documentation pages (grep)
   - README/docs divergence checks
   - Missing CHANGELOG entries

2. **Auto-Updates** (4-6 hours)
   - CHANGELOG generation from commits
   - CLAUDE.md "What's New" section updates
   - mkdocs.yml navigation sync
   - Link validation and fixing

3. **AI-Powered Generation** (8-12 hours)
   - LLM-based documentation writing
   - Interactive doc review interface
   - Multi-document consistency checks
   - Screenshot/diagram generation

**Integration Points:**
- Works with `/workflow:recap` for session restoration
- Complements `/workflow:next` for decision support
- Enhances git workflow with documentation awareness

### Quick Wins to Add:
- `aiterm context show` - Current context info (already exists!)
- `aiterm quota set` - Integration with existing `qu` command
- `aiterm export` - Export config for backup

### Timeline
**Target:** 2 weeks after v0.1.0 release
**Priority:** Hook management > MCP integration > StatusLine builder > Workflow automation

---

## Daily Standup Format

### Each Day:
**What I did:**
**What I'm doing today:**
**Blockers:**

Use `/recap` and `/next` to track progress!

---

## Resources

### Dependencies
- `typer` - CLI framework
- `rich` - Terminal formatting
- `questionary` - Interactive prompts
- `pyyaml` - Config files
- `pytest` - Testing

### Documentation
- Typer docs: https://typer.tiangolo.com/
- iTerm2 Python API: https://iterm2.com/python-api/
- Claude Code docs: https://claude.com/code

### Existing Code to Reference
- `zsh/iterm2-integration.zsh` (context detection)
- `scripts/test-context-switcher.sh` (test patterns)
- `statusline-alternatives/` (theme ideas)
- `.claude/settings.local.json` (auto-approvals)
