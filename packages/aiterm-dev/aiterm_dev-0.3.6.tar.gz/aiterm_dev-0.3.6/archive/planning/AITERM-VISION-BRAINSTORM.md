# aiterm: The Ultimate CLI Integration Hub for AI Coding

**Generated:** 2025-12-19
**New Vision:** Terminal integration + MCP/Plugin/Agent/Command management for Claude Code & Gemini CLI

---

## 🎯 NEW FOCUSED SCOPE

**aiterm is THE command-line tool for managing AI-assisted development workflows.**

### What aiterm Does (Focused Vision)

```
┌─────────────────────────────────────────────────────────────┐
│ aiterm: CLI Integration Hub for AI Coding Tools            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. Terminal Integration                                    │
│    - Auto-switch profiles based on context                 │
│    - Custom StatusLine (session info, quota, time)         │
│    - Multi-terminal support (iTerm2, Warp, Alacritty)     │
│                                                             │
│ 2. Claude Code Management                                  │
│    - Settings & auto-approvals (existing v0.1)            │
│    - Hook management (install, test, validate)             │
│    - MCP server management (discover, install, test)       │
│    - Plugin management (search, install, update)           │
│    - Agent management (create, configure, test)            │
│    - Custom commands (slash commands, skills)              │
│                                                             │
│ 3. Gemini CLI Integration                                  │
│    - Similar management for Gemini workflows               │
│    - Cross-tool context switching                          │
│    - Unified MCP server management                         │
│                                                             │
│ 4. Workflow Automation                                     │
│    - Context-aware recommendations                          │
│    - Session management                                     │
│    - Quota tracking & alerts                               │
│    - Template library                                       │
└─────────────────────────────────────────────────────────────┘
```

### What aiterm Does NOT Do (Out of Scope)

