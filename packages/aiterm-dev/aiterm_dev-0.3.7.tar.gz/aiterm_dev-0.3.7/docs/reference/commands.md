# CLI Reference

Complete reference for all **aiterm** commands with examples.

---

## Global Options

```bash
aiterm --help              # Show help message
aiterm --version           # Show version info (enhanced in v0.3.5)
aiterm --install-completion  # Install shell completion
aiterm --show-completion    # Show completion script
```

### Enhanced `--version` (v0.3.5+)

```bash
aiterm --version
```

**Output:**
```
aiterm 0.3.5
Python: 3.12.0
Platform: macOS-15.2-arm64
Path: /Users/dt/.local/bin/aiterm
```

Shows version, Python runtime, platform, and installation path.

---

## Core Commands

### `aiterm doctor`

Check aiterm installation and configuration health.

```bash
aiterm doctor
```

**Output:**
```
aiterm doctor - Health check

Terminal: iTerm.app
Shell: /bin/zsh
Python: 3.12.0
aiterm: 0.3.5

Basic checks passed!
```

**What it checks:**
- Terminal type (iTerm2 detection)
- Shell environment
- Python version
- aiterm installation

---

### `aiterm hello`

Diagnostic greeting command (added in v0.3.5).

```bash
aiterm hello              # Default greeting
aiterm hello --name "DT"  # Personalized greeting
```

**Output:**
```
👋 Hello from aiterm!
Version: 0.3.5
Terminal: iTerm.app
```

**With name:**
```
👋 Hello, DT!
Version: 0.3.5
Terminal: iTerm.app
```

Useful for verifying aiterm is installed and working correctly.

---

### `aiterm goodbye`

Farewell diagnostic command (added in v0.3.5).

```bash
aiterm goodbye              # Default farewell
aiterm goodbye --name "DT"  # Personalized farewell
```

**Output:**
```
👋 Goodbye from aiterm!
Thanks for using aiterm 0.3.5
```

Pair with `hello` for quick installation testing.

---

### `aiterm info`

Display detailed system diagnostics (added in v0.3.5).

```bash
aiterm info              # Full system info
aiterm info --json       # Output as JSON
```

**Output:**
```
aiterm System Information

Version: 0.3.5
Python: 3.12.0
Platform: macOS-15.2-arm64
Path: /Users/dt/.local/bin/aiterm

Environment:
  TERM_PROGRAM: iTerm.app
  SHELL: /bin/zsh
  CLAUDECODE: 1

Claude Code:
  Settings: ~/.claude/settings.json
  Hooks: 3 configured
  Permissions: 47 allowed
```

**JSON output:**
```bash
aiterm info --json | jq '.version'
# "0.3.5"
```

Useful for debugging, issue reports, and scripting.

---

### `aiterm init`

Interactive setup wizard (coming in v0.1.0 final).

```bash
aiterm init
```

**What it will do:**
- Detect terminal type
- Install base profiles
- Configure context detection
- Test installation

**Current status:** Placeholder (shows preview of features)

---

## Context Detection

### `aiterm detect [PATH]`

Detect project context for a directory.

```bash
# Current directory
aiterm detect

# Specific directory
aiterm detect ~/projects/my-app

# Short alias
ait detect
```

**Example output:**
```
Context Detection
┌────────────┬──────────────────────────┐
│ Directory  │ /Users/dt/projects/webapp│
│ Type       │ 📦 node                  │
│ Name       │ webapp                   │
│ Profile    │ Node-Dev                 │
│ Git Branch │ main *                   │
└────────────┴──────────────────────────┘
```

**Detects 8 context types:**
- 🚨 Production (`/production/`, `/prod/`)
- 🤖 AI Session (`/claude-sessions/`, `/gemini-sessions/`)
- 📦 R Package (`DESCRIPTION` file)
- 🐍 Python (`pyproject.toml`)
- 📦 Node.js (`package.json`)
- 📊 Quarto (`_quarto.yml`)
- 🔧 Emacs (`.spacemacs`)
- 🛠️ Dev Tools (`.git` + `scripts/`)

---

### `aiterm switch [PATH]`

Detect and apply context to terminal (iTerm2 only).

```bash
# Switch current directory context
aiterm switch

# Switch to specific directory
aiterm switch ~/production/live-site

# Short alias
ait switch
```

**What it does:**
1. Detects project context
2. Switches iTerm2 profile (colors)
3. Sets tab title with project name + git branch
4. Updates status bar variables

**Example:**
```bash
cd ~/production/myapp
ait switch
# → iTerm2 switches to Production profile (RED!)
# → Tab title: "🚨 production: myapp [main]"
```

---

### `aiterm context`

Subcommands for context management.

#### `aiterm context detect [PATH]`

Same as `aiterm detect` (full form).

```bash
aiterm context detect ~/projects/myapp
```

#### `aiterm context show`

Show current directory context (alias for `detect`).

```bash
aiterm context show
```

#### `aiterm context apply [PATH]`

Same as `aiterm switch` (full form).

```bash
aiterm context apply ~/projects/myapp
```

---

## Profile Management

### `aiterm profile list`

List available profiles (v0.2.0 feature preview).

```bash
aiterm profile list
```

**Output:**
```
Available Profiles:
  - default (iTerm2 base)
  - ai-session (Claude Code / Gemini)
  - production (warning colors)

Profile management coming in v0.2.0
```

**Coming in v0.2.0:**
- `aiterm profile show <name>` - Show profile details
- `aiterm profile install <name>` - Install profile template
- `aiterm profile create` - Interactive profile creator

---

## Claude Code Integration

### `aiterm claude settings`

Display current Claude Code settings.

```bash
aiterm claude settings
```

**Output:**
```
Claude Code Settings
┌───────────────────┬───────────────────────────┐
│ File              │ ~/.claude/settings.json   │
│ Permissions (allow)│ 47                       │
│ Permissions (deny) │ 0                        │
│ Hooks             │ 2                         │
└───────────────────┴───────────────────────────┘

Allowed:
  ✓ Bash(git status:*)
  ✓ Bash(git diff:*)
  ... and 45 more
```

---

### `aiterm claude backup`

Backup Claude Code settings with timestamp.

```bash
aiterm claude backup
```

**Output:**
```
✓ Backup created: ~/.claude/settings.backup-20241218-153045.json
```

**Backup format:**
- Location: Same directory as settings file
- Naming: `settings.backup-YYYYMMDD-HHMMSS.json`
- Automatic timestamping

---

### `aiterm claude approvals`

Manage auto-approval permissions.

#### `aiterm claude approvals list`

List current auto-approval permissions.

```bash
aiterm claude approvals list
```

**Output:**
```
Auto-Approvals (~/.claude/settings.json)

Allowed:
  ✓ Bash(git add:*)
  ✓ Bash(git commit:*)
  ✓ Bash(git diff:*)
  ✓ Bash(git log:*)
  ✓ Bash(git status:*)
  ✓ Bash(pytest:*)
  ✓ Bash(python3:*)
  ✓ Read(/Users/dt/**)
  ✓ WebSearch
```

---

#### `aiterm claude approvals presets`

List available approval presets.

```bash
aiterm claude approvals presets
```

**Output:**
```
Available Presets
┌────────────┬──────────────────────────────────┬─────────────┐
│ Name       │ Description                      │ Permissions │
├────────────┼──────────────────────────────────┼─────────────┤
│ safe-reads │ Read-only operations             │ 5           │
│ git-ops    │ Git commands                     │ 12          │
│ github-cli │ GitHub CLI operations            │ 8           │
│ python-dev │ Python development tools         │ 6           │
│ node-dev   │ Node.js development tools        │ 7           │
│ r-dev      │ R development tools              │ 5           │
│ web-tools  │ Web search and fetch             │ 2           │
│ minimal    │ Basic shell commands only        │ 10          │
└────────────┴──────────────────────────────────┴─────────────┘
```

---

#### `aiterm claude approvals add <preset>`

Add a preset to auto-approvals.

```bash
# Add safe read permissions
aiterm claude approvals add safe-reads

# Add Python dev tools
aiterm claude approvals add python-dev

# Add git operations
aiterm claude approvals add git-ops
```

**Output:**
```
✓ Added 6 permissions from 'python-dev':
  + Bash(python3:*)
  + Bash(pip3 install:*)
  + Bash(pytest:*)
  + Bash(python -m pytest:*)
  + Bash(uv:*)
  + Bash(uv pip install:*)
```