❌ ADHD workflows (that's zsh-configuration)
❌ Project management (that's zsh-configuration)
❌ 183 aliases (that's zsh-configuration)
❌ Desktop app (that's zsh-configuration)
❌ Obsidian integration (that's obsidian-cli-ops)
❌ Knowledge management (that's obs-cli)

### Why This Focus Makes Sense

✅ **Clear niche:** AI CLI tools integration
✅ **Public value:** Anyone using Claude Code/Gemini CLI needs this
✅ **Technical depth:** Complex systems (MCP, plugins, agents) need good tooling
✅ **Complementary:** Works WITH zsh-configuration, not against it

---

## PART 1: Terminal Integration (v0.1 + Enhancements)

### Existing Features (v0.1.0 ✅)
- [x] Context detection (8 types)
- [x] Profile switching (iTerm2 escape sequences)
- [x] Auto-approvals management (8 presets)
- [x] Settings management

### New Ideas: Terminal Integration++

#### 1.1 Multi-Terminal Support ⭐

**Current:** iTerm2 only
**Vision:** Support 5+ terminals

**Terminals to Support:**
1. **iTerm2** (macOS) - Full support (existing ✅)
   - Escape sequences for profiles
   - Python API for advanced features
   - StatusLine user variables

2. **Warp** (macOS/Linux) - High priority ⭐
   - Modern, AI-native terminal
   - Block-based interface
   - Custom themes via YAML
   - Integration: `~/.warp/themes/aiterm-*.yaml`

3. **Alacritty** (Cross-platform) - Medium priority
   - Config file: `~/.config/alacritty/alacritty.yml`
   - Live reload on config change
   - Integration: Generate config snippets

4. **Kitty** (Cross-platform) - Medium priority
   - Config file: `~/.config/kitty/kitty.conf`
   - Remote control protocol
   - Integration: `kitty @ set-colors`

5. **Windows Terminal** (Windows) - Future
   - JSON config: `settings.json`
   - Profile switching via CLI
   - Integration: PowerShell module

**Commands:**
```bash
aiterm terminal detect
# Output: iTerm2 v3.5.0

aiterm terminal list
# Output:
# ✅ iTerm2 (active, full support)
# ⚠️  Warp (detected, partial support)
# ❌ Alacritty (not detected)

aiterm terminal switch --profile=Python-Dev
# Switches profile in detected terminal

aiterm terminal export --format=warp
# Exports current profile to Warp YAML format
```

**Implementation:**
```python
# src/aiterm/terminal/
├── base.py          # Abstract base class
├── iterm2.py        # iTerm2 (existing ✅)
├── warp.py          # NEW
├── alacritty.py     # NEW
├── kitty.py         # NEW
└── detector.py      # Auto-detect which terminal
```

**Effort:** 🏗️ Large (1-2 weeks for 3 new terminals)
**Priority:** Medium (iTerm2 works for now)

---

#### 1.2 StatusLine Builder (Interactive) ⭐⭐

**Current:** Manual script editing
**Vision:** Interactive builder with live preview

**Command Flow:**
```bash
aiterm statusbar init
# → Interactive wizard

aiterm statusbar build
# → Opens TUI builder with live preview

aiterm statusbar preview
# → Shows what current config looks like

aiterm statusbar export --format=p10k
# → Generates Powerlevel10k config
```

**Interactive Builder Features:**

**1. Component Library:**
```
Available Components:
├── Session Info
│   ├── Model name (Sonnet 4.5 / Opus 4.5)
│   ├── Session duration (⏱ 15m)
│   ├── Current time (HH:MM)
│   └── Date
├── Cost Tracking
│   ├── Total cost (💰 $0.45)
│   ├── Lines changed (+123/-45)
│   ├── API calls count
│   └── Token usage
├── Git Info
│   ├── Branch name
│   ├── Dirty status (*)
│   ├── Ahead/behind
│   └── Last commit time
├── Project Info
│   ├── Project name
│   ├── Project type icon (📦 R / 🐍 Python / 📊 Quarto)
│   ├── Virtual env indicator
│   └── Node version
├── System Info
│   ├── Battery %
│   ├── CPU load
│   ├── Memory usage
│   └── WiFi signal
└── Custom
    ├── Run shell command
    ├── Read file
    └── Python expression
```

**2. Layout Designer:**
```
Choose layout:
[ ] Single line
[ ] Two lines (top + bottom)
[x] Three segments (left | center | right)

Left segment:
- [x] Project icon
- [x] Project name
- [ ] Git branch

Center segment:
- [x] Model name
- [x] Session duration

Right segment:
- [x] Time
- [x] Cost
- [x] Lines changed
```

**3. Theme Variants (from existing templates):**
- cool-blues (blue/cyan color scheme)
- forest-greens (green/teal scheme)
- purple-charcoal (purple/gray scheme)
- minimal (black & white)
- custom (color picker)

**4. Live Preview:**
```
┌─────────────────────────────────────────────────┐
│ Preview:                                        │
├─────────────────────────────────────────────────┤
│ ╭─ 📦 medfit  main ▓▒░                         │
│ ╰─ Sonnet 4.5 │ 14:35 │ ⏱ 15m │ +45/-12 │ ⚡84%│
└─────────────────────────────────────────────────┘
```

**Implementation Ideas:**

**Option A: TUI (Text UI) using Rich/Textual ⭐**
```bash
aiterm statusbar build
# Opens interactive TUI:
# - Left panel: Component list (checkboxes)
# - Right panel: Live preview
# - Bottom: Save/Cancel buttons
```

**Option B: Web UI (Streamlit/Flask)**
```bash
aiterm statusbar build --ui
# Opens browser: http://localhost:5000
# Visual drag-and-drop builder
# Export button → downloads script
```

**Option C: Wizard (Question/Answer)**
```bash
aiterm statusbar init

? What layout? (Use arrow keys)
  ❯ Single line
    Two lines
    Three segments

? Include model name? Yes
? Include session duration? Yes
? Include cost tracking? Yes

✨ Generated: ~/.claude/statusline.sh
```

**Recommendation:** Start with **Option C (Wizard)** for v0.2, add TUI in v0.3

**Effort:** 🔧 Medium (3-5 days for wizard, 1-2 weeks for TUI)
**Priority:** High (StatusLine is core feature)

---

#### 1.3 Context-Aware Profile Recommendations ⭐

**Vision:** aiterm suggests optimal terminal profile based on what you're doing

**How It Works:**
```bash
cd ~/projects/r-packages/medfit
aiterm detect

# Output:
# 📦 R Package detected: medfit
#
# Recommended profile: R-Dev
# Includes:
# - R syntax highlighting
# - devtools shortcuts in prompt
# - Package check reminders
#
# Apply now? [Y/n]
```

**Machine Learning (Future):**
- Track which profiles you use for which projects
- Learn your preferences
- Suggest: "You usually use Python-Dev for this, but it's a research project. Try Research?"

**Implementation:**
```python
# src/aiterm/recommender.py
class ProfileRecommender:
    def suggest(self, context: ProjectContext) -> List[Profile]:
        # Rule-based for v0.2
        # ML-based for v1.0
        pass
```

**Effort:** ⚡ Quick (rule-based), 🏗️ Large (ML-based)
**Priority:** Medium (nice-to-have)

---

## PART 2: Claude Code Management (CORE FOCUS) ⭐⭐⭐

### 2.1 Hook Management System

**Current State:** Manual hook creation, no discovery
**Vision:** Template library + validation + testing

**Hook Categories (9 types available):**

1. **PreToolUse** - Block/modify before tool execution
2. **PostToolUse** - Actions after tool completion
3. **PermissionRequest** - Auto-approve/deny dialogs
4. **UserPromptSubmit** - Enhance prompts with context
5. **SessionStart** - Initialize sessions
6. **SessionEnd** - Cleanup and logging
7. **Stop** - Control when Claude stops
8. **PreCompact** - Before context compaction
9. **Notification** - Custom alerts

**Commands:**

```bash
# Discovery
aiterm hooks list
# Output:
# Installed Hooks:
# ✅ prompt-optimizer (UserPromptSubmit) - Active
# ⚠️  cost-limiter (PreToolUse) - Syntax error
#
# Available Templates:
# - block-sensitive-files (PreToolUse)
# - auto-test-runner (PostToolUse)
# - quota-display (SessionStart)
# - [12 more...]

aiterm hooks search "test"
# Output:
# 🔍 Found 3 hooks matching "test":
# - auto-test-runner (PostToolUse)
# - test-validator (PreToolUse)
# - test-coverage (SessionEnd)

aiterm hooks info auto-test-runner
# Output:
# Hook: auto-test-runner
# Type: PostToolUse
# Description: Runs tests after code edits
# Author: claude-plugins-official
# Downloads: 1.2k
# Rating: ⭐⭐⭐⭐⭐ (4.8/5)
#
# When to use:
# - TDD workflows
# - Continuous testing
# - Instant feedback
#
# Configuration:
# - test_command: Command to run (default: "npm test")
# - patterns: Files to watch (default: "**/*.{js,ts}")

# Installation
aiterm hooks install auto-test-runner
# → Downloads from marketplace
# → Validates schema
# → Asks for config
# → Installs to ~/.claude/hooks/

aiterm hooks install --from-file ~/my-custom-hook.sh
# → Validates custom hook
# → Installs locally

# Testing
aiterm hooks test auto-test-runner
# → Dry-run with sample data
# → Shows what would happen
# → No side effects

aiterm hooks validate auto-test-runner
# → Checks syntax
# → Verifies schema
# → Tests with fixtures

# Management
aiterm hooks enable auto-test-runner
aiterm hooks disable auto-test-runner
aiterm hooks update auto-test-runner
aiterm hooks remove auto-test-runner

# Creation
aiterm hooks create my-hook
# → Interactive wizard
# → Template selection
# → Code scaffolding

aiterm hooks create my-hook --type=PreToolUse --template=block
# → Creates from template
# → Opens in $EDITOR
```

**Hook Template Library:**

**PreToolUse Hooks:**
- `block-sensitive-files` - Prevent .env, credentials access ⭐
- `validate-bash-commands` - Security checks for shell commands
- `cost-estimator` - Warn before expensive operations
- `rate-limiter` - Prevent API spam
- `file-size-limiter` - Block huge file reads

**PostToolUse Hooks:**
- `auto-test-runner` - Run tests after edits ⭐
- `backup-creator` - Save versions before changes
- `changelog-updater` - Track modifications
- `linter-runner` - Auto-lint after edits
- `git-auto-add` - Stage changes automatically

**UserPromptSubmit Hooks:**
- `context-injector` - Add project context ⭐
- `style-enforcer` - Ensure consistent tone
- `template-expander` - Expand shortcuts
- `multi-language` - Translate prompts
- `spell-checker` - Fix typos before submit

**SessionStart Hooks:**
- `quota-display` - Show API quota on startup ⭐
- `project-context` - Detect and show project info
- `git-status-check` - Warn if uncommitted changes
- `todo-loader` - Load .STATUS file
- `environment-validator` - Check dependencies

**PermissionRequest Hooks:**
- `auto-approve-reads` - Safe operations only ⭐
- `block-destructive` - Prevent rm, dangerous ops
- `require-confirmation` - Extra prompt for important actions

**Implementation:**

```python
# src/aiterm/hooks/
├── manager.py       # Hook management
├── validator.py     # Schema validation
├── tester.py        # Dry-run testing
├── installer.py     # Install from marketplace
└── templates/       # Built-in templates
    ├── pre-tool-use/
    ├── post-tool-use/
    ├── user-prompt-submit/
    └── ...
```

**Hook Marketplace Integration:**
```python
# Connect to official Claude marketplace
MARKETPLACE_URL = "https://marketplace.claude.com/hooks"

async def search_hooks(query: str) -> List[Hook]:
    # Search marketplace
    pass

async def download_hook(hook_id: str) -> Hook:
    # Download and verify
    pass
```

**Effort:** 🏗️ Large (1-2 weeks)
**Priority:** 🔥 HIGHEST (this is killer feature)

---

### 2.2 MCP Server Management ⭐⭐⭐

**Current State:** Manual JSON editing, no discovery
**Vision:** npm-like package manager for MCP servers

**Discovery & Search:**

```bash
aiterm mcp search "database"
# Output:
# 🔍 Found 8 MCP servers:
#
# ⭐ postgres-mcp (Official)
#    PostgreSQL database access
#    Downloads: 5.2k | Rating: ⭐⭐⭐⭐⭐ (4.9/5)
#
# ⭐ sqlite-mcp (Official)
#    SQLite database access
#    Downloads: 3.1k | Rating: ⭐⭐⭐⭐⭐ (4.8/5)
#
# mongodb-mcp (Community)
#    MongoDB integration
#    Downloads: 1.8k | Rating: ⭐⭐⭐⭐ (4.2/5)

aiterm mcp search --category=research
# Shows: zotero, pubmed, arxiv, etc.

aiterm mcp search --author=anthropic
# Shows official Anthropic servers

aiterm mcp trending
# Shows most downloaded this week

aiterm mcp featured
# Shows curated list
```

**Installation & Configuration:**

```bash
aiterm mcp install postgres-mcp
# → Interactive wizard:
#
# PostgreSQL MCP Server Setup
# ───────────────────────────
# Connection string: postgresql://user:pass@localhost/db
# Port (default 5432):
# SSL mode (disable/require): require
#
# ✨ Installed postgres-mcp to ~/.claude/settings.json
#
# Next steps:
# 1. Test connection: aiterm mcp test postgres-mcp
# 2. Try it: claude --mcp-config postgres-mcp

aiterm mcp install ~/my-custom-server/
# → Installs from local directory
# → Validates package structure
# → Adds to config

aiterm mcp install github:user/repo
# → Clones from GitHub
# → Runs npm install
# → Adds to config
```

**Management:**

```bash
aiterm mcp list
# Output:
# Configured MCP Servers:
#
# ✅ filesystem (built-in)
#    Status: Running
#    Tools: read_file, write_file, list_directory
#
# ✅ statistical-research (custom)
#    Status: Running
#    Tools: r_execute, zotero_search, pubmed_query
#    Location: ~/projects/dev-tools/mcp-servers/statistical-research
#
# ❌ postgres-mcp (installed)
#    Status: Error - Connection refused
#    Tools: query, execute, schema

aiterm mcp status postgres-mcp
# Output:
# Server: postgres-mcp
# Status: ❌ Not running
# Error: Connection refused (localhost:5432)
#
# Diagnostics:
# - PostgreSQL service not running
# - Try: brew services start postgresql@14

aiterm mcp test postgres-mcp
# → Validates connection
# → Tests each tool
# → Shows latency
#
# Output:
# Testing postgres-mcp...
# ✅ Connection: OK (12ms)
# ✅ Tool: query - OK (45ms)
# ✅ Tool: execute - OK (38ms)
# ✅ Tool: schema - OK (23ms)

aiterm mcp logs postgres-mcp
# → Shows recent logs
# → Tails in real-time with --follow

aiterm mcp restart postgres-mcp
# → Restarts server process

aiterm mcp update postgres-mcp
# → Checks for updates
# → Installs latest version

aiterm mcp remove postgres-mcp
# → Uninstalls server
# → Removes from config
```

**Configuration:**

```bash
aiterm mcp config postgres-mcp
# → Opens in $EDITOR:
#
# {
#   "command": "npx",
#   "args": ["-y", "@anthropic/postgres-mcp"],
#   "env": {
#     "DATABASE_URL": "postgresql://..."
#   }
# }

aiterm mcp config postgres-mcp --set DATABASE_URL=postgres://newurl
# → Updates config inline

aiterm mcp validate
# → Validates ALL server configs
# → Checks for errors
# → Shows warnings
```

**OAuth Integration (Advanced):**

```bash
aiterm mcp oauth google-drive-mcp
# → Opens browser
# → OAuth flow
# → Stores tokens securely
# → Updates config

aiterm mcp oauth google-drive-mcp --refresh
# → Refreshes access token
```

**Context-Aware Recommendations:**

```bash
cd ~/projects/r-packages/medfit
aiterm mcp recommend

# Output:
# 📊 R Package Project Detected
#
# Recommended MCP Servers:
#
# ⭐ r-execution (not installed)
#    Execute R code, manage packages
#    Why: You're in an R project
#    Install: aiterm mcp install r-execution
#
# ⭐ github (not installed)
#    Create releases, manage issues
#    Why: Publishing R packages to GitHub
#    Install: aiterm mcp install github
#
# Already installed:
# ✅ filesystem (active)
```

**Export/Import (Team Sharing):**

```bash
aiterm mcp export --output=team-mcp-config.json
# → Exports all server configs
# → Optionally includes credentials (encrypted)

aiterm mcp export --profile=research
# → Exports only research-related servers

aiterm mcp import team-mcp-config.json
# → Installs all servers
# → Prompts for credentials
# → Validates each one
```

**Implementation:**

```python
# src/aiterm/mcp/
├── manager.py       # MCP server management
├── installer.py     # Install from marketplace
├── validator.py     # Config validation
├── tester.py        # Connection testing
├── oauth.py         # OAuth flows
└── marketplace.py   # API client for marketplace

# Integration with existing registry
MARKETPLACE_URLS = [
    "https://mcp.run/servers",           # Official registry
    "https://glama.ai/mcp/servers",      # Community registry
]
```

**MCP Marketplace API:**
```python
async def search_servers(query: str, category: str = None) -> List[Server]:
    # Search across registries
    pass

async def get_server_info(server_id: str) -> ServerInfo:
    # Get detailed info
    pass

async def download_server(server_id: str) -> Path:
    # Download and verify
    pass
```

**Effort:** 🏗️ MASSIVE (2-3 weeks)
**Priority:** 🔥🔥🔥 HIGHEST (biggest value-add)

---

### 2.3 Plugin Management ⭐⭐

**Current State:** Manual plugin installation
**Vision:** Plugin marketplace with search, install, update

**Commands:**

```bash
aiterm plugin search "code review"
# Output:
# 🔍 Found 5 plugins:
#
# ⭐ pr-review-toolkit (Official)
#    Comprehensive PR review with specialized agents
#    Downloads: 12k | Rating: ⭐⭐⭐⭐⭐ (4.9/5)
#    Skills: review-pr, code-reviewer, type-design-analyzer
#
# code-quality-checker (Community)
#    Lint and quality checks
#    Downloads: 3.2k | Rating: ⭐⭐⭐⭐ (4.3/5)

aiterm plugin install pr-review-toolkit
# → Downloads plugin
# → Installs to ~/.claude/plugins/
# → Registers skills

aiterm plugin list
# Output:
# Installed Plugins:
#
# ✅ pr-review-toolkit (v1.2.0)
#    Skills: 5 skills
#    Agents: 3 agents
#    Commands: 1 command
#
# ✅ feature-dev (v2.0.1)
#    Skills: 3 skills
#    Agents: 3 agents

aiterm plugin update pr-review-toolkit
# → Checks for updates
# → Shows changelog
# → Updates if available

aiterm plugin info pr-review-toolkit
# → Shows detailed info
# → Lists all components
# → Shows usage stats

aiterm plugin validate
# → Validates ALL plugins
# → Checks plugin.json schema
# → Tests skill invocation

aiterm plugin create my-plugin
# → Interactive wizard
# → Scaffolds plugin structure
# → Creates plugin.json
```

**Effort:** 🔧 Medium (1 week)
**Priority:** Medium (plugins less common than MCP servers)

---

### 2.4 Agent Management ⭐

**Current State:** No agent management
**Vision:** Configure, test, and manage subagents

**Commands:**

```bash
aiterm agent list
# Output:
# Available Agents:
#
# Built-in:
# - Explore (fast codebase exploration)
# - Plan (software architect)
# - claude-code-guide (documentation lookup)
#
# Custom:
# - statistical-analyst (your custom agent)
# - research-assistant (your custom agent)

aiterm agent create statistical-analyst
# → Interactive wizard:
#
# Agent Creator
# ─────────────
# Name: statistical-analyst
# Description: Analyzes statistical methods and results
#
# Allowed Tools (select):
# [x] Read
# [x] Bash
# [ ] Write (read-only agent)
# [ ] Edit
#
# Model: sonnet (faster) / opus (smarter): sonnet
#
# System Prompt:
# You are an expert statistician...
#
# ✨ Created: ~/.claude/agents/statistical-analyst.json

aiterm agent test statistical-analyst
# → Runs test invocation
# → Shows example conversation
# → Validates tool usage

aiterm agent config statistical-analyst --edit
# → Opens in $EDITOR

aiterm agent validate
# → Validates all agent configs
```

**Effort:** ⚡ Quick (2-3 days)
**Priority:** Low (agents less commonly customized)

---

### 2.5 Custom Command Management ⭐⭐

**Current State:** Manual COMMAND.md files
**Vision:** Template system with validation

**Commands:**

```bash
aiterm command list
# Output:
# Custom Commands:
#
# Slash Commands (16):
# /research:literature, /research:cite, /research:methods
# /code:debug, /code:test, /code:review
# /teach:grade, /teach:feedback, /teach:rubric
# [...]
#
# Skills (24):
# research:manuscript, research:hypothesis
# code:rpkg-check, code:test-gen
# [...]

aiterm command create /research:summarize
# → Interactive wizard:
#
# Command Creator
# ───────────────
# Type: Slash Command
# Name: /research:summarize
# Description: Summarize research papers
#
# Supporting files needed? (y/n): y
# - templates/summary-template.md
#
# Allowed tools:
# [x] Read (to read papers)
# [x] WebFetch (to fetch papers)
# [ ] Write
#
# ✨ Created: ~/.claude/commands/research/summarize/COMMAND.md

aiterm command test /research:summarize
# → Dry-run test
# → Shows what would happen

aiterm command validate
# → Validates ALL commands
# → Checks frontmatter
# → Verifies supporting files exist

aiterm command import ~/my-commands/
# → Imports custom commands
# → Validates each one
# → Registers with Claude

aiterm command export --output=my-commands.tar.gz
# → Exports all custom commands
# → For sharing with team
```

**Template Library:**

```bash
aiterm command templates
# Output:
# Available Templates:
#
# Research:
# - literature-review
# - citation-formatter
# - methods-writer
#
# Development:
# - code-reviewer
# - test-generator
# - documentation-writer
#
# Teaching:
# - assignment-grader
# - feedback-generator
# - rubric-creator

aiterm command create --template=code-reviewer my-reviewer
# → Creates from template
# → Customizes for your needs
```

**Effort:** 🔧 Medium (3-5 days)
**Priority:** Medium (commands less used than MCP servers)

---

## PART 3: Gemini CLI Integration ⭐

**Vision:** Everything that works for Claude Code also works for Gemini CLI

**Commands:**

```bash
aiterm gemini settings
# → Shows Gemini config

aiterm gemini init
# → Sets up Gemini CLI integration

aiterm switch gemini
# → Switches terminal profile to Gemini mode
# → Updates StatusLine to show "Gemini 1.5 Pro"

aiterm switch claude
# → Switches back to Claude mode

aiterm gemini mcp install postgres-mcp
# → Installs MCP server for Gemini
# → (if Gemini supports MCP in future)
```

**Cross-Tool Features:**

```bash
aiterm quota --all
# Output:
# API Quota Summary:
#
# Claude Code (Sonnet 4.5):
# - Today: $2.45 / $50.00 (4.9%)
# - This week: $12.30 / $200.00 (6.2%)
# - This month: $45.67 / $500.00 (9.1%)
#
# Gemini CLI (Pro 1.5):
# - Today: $0.89 / $20.00 (4.5%)
# - This week: $5.32 / $80.00 (6.7%)
# - This month: $18.45 / $300.00 (6.2%)
#
# Total spent this month: $64.12

aiterm context switch --tool=gemini
# → Detects project context
# → Switches terminal to Gemini profile
# → Updates StatusLine

aiterm recommend
# Output:
# 📊 R Package Project Detected
#
# Recommended AI Tool: Claude Code
# Why: Better for coding tasks, R support
#
# Alternative: Gemini CLI
# When to use: Research, literature review
```

**Effort:** 🏗️ Large (1-2 weeks, depends on Gemini API)
**Priority:** Low (focus on Claude first)

---

## PART 4: Workflow Automation ⭐⭐

### 4.1 Context-Aware Recommendations

**Vision:** aiterm suggests optimal setup based on what you're doing

**Examples:**

```bash
cd ~/projects/r-packages/medfit
aiterm recommend

# Output:
# 📦 R Package Project: medfit
#
# Recommended Setup:
#
# Terminal Profile: R-Dev ✅ (already active)
#
# MCP Servers:
# ⚠️  r-execution - Not installed
#    Why: Execute R code, run devtools::check()
#    Install: aiterm mcp install r-execution
#
# ✅ filesystem - Active
# ✅ github - Active
#
# Custom Commands:
# ⭐ /code:rpkg-check - Run R CMD check
# ⭐ /code:rpkg-test - Run testthat tests
# ⭐ /code:rpkg-document - Update documentation
#
# Hooks:
# ⭐ auto-test-runner - Run tests after edits
#    Install: aiterm hooks install auto-test-runner
#
# Apply all recommendations? [Y/n]
```

**Machine Learning (Future):**
```python
# Learn from your behavior
# - Which MCP servers do you use for which projects?
# - Which commands do you invoke most often?
# - What terminal profiles do you prefer?

# Suggest based on patterns
# - "You usually use postgres-mcp for this type of project"
# - "Last time you worked on medfit, you used /code:rpkg-check"
```

**Effort:** 🔧 Medium (rule-based), 🏗️ Large (ML-based)
**Priority:** Medium

---

### 4.2 Session Management

**Vision:** Track and resume AI coding sessions

**Commands:**

```bash
aiterm session list
# Output:
# Recent Sessions:
#
# 1. medfit R package (2h ago) - Claude Code
#    Duration: 45 min | Cost: $1.23 | Lines: +234/-89
#    Status: In progress
#
# 2. aiterm docs (1 day ago) - Claude Code
#    Duration: 2h 15min | Cost: $4.56 | Lines: +567/-123
#    Status: Completed
#
# 3. Literature review (3 days ago) - Gemini CLI
#    Duration: 1h 30min | Cost: $0.45
#    Status: Completed

aiterm session show <id>
# → Shows detailed session info
# → Commands run
# → Files modified
# → Cost breakdown

aiterm session resume <id>
# → Restores context
# → Switches terminal profile
# → Loads project files

aiterm session export <id> --format=json
# → Exports session data
# → For analysis/backup
```

**Effort:** 🏗️ Large (1-2 weeks)
**Priority:** Low (nice-to-have)

---

### 4.3 Quota Tracking & Alerts ⭐

**Vision:** Proactive quota management

**Features:**

```bash
aiterm quota show
# Output:
# 💰 API Quota Summary
# ──────────────────
# Today: $2.45 / $50.00 (4.9%) ████░░░░░░
# Week:  $12.30 / $200.00 (6.2%) ██░░░░░░░░
# Month: $45.67 / $500.00 (9.1%) ██░░░░░░░░
#
# Projects:
# - medfit: $15.34 (33.6%)
# - aiterm: $12.45 (27.3%)
# - teaching: $8.92 (19.5%)
# - [others]: $8.96 (19.6%)

aiterm quota set --daily=50 --weekly=200 --monthly=500
# → Sets quota limits

aiterm quota alert --threshold=80
# → Sends notification at 80% usage

aiterm quota export --format=csv
# → Exports usage data for analysis
```

**Integration with Existing `qu` Command:**
```bash
# Your existing ZSH command
qu

# Could call aiterm under the hood
alias qu='aiterm quota show'
```

**Effort:** ⚡ Quick (2-3 days)
**Priority:** High (cost management is important!)

---

### 4.4 Template Library

**Vision:** Pre-built workflows for common tasks

**Categories:**

1. **Research Workflows**
   - Literature review template
   - Manuscript writing template
   - Statistical analysis template

2. **R Package Development**
   - New package setup
   - CRAN submission checklist
   - Pkgdown site template

3. **Teaching Workflows**
   - Course setup template
   - Assignment creation template
   - Grading workflow template

**Commands:**

```bash
aiterm template list
# Shows all available templates

aiterm template search "R package"
# Searches templates

aiterm template apply r-package-new
# → Interactive wizard
# → Sets up MCP servers
# → Installs hooks
# → Creates custom commands
# → Configures terminal profile
```

**Effort:** 🔧 Medium (1 week)
**Priority:** Low (nice-to-have)

---

## PART 5: Technical Architecture

### 5.1 Plugin System Architecture

```
aiterm/
├── core/                    # Core functionality
│   ├── cli.py              # Main CLI (Typer)
│   ├── config.py           # Config management
│   └── api.py              # Internal API
├── terminal/                # Terminal integration
│   ├── base.py
│   ├── iterm2.py
│   ├── warp.py
│   └── detector.py
├── claude/                  # Claude Code integration
│   ├── settings.py         # Settings management (existing)
│   ├── hooks.py            # Hook management (NEW)
│   ├── mcp.py              # MCP server management (NEW)
│   ├── plugins.py          # Plugin management (NEW)
│   ├── agents.py           # Agent management (NEW)
│   └── commands.py         # Custom command management (NEW)
├── gemini/                  # Gemini CLI integration
│   ├── settings.py
│   ├── mcp.py
│   └── commands.py
├── workflow/                # Workflow automation
│   ├── recommender.py      # Context-aware recommendations
│   ├── quota.py            # Quota tracking
│   └── session.py          # Session management
└── utils/
    ├── marketplace.py      # Marketplace API client
    ├── validator.py        # Schema validation
    └── installer.py        # Package installation
```

### 5.2 Data Model

```python
# Configuration
class AitermConfig:
    terminal: TerminalConfig
    claude: ClaudeConfig
    gemini: GeminiConfig
    workflow: WorkflowConfig

# Claude Code
class ClaudeConfig:
    settings_path: Path
    hooks: List[Hook]
    mcp_servers: List[MCPServer]
    plugins: List[Plugin]
    agents: List[Agent]
    commands: List[Command]

# MCP Server
class MCPServer:
    id: str
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    status: ServerStatus  # Running | Stopped | Error
    tools: List[Tool]

# Hook
class Hook:
    id: str
    name: str
    type: HookType  # PreToolUse | PostToolUse | etc.
    path: Path
    enabled: bool
    config: Dict[str, Any]
```

### 5.3 API Design

**JSON Output for All Commands:**
```bash
aiterm mcp list --json
# {
#   "servers": [
#     {
#       "id": "filesystem",
#       "status": "running",
#       "tools": ["read_file", "write_file"]
#     }
#   ]
# }

aiterm hooks list --json
# {
#   "hooks": [
#     {
#       "id": "prompt-optimizer",
#       "type": "UserPromptSubmit",
#       "enabled": true
#     }
#   ]
# }
```

**Python API (for integration):**
```python
from aiterm import Aiterm

# Initialize
at = Aiterm()

# MCP management
servers = await at.mcp.list()
await at.mcp.install("postgres-mcp")
status = await at.mcp.test("postgres-mcp")

# Hook management
hooks = await at.hooks.list()
await at.hooks.install("auto-test-runner")

# Terminal integration
await at.terminal.switch_profile("Python-Dev")
context = await at.terminal.detect_context()
```

---

## PART 6: Prioritized Implementation Roadmap

### Phase 1: Foundation (v0.2.0) - Week 1-2 🔥

**Focus:** Core management features

**Tasks:**
1. ✅ Keep existing v0.1.0 features (context, profiles, settings)
2. ⭐⭐⭐ MCP Server Management (HIGHEST PRIORITY)
   - `aiterm mcp list|install|test|config`
   - Marketplace integration (mcp.run, glama.ai)
   - OAuth flows for auth
   - **Effort:** 2 weeks
3. ⭐⭐⭐ Hook Management (HIGHEST PRIORITY)
   - `aiterm hooks list|install|test|validate`
   - Template library (10 built-in hooks)
   - **Effort:** 1-2 weeks
4. ⭐ StatusLine Builder (Wizard)
   - `aiterm statusbar init` (interactive wizard)
   - **Effort:** 3-5 days
5. ⭐ Quota Tracking
   - `aiterm quota show|set|alert`
   - **Effort:** 2-3 days

**Deliverable:** v0.2.0 with killer MCP + Hook management

---

### Phase 2: Expansion (v0.3.0) - Week 3-4 🚀

**Focus:** Multi-terminal + More management

**Tasks:**
1. ⭐⭐ Multi-Terminal Support
   - Warp integration
   - Alacritty integration
   - **Effort:** 1 week
2. ⭐ Plugin Management
   - `aiterm plugin list|install|update`
   - **Effort:** 1 week
3. ⭐ Custom Command Management
   - `aiterm command list|create|validate`
   - Template library
   - **Effort:** 3-5 days
4. Agent Management
   - `aiterm agent list|create|test`
   - **Effort:** 2-3 days

**Deliverable:** v0.3.0 with multi-terminal + full management suite

---

### Phase 3: Intelligence (v0.4.0) - Week 5-6 🧠

**Focus:** Recommendations + Automation

**Tasks:**
1. Context-Aware Recommendations
   - `aiterm recommend` (rule-based)
   - **Effort:** 1 week
2. StatusLine Builder (TUI)
   - Interactive TUI with live preview
   - **Effort:** 1 week
3. Session Management
   - `aiterm session list|resume|export`
   - **Effort:** 3-5 days
4. Template Library
   - Pre-built workflows
   - **Effort:** 3-5 days

**Deliverable:** v0.4.0 with intelligent recommendations

---

### Phase 4: Gemini + ML (v1.0.0) - Month 2-3 🌟

**Focus:** Cross-tool + Machine learning

**Tasks:**
1. Gemini CLI Integration
   - Full parity with Claude features
   - **Effort:** 1-2 weeks
2. Machine Learning Recommendations
   - Learn from usage patterns
   - Personalized suggestions
   - **Effort:** 2-3 weeks
3. Advanced Analytics
   - Cost optimization
   - Usage patterns
   - **Effort:** 1 week
4. Public Release
   - PyPI package
   - Homebrew formula
   - Documentation site
   - **Effort:** 1 week

**Deliverable:** v1.0.0 public release

---

## PART 7: Success Metrics

### v0.2.0 Success (Week 2)
- [ ] MCP management working (install, test, validate)
- [ ] Hook management working (install, test, validate)
- [ ] StatusLine wizard working
- [ ] Quota tracking working
- [ ] 5+ MCP servers in marketplace
- [ ] 10+ hooks in template library

### v0.3.0 Success (Week 4)
- [ ] 3+ terminals supported (iTerm2, Warp, Alacritty)
- [ ] Plugin management working
- [ ] Command management working
- [ ] Agent management working

### v1.0.0 Success (Month 3)
- [ ] 100+ external users
- [ ] PyPI package published
- [ ] 20+ MCP servers in marketplace
- [ ] 30+ hooks in template library
- [ ] Gemini CLI integration working
- [ ] 4.5+ star rating on GitHub

---

## PART 8: Quick Wins vs Long-term

### ⚡ Quick Wins (This Week)

1. **Quota Tracking** (2-3 days)
   - `aiterm quota show`
   - Integrates with existing `qu` command
   - **Impact:** Immediate value, cost management

2. **MCP List/Status** (2-3 days)
   - `aiterm mcp list`
   - `aiterm mcp status <server>`
   - **Impact:** Visibility into existing setup

3. **Hook Validator** (2-3 days)
   - `aiterm hooks validate`
   - Checks syntax, schema
   - **Impact:** Catch errors early

### 🏗️ Long-term Projects (Weeks)

1. **MCP Marketplace** (2 weeks)
   - Full discovery, install, test workflow
   - **Impact:** Game-changer for MCP adoption

2. **Hook Marketplace** (1-2 weeks)
   - Template library with testing
   - **Impact:** Democratizes hook creation

3. **Multi-Terminal** (1 week)
   - Warp, Alacritty support
   - **Impact:** Broader audience

---

## PART 9: Open Questions for Discussion

1. **Should aiterm absorb CLAUDE.md management?**
   - Option A: Yes - `aiterm claude init` creates CLAUDE.md
   - Option B: No - keep in zsh-configuration
   - **Recommendation:** A (makes sense for "Claude Code management")

2. **Should aiterm manage context detection?**
   - Option A: Yes - aiterm is source of truth
   - Option B: No - delegate to zsh-configuration
   - **Recommendation:** A (Python is better than shell for this)

3. **How to handle credentials for MCP servers?**
   - Option A: Store in settings.json (current)
   - Option B: Use system keychain (more secure)
   - Option C: Prompt every time (most secure, annoying)
   - **Recommendation:** B (use keychain)

4. **Should aiterm have a TUI mode?**
   - Option A: Yes - full TUI interface (like lazygit)
   - Option B: No - stay CLI-only
   - Option C: Hybrid - TUI for some features (statusbar builder)
   - **Recommendation:** C (TUI for complex interactions)

5. **Pricing model for marketplace?**
   - Option A: All free (community-driven)
   - Option B: Freemium (basic free, premium paid)
   - Option C: Curation fee (verified hooks cost $)
   - **Recommendation:** A for now (community first)

---

## PART 10: Final Vision Statement

**aiterm is THE command-line tool that makes AI-assisted development workflows effortless.**

### What Makes aiterm Unique?

1. **Comprehensive Management**
   - MCP servers, hooks, plugins, agents, commands
   - All in one tool, consistent interface

2. **Terminal Integration**
   - Multi-terminal support
   - Context-aware profile switching
   - Beautiful StatusLine

3. **Intelligence Built-in**
   - Context-aware recommendations
   - Quota tracking & alerts
   - Usage analytics

4. **Developer-Friendly**
   - Python-based (testable, maintainable)
   - PyPI installable (easy distribution)
   - JSON API (integration-ready)

5. **ADHD-Optimized**
   - Quick wins (quota tracking, MCP status)
   - Clear commands (no ambiguity)
   - Beautiful output (Rich library)

### The Pitch

> **"npm for AI coding tools"**
>
> Just like npm makes JavaScript package management effortless,
> aiterm makes AI coding tool management effortless.
>
> Install MCP servers like packages.
> Discover hooks like browsing npm.
> Configure everything from one CLI.

---

**Last Updated:** 2025-12-19
**Status:** 🟡 Awaiting decision on focused scope
**Next Action:** Choose Phase 1 priorities, start implementation