**Features:**
- Automatic backup before changes
- Duplicate detection (won't add existing permissions)
- Shows exactly what was added

**Available presets:**

**safe-reads** (5 permissions)
- Read-only file operations
- Non-destructive commands

**git-ops** (12 permissions)
- Git status, diff, log
- Git add, commit, push
- Git checkout, branch operations
- No destructive git commands

**github-cli** (8 permissions)
- `gh pr list/view/create`
- `gh issue list/view`
- `gh api` (read-only)
- No `gh pr merge` without confirmation

**python-dev** (6 permissions)
- pytest, python3, pip3
- uv pip install
- Standard Python tooling

**node-dev** (7 permissions)
- npm install/run
- npx commands
- bun operations

**r-dev** (5 permissions)
- Rscript, R CMD
- quarto commands

**web-tools** (2 permissions)
- WebSearch
- WebFetch (read-only)

**minimal** (10 permissions)
- Basic shell: ls, cat, echo
- Safe navigation: cd, pwd
- No write/modify operations

---

## OpenCode Integration

### `aiterm opencode config`

Display current OpenCode configuration.

```bash
aiterm opencode config
aiterm opencode config --raw    # Output as JSON
```

---

### `aiterm opencode validate`

Validate OpenCode configuration against schema.

```bash
aiterm opencode validate
```

---

### `aiterm opencode backup`

Backup OpenCode configuration with timestamp.

```bash
aiterm opencode backup
```

---

### `aiterm opencode servers`

Manage MCP server configurations.

#### `aiterm opencode servers list`

List all configured MCP servers.

```bash
aiterm opencode servers list
```

#### `aiterm opencode servers enable <name>`

Enable a disabled server.

```bash
aiterm opencode servers enable github
aiterm opencode servers enable sequential-thinking
```

#### `aiterm opencode servers disable <name>`

Disable an enabled server.

```bash
aiterm opencode servers disable playwright
```

#### `aiterm opencode servers test <name>`

Test if a server can start successfully.

```bash
aiterm opencode servers test filesystem
aiterm opencode servers test time --timeout 5
```

**Output:**
```
Testing filesystem...
Command: npx -y @modelcontextprotocol/server-filesystem /Users/dt
✓ Server 'filesystem' started successfully
```

#### `aiterm opencode servers health`

Check health of all enabled servers.

```bash
aiterm opencode servers health          # Check enabled servers
aiterm opencode servers health --all    # Check all servers
```

**Output:**
```
                           MCP Server Health
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Server              ┃ Enabled ┃ Status ┃ Details                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ filesystem          │ yes     │ ✓ OK   │ Started successfully       │
│ memory              │ yes     │ ✓ OK   │ Started successfully       │
│ github              │ yes     │ ✓ OK   │ Started successfully       │
└─────────────────────┴─────────┴────────┴────────────────────────────┘
Summary: 3 ok, 0 errors
```

#### `aiterm opencode servers templates`

List available MCP server templates.

```bash
aiterm opencode servers templates
```

**Available templates:**
- `filesystem` - File system read/write access
- `memory` - Persistent context memory
- `sequential-thinking` - Complex reasoning chains
- `playwright` - Browser automation
- `time` - Timezone tracking
- `github` - PR/issue management (requires GITHUB_TOKEN)
- `brave-search` - Web search (requires BRAVE_API_KEY)
- `slack` - Slack integration (requires SLACK_TOKEN)
- `sqlite` - SQLite database access
- `puppeteer` - Headless browser
- `fetch` - HTTP fetch for web content
- `everything` - Demo server (testing only)

#### `aiterm opencode servers add <name>`

Add a new MCP server configuration.

```bash
# Add from template
aiterm opencode servers add brave-search --template

# Add with custom command
aiterm opencode servers add myserver --command "npx -y my-mcp-server"

# Add disabled
aiterm opencode servers add sqlite --template --disabled
```

#### `aiterm opencode servers remove <name>`

Remove an MCP server configuration.

```bash
aiterm opencode servers remove myserver
aiterm opencode servers remove filesystem --force  # Force remove essential
```

---

### `aiterm opencode agents`

Manage custom agent configurations.

#### `aiterm opencode agents list`

List configured agents.

```bash
aiterm opencode agents list
```

#### `aiterm opencode agents add <name>`

Add a new custom agent.

```bash
aiterm opencode agents add quick --desc "Fast responses" --model anthropic/claude-haiku-4-5
```

#### `aiterm opencode agents remove <name>`

Remove a custom agent.

```bash
aiterm opencode agents remove quick
```

---

### `aiterm opencode models`

List recommended models for OpenCode.

```bash
aiterm opencode models
```

---

### `aiterm opencode set-model <model>`

Set the primary or small model.

```bash
aiterm opencode set-model anthropic/claude-opus-4-5           # Set primary
aiterm opencode set-model anthropic/claude-haiku-4-5 --small  # Set small model
```

---

## Examples

### Quick Setup for Claude Code

```bash
# 1. Check installation
ait doctor

# 2. View current settings
ait claude settings

# 3. Backup before changes
ait claude backup

# 4. Add safe permissions
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev

# 5. Verify
ait claude approvals list
```

### Context Switching Workflow

```bash
# Work on web app
cd ~/projects/webapp
ait switch
# → Node-Dev profile (green)

# Switch to API service
cd ~/projects/api
ait switch
# → Python-Dev profile (blue)

# Deploy to production
cd ~/production/live-site
ait switch
# → Production profile (RED!) 🚨
```

### R Package Development

```bash
# Navigate to R package
cd ~/r-packages/mypackage

# Check context
ait detect
# Shows: 📦 r-package → R-Dev profile

# Add R dev permissions
ait claude approvals add r-dev

# Apply context
ait switch
```

---

## Short Aliases

All commands support the `ait` shortalias:

```bash
ait --version              # = aiterm --version
ait doctor                 # = aiterm doctor
ait detect                 # = aiterm detect
ait switch                 # = aiterm switch
ait claude settings        # = aiterm claude settings
ait claude approvals list  # = aiterm claude approvals list
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | General error (missing file, invalid input) |
| 2    | Command failed (operation couldn't complete) |

---

## Environment Variables

**aiterm** respects these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `TERM_PROGRAM` | Terminal detection | `iTerm.app` |
| `SHELL` | Shell detection | `/bin/zsh` |
| `CLAUDECODE` | Claude Code detection | `1` |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.claude/settings.json` | Claude Code settings |
| `~/.claude/hooks/` | Claude Code hooks |
| `~/.config/aiterm/` | aiterm config (coming v0.2.0) |

---

## Next Steps

- **Workflows:** [Common use cases](../guide/workflows.md)
- **Claude Integration:** [Detailed integration guide](../guide/claude-integration.md)
- **Troubleshooting:** [Common issues and solutions](troubleshooting.md)
