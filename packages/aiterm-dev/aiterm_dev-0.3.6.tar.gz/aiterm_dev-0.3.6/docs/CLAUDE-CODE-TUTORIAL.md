# Claude Code CLI - Comprehensive Tutorial

**The Complete Guide to Anthropic's Official CLI for Claude**

*Based on official documentation from [code.claude.com](https://code.claude.com/docs)*
*Version: 2.0.71+ | Last Updated: December 2025*

---

## Table of Contents

1. [Installation & Setup](#1-installation-setup)
2. [Core Concepts](#2-core-concepts)
3. [Interactive Mode](#3-interactive-mode)
4. [Permission System](#4-permission-system)
5. [Slash Commands](#5-slash-commands)
6. [Configuration Deep Dive](#6-configuration-deep-dive)
7. [Hooks System](#7-hooks-system)
8. [MCP (Model Context Protocol)](#8-mcp-model-context-protocol)
9. [Plugins & Marketplaces](#9-plugins-marketplaces) *(extend Claude Code with community tools)*
10. [Advanced Workflows](#10-advanced-workflows)
11. [Real-World Examples](#11-real-world-examples)
12. [Troubleshooting](#12-troubleshooting)
13. [macOS-Specific Tips](#13-macos-specific-tips)
14. [Quick Reference](#14-quick-reference) *(with plain English explanations)*
15. [Glossary](#15-glossary-plain-english-definitions) *(definitions for beginners)*
16. [ADHD-Friendly Workflows](#16-adhd-friendly-workflows) *(focus strategies & templates)*

---

## 1. Installation & Setup

### 1.1 Installation Methods

#### Native Install (Recommended)

**macOS, Linux, WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Windows CMD:**
```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

#### Alternative Methods

**Homebrew (macOS):**
```bash
brew install --cask claude-code
```

**NPM (requires Node.js 18+):**
```bash
npm install -g @anthropic-ai/claude-code
```

### 1.2 Verify Installation

```bash
# Check version
claude --version

# Run health check
claude
> /doctor
```

### 1.3 Authentication

**First Launch:**
```bash
claude
# Follow prompts to authenticate
```

**Authentication Options:**

| Method | Best For | Cost Model |
|--------|----------|------------|
| **Claude.ai** | Individual developers | Subscription (Pro/Max) |
| **Claude Console** | API users, teams | Pre-paid credits |
| **Enterprise** | Organizations | Custom billing |

**Switch Accounts:**
```bash
> /login    # Switch to different account
> /logout   # Sign out completely
```

### 1.4 First-Time Setup

**Initialize a project:**
```bash
cd /your/project
claude
> /init
```

This creates `.claude/` directory with:
- `CLAUDE.md` - Project instructions for Claude
- `settings.json` - Project-specific settings

> **💡 Tip:** Run `/init` in every project you work on. The CLAUDE.md file helps Claude understand your project's conventions, which means less repetitive explaining and better code suggestions.
>
> **📋 DT's Workflow:** Each project type has different conventions. For R packages, CLAUDE.md should specify roxygen2 style, testthat usage, and tidyverse conventions. For Quarto manuscripts, specify citation style and figure conventions. For teaching materials, note the course level and student prerequisites.

**Example CLAUDE.md:**
```markdown
# Project: My Web App

## Tech Stack
- React 18 with TypeScript
- Node.js backend with Express
- PostgreSQL database

## Conventions
- Use functional components with hooks
- Follow Airbnb ESLint rules
- Write tests for all new features

## Important Files
- `src/App.tsx` - Main application entry
- `src/api/` - Backend API routes
- `prisma/schema.prisma` - Database schema
```

---

## 2. Core Concepts

### 2.1 How Claude Code Works

**In Plain English:** Claude Code is like having a senior developer sitting next to you who can actually type on your keyboard. You describe what you want, and Claude reads your code, makes changes, runs commands, and explains what it's doing - all while asking permission for anything risky.

Claude Code is an **agentic AI assistant** that can:

1. **Read** your codebase (files, directories, git history)
2. **Understand** project structure and conventions
3. **Execute** shell commands (with permission)
4. **Edit** files (with permission)
5. **Search** the web for documentation
6. **Connect** to external tools via MCP

**What "agentic" means:** Unlike a chatbot that just answers questions, Claude Code takes action. When you say "add a login button," it doesn't just tell you how - it actually creates the files, writes the code, and can even run tests to verify it works.

### 2.2 Context Management

**In Plain English:** "Context" is everything Claude remembers during your conversation - your files, your questions, its answers. Think of it like Claude's working memory. The more you talk, the more context fills up. Claude automatically manages this so you don't have to worry about it.

Claude Code automatically manages context by:
- Reading relevant files as needed
- Summarizing long conversations when memory gets full
- Tracking file changes during the session

**View context usage:**
```bash
> /context    # Visual grid showing how much "memory" is used
> /cost       # How many tokens (words) have been processed
```

**Why this matters:** If you're working on a huge codebase and have a very long conversation, Claude might need to summarize earlier parts to make room for new information. This happens automatically - you'll see a notification when it does.

### 2.3 Tools Available to Claude

**In Plain English:** "Tools" are the actions Claude can take. Some are safe (just looking at files), so Claude does them automatically. Others can change things (editing files, running commands), so Claude asks your permission first.

| Tool | What It Does (Plain English) | Needs Permission? |
|------|------------------------------|-------------------|
| `Read` | Look at what's inside a file | No - just looking |
| `Glob` | Find files by name pattern (like "all .js files") | No - just searching |
| `Grep` | Search for text inside files | No - just searching |
| `Write` | Create a new file or replace an existing one | **Yes** - changes things |
| `Edit` | Change specific parts of a file | **Yes** - changes things |
| `Bash` | Run terminal commands (like `npm install`) | **Yes** - can change things |
| `WebFetch` | Download content from a website | **Yes** - makes network requests |
| `WebSearch` | Search Google/Bing for information | **Yes** - makes network requests |
| `NotebookEdit` | Edit Jupyter notebook cells | **Yes** - changes things |

**Example of tools in action:**
```
You: "Find all the TODO comments in my code"
Claude: [Uses Grep tool - no permission needed]
        "I found 12 TODOs. Want me to show them?"

You: "Fix the first one"
Claude: "I'll edit src/utils.js to fix this TODO. Allow?"
        [You press Enter to approve]
        [Uses Edit tool to make the change]
```

### 2.4 The Conversation Model

```
┌─────────────────────────────────────────────────┐
│                   Session                        │
│  ┌─────────────────────────────────────────┐    │
│  │ Turn 1: User prompt                      │    │
│  │ Turn 2: Claude response + tool calls     │    │
│  │ Turn 3: User follow-up                   │    │
│  │ Turn 4: Claude response + tool calls     │    │
│  │ ...                                      │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  Context Window: ~200K tokens                    │
│  Auto-summarization when approaching limit       │
└─────────────────────────────────────────────────┘
```

---

## 3. Interactive Mode

### 3.1 Starting Sessions

> **💡 Tip:** The `-c` flag (continue) is your best friend. It resumes your last session with full context intact. Use it when you come back from a break, get distracted, or start a new terminal window.

```bash
# Basic start
claude

# Start with initial prompt
claude "explain this project"

# Start in specific directory
cd /path/to/project && claude

# Continue most recent conversation
claude -c
claude --continue

# Resume specific session
claude -r "session-name"
claude --resume "auth-refactor"
```

> **💡 Tip for ADHD:** Name your sessions with `/rename` as soon as you start working on something. Later, when you have 50 sessions, you'll thank yourself. "auth-refactor" is much easier to find than "session-2024-12-17-abc123".

### 3.2 Session Management

**Name your session:**
```bash
> /rename auth-refactor
```

#### Why Rename Sessions?

Without renaming, Claude Code generates cryptic session names like `session-2024-12-17-a3f2b1`. After a week of work, you'll have dozens of these, and finding "that conversation where I fixed the login bug" becomes impossible.

**Good session names are:**
- **Searchable:** Use keywords you'll remember (`stat440-hw3`, `rmediation-vignette`)
- **Project-prefixed:** Include the project name (`aiterm-hooks`, `collider-revision`)
- **Task-specific:** Describe what you're doing (`fix-auth-timeout`, `add-dark-mode`)

**Naming convention examples:**

| Project Type | Session Name Pattern | Example |
|--------------|---------------------|---------|
| R Package | `{package}-{task}` | `rmediation-bootstrap-ci` |
| Teaching | `{course}-{assignment}` | `stat440-lecture-week12` |
| Research | `{paper}-{section}` | `collider-reviewer2-response` |
| Dev Tools | `{tool}-{feature}` | `aiterm-context-detection` |
| Quarto | `{doc}-{task}` | `jasa-manuscript-figures` |
| Bug Fix | `fix-{issue}` | `fix-auth-timeout` |

> **📋 DT's Workflow:** With 30+ active projects across teaching, research, and dev-tools, named sessions are essential. When returning to a project after days or weeks, `/resume` + search lets you pick up exactly where you left off with full context intact.

**List sessions:**
```bash
> /resume    # Opens session picker
```

**Session Picker Shortcuts:**

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate sessions |
| `Enter` | Select session |
| `P` | Preview content |
| `R` | Rename session |
| `/` | Search/filter (type to find by name) |
| `Esc` | Exit picker |

> **💡 Tip:** Use `/` in the session picker to filter by name. If you've named sessions well, you can type `stat440` and instantly see all your teaching sessions for that course.

**Export conversation:**
```bash
> /export conversation.md    # Save to file
> /export                    # Copy to clipboard
```

> **📋 DT's Workflow:** Export conversations before major milestones. For research projects, export when submitting a paper. For teaching, export after creating assignments. These exports serve as documentation of your AI-assisted development process.

### 3.3 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `?` | Show all shortcuts |
| `Tab` | Command/file completion |
| `↑` / `↓` | Command history |
| `/` | Start slash command |
| `@` | Reference file/directory |
| `Shift+Tab` | Toggle permission mode |
| `Ctrl+O` | Toggle verbose mode |
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit Claude Code |

### 3.4 Input Methods

**Multi-line input:**

By default, pressing Enter sends your message immediately. But sometimes you need to write multiple lines (like pasting code blocks or writing detailed instructions). The `/terminal-setup` command installs a special keyboard binding so Shift+Enter creates a new line instead of sending.

```bash
# Step 1: Run terminal setup (one-time only)
claude
> /terminal-setup

# Step 2: Now you can use Shift+Enter for new lines
> Fix this function:          # First line
  function broken() {         # Shift+Enter for new line
    return null               # Shift+Enter again
  }                           # Press Enter to send all lines together
```

**What `/terminal-setup` actually does:**
- Detects your terminal type (iTerm2, VS Code, Terminal.app, etc.)
- Installs keyboard bindings specific to your terminal
- For iTerm2: Creates a key mapping in your iTerm2 preferences
- For VS Code: Updates keybindings.json
- Settings are permanent (survives restarts)

**Manual setup if `/terminal-setup` fails:**

For **iTerm2**:
1. Open iTerm2 → Preferences → Profiles → Keys → Key Mappings
2. Click `+` to add new mapping
3. Set "Keyboard Shortcut" to `Shift+Enter`
4. Action: "Send Text with vim Special Chars"
5. Value: `\n` (backslash-n, which means "new line")

For **VS Code integrated terminal**:
1. Open Command Palette (`Cmd+Shift+P`)
2. Search "Preferences: Open Keyboard Shortcuts (JSON)"
3. Add this entry:
```json
{
  "key": "shift+enter",
  "command": "workbench.action.terminal.sendSequence",
  "args": { "text": "\n" },
  "when": "terminalFocus"
}
```

For **Terminal.app** (macOS default):
- Unfortunately, Terminal.app doesn't support custom key bindings
- Workaround: Type your multi-line input in a text editor, then paste it
- Better solution: Install iTerm2 (`brew install --cask iterm2`)

**Reference files with @:**
```bash
> explain @src/utils/auth.js
> compare @old-version.js with @new-version.js
> what's in @src/components/
```

**Work with images:**
- Drag and drop images into terminal
- Paste with `Ctrl+V`
- Reference by path: `> analyze this screenshot @/path/to/image.png`

---

## 4. Permission System

### 4.1 Permission Modes Explained

#### `default` - Conservative Mode
```
✓ File reads: Auto-allowed
✗ File edits: Prompt every time
✗ Bash commands: Prompt every time
✗ Web requests: Prompt every time
```
**Use when:** Learning Claude Code, unfamiliar codebase

#### `acceptEdits` - Balanced Mode (Recommended)
```
✓ File reads: Auto-allowed
✓ File edits: Auto-allowed
✓ Allowed bash: Auto-allowed
? Unknown bash: Prompt
? Web requests: Based on allow list
```
**Use when:** Daily development, trusted projects

#### `plan` - Read-Only Mode
```
✓ File reads: Auto-allowed
✗ File edits: Blocked completely
✗ Bash commands: Blocked completely
✗ Web requests: Blocked completely
```
**Use when:** Code review, exploring unfamiliar code, understanding before changing

#### `dontAsk` - Restrictive Mode
```
✓ File reads: Auto-allowed
✓ Allowed tools: Auto-allowed
✗ Unknown tools: Auto-DENIED (no prompt)
```
**Use when:** Automated pipelines where you want predictable behavior

**Important:** `dontAsk` auto-DENIES unknown tools, it doesn't auto-allow them!

#### `delegate` - Sub-Agent Mode
```
✓ All tools: Work normally
✗ Output: Hidden from user
✗ GUI apps: Cannot launch
```
**Use when:** Never directly - only for programmatic sub-agents

**Warning:** If set as default, you won't see tool output!

#### `bypassPermissions` - Unrestricted Mode
```
✓ Everything: Auto-allowed without prompts
```
**Use when:** Only in sandboxed environments, CI/CD pipelines

### 4.2 Setting Permission Mode

**Per-session (CLI flag):**
```bash
claude --permission-mode plan
claude --permission-mode acceptEdits
```

**During session:**
```bash
> /config    # Open settings, change mode
# Or press Shift+Tab / Alt+M to toggle
```

**Default in settings.json:**
```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

### 4.3 Permission Rules

> **💡 Tip for ADHD:** Permission prompts can break your flow. Set up your allow list once (see examples below), and you'll rarely be interrupted. Start with `acceptEdits` mode for trusted projects.
>
> **📋 DT's Workflow:** Auto-approve language-specific commands for your stack. For R development: `Bash(Rscript:*)`, `Bash(R CMD:*)`, `Bash(quarto:*)`. For Python dev-tools: `Bash(python3:*)`, `Bash(pytest:*)`, `Bash(pip3:*)`. For teaching with Git: `Bash(git:*)`, `Bash(gh:*)`.

Permission rules use three categories:

```json
{
  "permissions": {
    "allow": [
      "Tool(pattern:*)"    // Auto-allow
    ],
    "ask": [
      "Tool(pattern:*)"    // Always prompt
    ],
    "deny": [
      "Tool(pattern:*)"    // Block completely
    ]
  }
}
```

#### Pattern Syntax

```json
{
  "permissions": {
    "allow": [
      // Exact command
      "Bash(npm test)",

      // Command with any arguments
      "Bash(git:*)",

      // Specific subcommand with arguments
      "Bash(npm run test:*)",

      // Multiple commands (use separate entries)
      "Bash(ls:*)",
      "Bash(cat:*)",

      // File patterns
      "Read(./docs/**)",           // All files in docs recursively
      "Read(./*.md)",              // Markdown files in root

      // Web patterns
      "WebFetch(domain:github.com)",
      "WebSearch"                   // All web searches
    ],
    "deny": [
      // Sensitive files
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./**/credentials*)",

      // Dangerous commands
      "Bash(rm -rf:*)",
      "Bash(sudo:*)"
    ]
  }
}
```

### 4.4 Building Your Allow List

**Start minimal, add as needed:**

```json
{
  "permissions": {
    "allow": [
      // Git operations (safe)
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git branch:*)",
      "Bash(git checkout:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git pull:*)",

      // File exploration (safe)
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(find:*)",
      "Bash(tree:*)",
      "Bash(wc:*)",

      // Development tools
      "Bash(npm:*)",
      "Bash(npx:*)",
      "Bash(yarn:*)",
      "Bash(pnpm:*)",
      "Bash(python3:*)",
      "Bash(pip:*)",
      "Bash(pytest:*)",

      // Web search
      "WebSearch"
    ],
    "defaultMode": "acceptEdits"
  }
}
```

**Language-specific additions:**

```json
// R Development
"Bash(Rscript:*)",
"Bash(R CMD:*)",
"Bash(R:*)",

// Quarto
"Bash(quarto:*)",

// Docker
"Bash(docker:*)",
"Bash(docker-compose:*)",

// Kubernetes
"Bash(kubectl:*)",
"Bash(helm:*)"
```

---

## 5. Slash Commands

### 5.1 Built-in Commands Reference

#### Session Management
| Command | Description | Example |
|---------|-------------|---------|
| `/clear` | Clear conversation history | `/clear` |
| `/resume [name]` | Resume previous session | `/resume auth-fix` |
| `/rename <name>` | Rename current session | `/rename feature-auth` |
| `/export [file]` | Export conversation | `/export chat.md` |
| `/exit` | Exit Claude Code | `/exit` |

#### Configuration
| Command | Description | Example |
|---------|-------------|---------|
| `/config` | Open settings interface | `/config` |
| `/status` | View current status | `/status` |
| `/permissions` | View/update permissions | `/permissions` |
| `/model` | Change AI model | `/model opus` |

#### Project
| Command | Description | Example |
|---------|-------------|---------|
| `/init` | Initialize CLAUDE.md | `/init` |
| `/memory` | Edit CLAUDE.md files | `/memory` |
| `/doctor` | Health check | `/doctor` |
| `/add-dir` | Add working directories | `/add-dir ../shared` |

#### Tools & Integrations
| Command | Description | Example |
|---------|-------------|---------|
| `/mcp` | Manage MCP servers | `/mcp` |
| `/agents` | Manage subagents | `/agents` |
| `/hooks` | Manage hooks | `/hooks` |
| `/ide` | IDE integration status | `/ide` |

#### Information
| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Get help | `/help` |
| `/cost` | Token usage | `/cost` |
| `/context` | Context visualization | `/context` |
| `/release-notes` | View updates | `/release-notes` |
| `/stats` | Usage statistics | `/stats` |

#### Special Modes
| Command | Description | Example |
|---------|-------------|---------|
| `/review` | Code review mode | `/review` |
| `/vim` | Vim-style editing | `/vim` |
| `/compact` | Compact conversation | `/compact focus on auth` |

### 5.2 Custom Slash Commands

#### Creating Project Commands

```bash
# Create commands directory
mkdir -p .claude/commands

# Create a simple command
cat > .claude/commands/optimize.md << 'EOF'
Analyze this code for performance issues and suggest optimizations.
Focus on:
1. Unnecessary re-renders
2. Memory leaks
3. Expensive operations
4. Missing memoization
EOF
```

**Usage:**
```bash
> /optimize
```

#### Creating Personal Commands

> **💡 Tip:** Personal commands in `~/.claude/commands/` are available in ALL projects. Put your most-used workflows here. Project-specific commands go in `.claude/commands/`.
>
> **📋 DT's Workflow:** Create domain-specific commands: `/r-check` runs R CMD check for packages, `/quarto-preview` renders and opens Quarto docs, `/teach-deploy` publishes course materials to GitHub Pages, `/research-status` checks .STATUS files across research projects.

```bash
# Create personal commands (available in all projects)
mkdir -p ~/.claude/commands

cat > ~/.claude/commands/security.md << 'EOF'
Review this code for security vulnerabilities.
Check for:
1. SQL injection
2. XSS vulnerabilities
3. CSRF issues
4. Insecure dependencies
5. Hardcoded secrets
6. Authentication bypasses
EOF
```

#### Commands with Arguments

**Single argument (`$ARGUMENTS`):**
```markdown
<!-- .claude/commands/fix-issue.md -->
Fix GitHub issue #$ARGUMENTS

Follow these steps:
1. Read the issue description
2. Understand the expected behavior
3. Find the relevant code
4. Implement the fix
5. Write tests
6. Create a commit
```

**Usage:**
```bash
> /fix-issue 123
```

**Multiple arguments (`$1`, `$2`, etc.):**
```markdown
<!-- .claude/commands/review-pr.md -->
Review PR #$1 with priority level: $2

Assignee: $3
```

**Usage:**
```bash
> /review-pr 456 high alice
```

#### Advanced Command Features

**With frontmatter:**
```markdown
---
description: Create a well-formatted git commit
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
model: claude-3-5-haiku-20241022
---

Create a git commit for the current changes.

Guidelines:
- Use conventional commit format
- Keep subject line under 50 characters
- Add body if changes are complex
```

**With dynamic context (bash execution):**
```markdown
---
description: Smart commit with context
allowed-tools: Bash(git:*)
---

## Current State
- Branch: !`git branch --show-current`
- Status: !`git status --short`
- Recent commits: !`git log --oneline -5`

## Staged Changes
!`git diff --cached`

## Task
Based on the above context, create an appropriate commit message and commit the changes.
```

**With file references:**
```markdown
Review the authentication implementation:

Key files:
- @src/auth/login.ts
- @src/auth/middleware.ts
- @src/utils/jwt.ts

Ensure consistency across all auth-related code.
```

---

## 6. Configuration Deep Dive

### 6.1 Settings File Hierarchy

```
Precedence (highest to lowest):
┌─────────────────────────────────────┐
│ 1. Enterprise managed policies      │  /Library/Application Support/ClaudeCode/
├─────────────────────────────────────┤
│ 2. Command line arguments           │  claude --permission-mode plan
├─────────────────────────────────────┤
│ 3. Local project settings           │  .claude/settings.local.json
├─────────────────────────────────────┤
│ 4. Shared project settings          │  .claude/settings.json
├─────────────────────────────────────┤
│ 5. User settings                    │  ~/.claude/settings.json
└─────────────────────────────────────┘
```

### 6.2 Complete Settings Reference

```json
{
  // Model Configuration
  "model": "claude-sonnet-4-5-20250929",
  "alwaysThinkingEnabled": false,

  // Permission Configuration
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(npm:*)",
      "WebSearch"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)"
    ],
    "ask": [
      "Bash(rm:*)"
    ],
    "additionalDirectories": ["../shared-lib/"],
    "defaultMode": "acceptEdits",
    "disableBypassPermissionsMode": "disable"
  },

  // Sandbox Configuration
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker", "kubectl"],
    "allowUnsandboxedCommands": true,
    "network": {
      "allowUnixSockets": ["~/.ssh/agent-socket"],
      "allowLocalBinding": true,
      "httpProxyPort": 8080,
      "socksProxyPort": 8081
    }
  },

  // Status Line
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  },

  // Output Style
  "outputStyle": "Explanatory",

  // Git Attribution
  "attribution": {
    "commit": "🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
    "pr": "🤖 Generated with Claude Code"
  },

  // Hooks
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "UserPromptSubmit": [...],
    "SessionStart": [...],
    "SessionEnd": [...],
    "Stop": [...]
  },

  // MCP Servers
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@org/mcp-server"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  },

  // Environment Variables
  "env": {
    "NODE_ENV": "development",
    "DEBUG": "true"
  },

  // Cleanup
  "cleanupPeriodDays": 30
}
```

### 6.3 Environment Variables

```bash
# Authentication
ANTHROPIC_API_KEY=sk-ant-...          # API key (Console users)
ANTHROPIC_AUTH_TOKEN=...              # Auth token

# Model Selection
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-3-5-haiku
ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-5
ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-5

# Extended Thinking
MAX_THINKING_TOKENS=10000             # Max tokens for thinking (default: 31999)

# Bash Execution
BASH_DEFAULT_TIMEOUT_MS=30000         # Default timeout (30 seconds)
BASH_MAX_TIMEOUT_MS=600000            # Max timeout (10 minutes)
BASH_MAX_OUTPUT_LENGTH=100000         # Max output chars before truncation
CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1  # Stay in project dir

# Networking
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1

# Feature Toggles
DISABLE_TELEMETRY=1                   # Disable telemetry
DISABLE_AUTOUPDATER=1                 # Disable auto-updates
DISABLE_ERROR_REPORTING=1             # Disable error reports
DISABLE_BUG_COMMAND=1                 # Disable /bug command
DISABLE_PROMPT_CACHING=0              # Disable prompt caching
DISABLE_COST_WARNINGS=0               # Disable cost warnings

# Development
CLAUDE_CONFIG_DIR=~/.claude           # Config directory
CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1  # Don't update terminal title
```

### 6.4 Project-Specific Configuration

**Team settings (`.claude/settings.json`):**
```json
{
  "permissions": {
    "allow": [
      "Bash(npm test:*)",
      "Bash(npm run lint:*)",
      "Bash(npm run build:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "attribution": {
    "commit": "Co-Authored-By: Claude <ai@company.com>"
  }
}
```

**Personal overrides (`.claude/settings.local.json`):**
```json
{
  "permissions": {
    "allow": [
      "Bash(docker:*)"
    ],
    "defaultMode": "acceptEdits"
  },
  "alwaysThinkingEnabled": true
}
```

---

## 7. Hooks System

Hooks let you automate actions that happen before or after Claude does something. They're like "if this, then that" rules for your development workflow.

> **💡 Tip:** Start simple. The most useful hook is `PostToolUse` to auto-format code after Claude edits it. Get that working before trying complex setups.
>
> **💡 Tip for ADHD:** Hooks reduce context-switching by automating repetitive tasks. Instead of remembering to lint after every edit, let a hook do it automatically.
>
> **📋 DT's Workflow:** Useful hooks by project type:
> - **R packages:** PostToolUse hook to run `styler::style_file()` after R file edits
> - **Quarto docs:** PostToolUse hook to re-render preview after .qmd changes
> - **Teaching:** UserPromptSubmit hook to auto-inject course context
> - **All projects:** PreToolUse hook for the `@smart` prompt optimizer

### 7.1 Hook Events

| Event | Trigger | Input Data | Use Cases |
|-------|---------|------------|-----------|
| `PreToolUse` | Before any tool runs | Tool name, input params | Validate, auto-approve, block |
| `PostToolUse` | After tool completes | Tool name, input, output | Lint, format, validate results |
| `UserPromptSubmit` | User sends message | Prompt text | Add context, validate input |
| `SessionStart` | Session begins | Session info | Load environment, setup |
| `SessionEnd` | Session ends | Session info | Cleanup, logging |
| `Stop` | Agent finishes | Completion reason | Decide if more work needed |
| `SubagentStop` | Subagent finishes | Agent output | Evaluate subagent work |
| `Notification` | Notification sent | Message content | External alerts |
| `PreCompact` | Before compaction | Context info | Pre-compact validation |

### 7.2 Hook Configuration

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",    // Optional: regex to match tools
        "hooks": [
          {
            "type": "command",       // "command" or "prompt"
            "command": "/path/to/script.sh",
            "timeout": 30            // Optional: seconds
          }
        ]
      }
    ]
  }
}
```

### 7.3 Hook Input/Output

**Input (JSON via stdin):**
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "acceptEdits",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  }
}
```

**Exit Codes:**
- `0` = Success (stdout parsed for JSON)
- `2` = Blocking error (stderr shown to Claude)
- Other = Non-blocking error (shown in verbose mode)

**JSON Output Control:**
```json
{
  "continue": true,
  "stopReason": "Optional message",
  "suppressOutput": false,
  "systemMessage": "Warning: ...",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Auto-approved"
  }
}
```

### 7.4 Practical Hook Examples

#### Auto-Approve Documentation Files
```python
#!/usr/bin/env python3
# ~/.claude/hooks/auto-approve-docs.py
import json
import sys

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Read":
    file_path = tool_input.get("file_path", "")
    if file_path.endswith((".md", ".txt", ".json", ".yaml", ".yml")):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Documentation file auto-approved"
            }
        }
        print(json.dumps(output))

sys.exit(0)
```

#### Block Sensitive Patterns
```python
#!/usr/bin/env python3
# ~/.claude/hooks/block-secrets.py
import json
import sys
import re

input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")

# Block prompts containing secrets
patterns = [
    r"(?i)\b(password|secret|key|token)\s*[:=]\s*['\"]?\w+",
    r"sk-[a-zA-Z0-9]{20,}",  # API keys
    r"-----BEGIN.*PRIVATE KEY-----"  # Private keys
]

for pattern in patterns:
    if re.search(pattern, prompt):
        output = {
            "decision": "block",
            "reason": "Security: Remove sensitive information before sending"
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)
```

#### Add Project Context
```bash
#!/bin/bash
# ~/.claude/hooks/add-context.sh

# Read input
input=$(cat)

# Add timestamp and git info
echo "Context added at $(date)"
echo "Current branch: $(git branch --show-current 2>/dev/null || echo 'not in git repo')"

exit 0
```

#### Auto-Format on File Write
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run format -- --write",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

#### Persist Environment Variables
```bash
#!/bin/bash
# SessionStart hook to persist environment

if [ -n "$CLAUDE_ENV_FILE" ]; then
    # Activate conda environment
    echo 'eval "$(conda shell.bash hook)"' >> "$CLAUDE_ENV_FILE"
    echo 'conda activate myenv' >> "$CLAUDE_ENV_FILE"

    # Set project-specific vars
    echo 'export DATABASE_URL=postgresql://localhost/mydb' >> "$CLAUDE_ENV_FILE"
    echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

---

## 8. MCP (Model Context Protocol)

### 8.1 What is MCP?

MCP (Model Context Protocol) is an open standard for connecting AI assistants to external tools and data sources. Think of it as "plugins" for Claude Code - ways to give Claude access to things it can't normally reach.

> **💡 Tip:** You don't need MCP to use Claude Code effectively. Start without it. Add MCP servers later when you have a specific need (like querying a database or accessing a specific API).
>
> **📋 DT's Workflow:** The `statistical-research` MCP server provides R execution, literature search, and Zotero integration - perfect for research projects. The `shell-mcp-server` enables shell commands in claude.ai browser tabs. The `filesystem` MCP gives Claude access to read/write files when using the browser extension.

MCP allows Claude Code to:

- Query databases directly
- Access issue trackers (Jira, GitHub)
- Read monitoring data (Sentry, Datadog)
- Integrate with design tools (Figma)
- Connect to any API with an MCP server

### 8.2 Adding MCP Servers

#### HTTP Servers (Remote)
```bash
# Basic
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# With authentication
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp \
  --header "Authorization: Bearer $SENTRY_TOKEN"

# With OAuth (authenticate in browser)
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

#### Stdio Servers (Local)
```bash
# NPM package
claude mcp add --transport stdio filesystem \
  -- npx -y @modelcontextprotocol/server-filesystem /Users/me

# With environment variables
claude mcp add --transport stdio postgres \
  --env DATABASE_URL=postgresql://user:pass@localhost/db \
  -- npx -y @modelcontextprotocol/server-postgres

# Custom server
claude mcp add --transport stdio my-server \
  -- /path/to/server --config /path/to/config.json
```

### 8.3 Server Scopes

| Scope | Storage | Shared | Use Case |
|-------|---------|--------|----------|
| `local` (default) | `~/.claude.json` | No | Personal, sensitive keys |
| `project` | `.mcp.json` | Yes (git) | Team tools |
| `user` | `~/.claude.json` | No | All your projects |

```bash
# Local (default)
claude mcp add --transport http stripe https://mcp.stripe.com

# Project (shared with team)
claude mcp add --transport http paypal --scope project https://mcp.paypal.com

# User (all your projects)
claude mcp add --transport http hubspot --scope user https://mcp.hubspot.com
```

### 8.4 Managing Servers

```bash
# List all servers
claude mcp list

# Get server details
claude mcp get github

# Remove server
claude mcp remove github

# Reset project approvals
claude mcp reset-project-choices

# In-session management
> /mcp
```

### 8.5 Using MCP in Conversations

**Natural language:**
```bash
> What are the most common errors in Sentry this week?
> Create a GitHub issue for the bug we found
> Query the database for users who signed up this month
> Update the Jira ticket with our progress
```

**Reference resources:**
```bash
> Can you analyze @github:issue://123 and suggest a fix?
> Compare @postgres:schema://users with the User model
```

**MCP prompts as slash commands:**
```bash
> /mcp__github__list_prs
> /mcp__jira__create_issue "Bug title" high
```

### 8.6 Settings-Based Configuration

```json
{
  "mcpServers": {
    "statistical-research": {
      "command": "bun",
      "args": ["run", "/path/to/mcp-server/src/index.ts"],
      "env": {
        "R_LIBS_USER": "~/R/library"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### 8.7 Popular MCP Servers

| Server | Description | Install |
|--------|-------------|---------|
| `@modelcontextprotocol/server-filesystem` | File system access | `npx -y @modelcontextprotocol/server-filesystem` |
| `@modelcontextprotocol/server-postgres` | PostgreSQL queries | `npx -y @modelcontextprotocol/server-postgres` |
| `@modelcontextprotocol/server-github` | GitHub API | `npx -y @modelcontextprotocol/server-github` |
| `@modelcontextprotocol/server-sqlite` | SQLite database | `npx -y @modelcontextprotocol/server-sqlite` |
| `@modelcontextprotocol/server-memory` | Knowledge graph | `npx -y @modelcontextprotocol/server-memory` |

---

## 9. Plugins & Marketplaces

### 9.1 What Are Plugins?

**In Plain English:** Plugins are like apps for your phone - they add new features to Claude Code. Instead of configuring everything yourself, you can install pre-made plugins that other developers have created and shared.

A plugin can bundle together:
- **Slash commands** - Custom shortcuts like `/deploy` or `/review-pr`
- **Subagents** - Specialized AI assistants for specific tasks
- **MCP servers** - Connections to external tools and databases
- **Hooks** - Automated actions that run at specific times

**Why use plugins?**
- **Save time:** Don't reinvent the wheel - use what others have built
- **Learn patterns:** See how experts configure their Claude Code setup
- **Team consistency:** Everyone uses the same tools and workflows
- **Easy updates:** Plugins can auto-update when authors improve them

> **💡 Tip:** Plugins are currently in public beta. They work in both terminal and VS Code environments.

---

### 9.2 Finding and Installing Plugins

#### **Browse Available Plugins**

The simplest way to discover plugins:

```bash
# Open the interactive plugin menu
> /plugin
```

This shows you:
- Installed plugins (with on/off toggles)
- Available plugins from your marketplaces
- Options to add new marketplaces

#### **Add a Plugin Marketplace**

Marketplaces are collections of plugins. Think of them like app stores:

```bash
# Add the official Anthropic marketplace
> /plugin marketplace add anthropics/claude-code

# Add a community marketplace
> /plugin marketplace add jeremylongshore/claude-code-plugins-plus

# Add your company's internal marketplace
> /plugin marketplace add your-org/internal-plugins
```

#### **Install a Plugin**

```bash
# From the interactive menu (easiest)
> /plugin
# Then browse and select what you want

# Or install directly by name
> /plugin install plugin-name@marketplace-name
```

#### **Manage Marketplaces**

```bash
# See all your marketplaces
> /plugin marketplace list

# Update a marketplace to get new plugins
> /plugin marketplace update marketplace-name

# Remove a marketplace you no longer need
> /plugin marketplace remove marketplace-name
```

---

### 9.3 Popular Plugin Marketplaces

| Marketplace | What's In It | How to Add |
|-------------|--------------|------------|
| **Official Anthropic** | Curated, high-quality plugins from Anthropic | `/plugin marketplace add anthropics/claude-code` |
| **Claude Code Plugins Plus** | 243 community plugins, ADHD-friendly agents | `/plugin marketplace add jeremylongshore/claude-code-plugins-plus` |

> **📋 DT's Workflow:** Start with the official Anthropic marketplace. It has vetted plugins for common tasks like PR reviews and security checks. Add community marketplaces later when you need specialized tools.

---

### 9.4 Using Installed Plugins

Once installed, plugins add features you can use immediately:

**Slash commands from plugins:**
```bash
# If you installed a code-review plugin
> /review-pr 123

# If you installed a deployment plugin
> /deploy staging
```

**Subagents from plugins:**
```bash
# If you installed a security-audit plugin
> @security-auditor check this authentication code
```

**Toggle plugins on/off:**
```bash
> /plugin
# Select the plugin
# Choose "Enable" or "Disable"
```

> **💡 Tip:** Disable plugins you're not using. Each enabled plugin adds to Claude's system prompt, which can slow things down.

---

### 9.5 Plugin Examples

#### **PR Review Plugin**
```bash
# After installing from Anthropic marketplace
> /review-pr 456

# Claude examines the PR and provides:
# - Code quality feedback
# - Security concerns
# - Suggestions for improvement
```

#### **Security Guidance Plugin**
```bash
# Ask the security subagent
> @security-advisor is this SQL query safe?

# Get expert-level security analysis
```

#### **Documentation Generator Plugin**
```bash
# Generate docs for your code
> /generate-docs src/utils/

# Creates markdown documentation automatically
```

---

### 9.6 Creating Your Own Plugins

If you want to share your custom commands, hooks, or agents with others, you can create a plugin.

**Basic plugin structure:**
```
my-plugin/
├── .claude-plugin/
│   └── manifest.json      # Plugin metadata
├── commands/
│   └── my-command.md      # Slash commands
├── agents/
│   └── my-agent.md        # Subagents
└── hooks/
    └── my-hook.sh         # Hook scripts
```

**Simple manifest.json:**
```json
{
  "name": "my-awesome-plugin",
  "version": "1.0.0",
  "description": "Does awesome things",
  "author": {
    "name": "Your Name"
  },
  "commands": ["commands/my-command.md"],
  "agents": ["agents/my-agent.md"]
}
```

**Validate your plugin:**
```bash
claude plugin validate .
```

> **📋 DT's Workflow:** Create plugins for workflows you repeat across projects:
> - **R package plugin:** Commands for `R CMD check`, documentation, CRAN submission
> - **Teaching plugin:** Commands for grading, publishing to GitHub Pages
> - **Research plugin:** Agents for literature review, statistical consulting

---

### 9.7 Hosting Your Own Marketplace

Share plugins with your team or the community by creating a marketplace:

**1. Create the marketplace file** (`.claude-plugin/marketplace.json`):
```json
{
  "name": "my-team-tools",
  "owner": {
    "name": "My Team",
    "email": "[email protected]"
  },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Auto-format code on save",
      "version": "1.0.0"
    },
    {
      "name": "deploy-helper",
      "source": {
        "source": "github",
        "repo": "my-org/deploy-plugin"
      },
      "description": "Simplified deployment commands"
    }
  ]
}
```

**2. Host it** (any of these work):
- GitHub repository (most common)
- GitLab repository
- Any URL serving the JSON file

**3. Share with others:**
```bash
# They run this to add your marketplace
> /plugin marketplace add your-username/your-repo
```

---

### 9.8 Auto-Updates

Plugins can update automatically so you always have the latest version.

| Marketplace Type | Auto-Update Default |
|------------------|---------------------|
| Official Anthropic | ✅ Enabled |
| Third-party community | ❌ Disabled |
| Local development | ❌ Disabled |

**Configure auto-update per marketplace:**
```bash
> /plugin
# Select "Marketplaces"
# Choose your marketplace
# Toggle "Enable/Disable auto-update"
```

**Disable all auto-updates:**
```bash
export DISABLE_AUTOUPDATER=true
```

---

### 9.9 Enterprise/Team Settings

For organizations that need to control which plugins are allowed:

**Allow only approved marketplaces** (in managed settings):
```json
{
  "strictKnownMarketplaces": [
    {
      "source": "github",
      "repo": "company/approved-plugins"
    }
  ]
}
```

**Managed settings locations:**
- **macOS:** `/Library/Application Support/ClaudeCode/managed-settings.json`
- **Linux:** `/etc/claude-code/managed-settings.json`
- **Windows:** `C:\ProgramData\ClaudeCode\managed-settings.json`

---

### 9.10 Troubleshooting Plugins

| Problem | Solution |
|---------|----------|
| Marketplace won't load | Check URL is accessible, verify `.claude-plugin/marketplace.json` exists |
| Plugin won't install | Verify plugin source URLs are correct, check for typos |
| Plugin not working | Make sure it's enabled: `/plugin` → select plugin → "Enable" |
| Commands not showing | Restart Claude Code after installing plugins |
| Validation errors | Run `claude plugin validate .` to see detailed errors |

**Validate a plugin or marketplace:**
```bash
claude plugin validate .
claude plugin validate ./path/to/plugin
```

---

## 10. Advanced Workflows

### 10.1 Extended Thinking Mode

Claude can use up to 31,999 tokens for internal reasoning before responding. This is useful for complex architectural decisions, tricky bugs, or anything that needs deeper analysis.

> **💡 Tip:** Use `think:` prefix for one-off deep thinking. Don't enable "always thinking" mode unless you're consistently solving complex problems - it slows responses and uses more tokens.
>
> **💡 Tip for ADHD:** Extended thinking can help when you're stuck in analysis paralysis. Ask Claude to "think through" the options, then present a single recommendation. Let Claude do the overthinking for you.
>
> **📋 DT's Workflow:** Use extended thinking for:
> - **Research:** "think: what's the right statistical approach for this mediation analysis?"
> - **R packages:** "think: design the API for this new function - what parameters make sense?"
> - **Teaching:** "think: what order should I present these concepts for STAT 440 students?"
> - **Architecture:** "think: how should I structure this MCP server for extensibility?"

**Enable per-request:**
```bash
> think: design a caching architecture for our API
> ultrathink: analyze the security implications of this change
```

**Enable globally:**
```bash
> /config
# Toggle "Always use thinking mode"
```

**Or in settings:**
```json
{
  "alwaysThinkingEnabled": true
}
```

**View thinking process:**
Press `Ctrl+O` to toggle verbose mode

**Set custom budget:**
```bash
export MAX_THINKING_TOKENS=10000
claude
```

### 10.2 Subagents

Subagents are specialized AI assistants for specific tasks.

**Create a subagent (`.claude/agents/code-reviewer.md`):**
```markdown
---
description: Expert code reviewer for security and quality
tools: ["Read", "Grep", "Glob", "Bash"]
model: sonnet
---

You are a senior code reviewer with expertise in:
- Security vulnerabilities (OWASP Top 10)
- Performance optimization
- Code quality and maintainability
- Best practices for the project's tech stack

When reviewing code:
1. First understand the context and purpose
2. Check for security issues
3. Evaluate performance implications
4. Suggest improvements with examples
5. Be constructive and educational

Always explain WHY something is an issue, not just WHAT.
```

**Use subagent:**
```bash
> /agents                           # List available agents
> use the code-reviewer agent to review auth module
```

**CLI flag:**
```bash
claude --agent code-reviewer "review the authentication changes"
```

### 10.3 Parallel Sessions with Git Worktrees

Work on multiple features simultaneously:

```bash
# Create worktrees for different features
git worktree add ../project-feature-auth -b feature/auth
git worktree add ../project-feature-api -b feature/api

# Run Claude in each (separate terminals)
cd ../project-feature-auth
claude

cd ../project-feature-api  # Different terminal
claude

# Clean up when done
git worktree remove ../project-feature-auth
git worktree remove ../project-feature-api
```

### 10.4 Unix Pipeline Integration

**Pipe data to Claude:**
```bash
# Analyze logs
cat error.log | claude -p "summarize the errors and suggest fixes"

# Process build output
npm run build 2>&1 | claude -p "explain any errors"

# Git diff analysis
git diff main | claude -p "review these changes for issues"
```

**Pipe output from Claude:**
```bash
# Save analysis
claude -p "analyze @src/api/routes.ts" > analysis.md

# Chain with other tools
claude -p "list files that need refactoring" | xargs -I {} echo "TODO: {}"
```

**Output formats:**
```bash
# Default text
claude -p "analyze this" --output-format text

# JSON (structured)
claude -p "list dependencies" --output-format json

# Streaming JSON (for real-time processing)
claude -p "long analysis" --output-format stream-json
```

### 10.5 Build Script Integration

**package.json:**
```json
{
  "scripts": {
    "ai:review": "claude -p 'review changes vs main branch'",
    "ai:test": "claude -p 'analyze test coverage and suggest missing tests'",
    "ai:docs": "claude -p 'generate documentation for public APIs'",
    "ai:security": "claude -p 'security audit of recent changes'"
  }
}
```

**Makefile:**
```makefile
.PHONY: ai-review ai-explain

ai-review:
	@git diff main | claude -p "review these changes"

ai-explain:
	@claude -p "explain the architecture of this project"
```

### 10.6 Non-Interactive Mode

```bash
# Single query, exit after response
claude -p "what does the main function do?"

# With specific tools
claude -p "list all TODO comments" --tools "Grep,Glob"

# With JSON output
claude -p "analyze dependencies" --output-format json

# Continue without interaction
claude -p "fix the linting errors" --max-turns 5

# With fallback model (for rate limits)
claude -p "complex analysis" --fallback-model haiku
```

---

## 11. Real-World Examples

### 11.1 Feature Development Workflow

```bash
# Start session
claude

# Understand requirements
> I need to add user profile settings. Users should be able to update
> their name, email, and avatar. Show me similar features in the codebase.

# Plan implementation
> Create a plan for implementing this feature. Consider the existing
> patterns in this codebase.

# Implement step by step
> Let's start with the database schema changes

> Now create the API endpoints

> Add the frontend form component

> Write tests for the new functionality

# Review and commit
> Review all the changes we made for any issues

> Create a commit with a descriptive message
```

### 11.2 Bug Investigation

```bash
claude

# Describe the bug
> Users report that the checkout process fails intermittently with
> error code E_PAYMENT_TIMEOUT. Help me investigate.

# Follow the trail
> Search for where E_PAYMENT_TIMEOUT is thrown

> Show me the payment processing logic

> What external services does this code call?

# Find root cause
> Analyze the timeout configuration. Is 5 seconds enough for the
> payment gateway?

# Implement fix
> Implement a retry mechanism with exponential backoff

> Add better error logging so we can debug future issues

> Write a test that simulates the timeout scenario
```

### 11.3 Code Review Session

```bash
claude --permission-mode plan

# Get overview
> Summarize the changes in this PR compared to main

> What are the potential issues with these changes?

# Deep dive
> Analyze the security implications of the auth changes

> Check if the database queries are optimized

> Are there any edge cases not covered by tests?

# Generate feedback
> Write detailed code review comments for each issue found
```

### 11.4 Documentation Generation

```bash
claude

# Generate API docs
> Generate OpenAPI documentation for all endpoints in src/api/

> Create a getting-started guide for new developers

> Document the deployment process based on the scripts in deploy/

# Review existing docs
> Are our README instructions still accurate? Test them.

> What's missing from our documentation?
```

### 11.5 Refactoring Legacy Code

```bash
claude

# Understand current state
> Analyze the authentication module. It was written 3 years ago and
> needs modernization.

> What patterns does it use? What would modern equivalents be?

# Plan refactoring
> Create a refactoring plan that:
> 1. Doesn't break existing functionality
> 2. Can be done incrementally
> 3. Adds proper TypeScript types
> 4. Improves testability

# Execute carefully
> Let's start with step 1. Make sure all existing tests still pass.

> Run the tests after each change
```

### 11.6 Learning a New Codebase

```bash
claude --permission-mode plan

# High-level understanding
> Give me a tour of this codebase. What does it do? How is it organized?

> Draw an architecture diagram in ASCII art

> What are the main entry points?

# Dive deeper
> How does data flow from the API to the database?

> Explain the state management approach

> What design patterns are used?

# Find specific things
> Where would I add a new API endpoint?

> How do I add a new database migration?

> Where are environment variables configured?
```

---

## 12. Troubleshooting

> **💡 Tip:** When something doesn't work, run `/doctor` first. It checks for common issues automatically. If that doesn't help, check your settings with `/permissions` and `/status`.
>
> **💡 Tip for ADHD:** Don't rabbit-hole on debugging. If you've spent more than 10 minutes on a Claude Code issue, try: 1) Restart Claude Code, 2) Check GitHub Issues, 3) Ask in Discord. Fresh eyes often solve it faster.
>
> **📋 DT's Workflow:** Common issues by project type:
> - **R packages:** R not found → check `PATH` includes R, or use full path `/usr/local/bin/Rscript`
> - **Quarto:** Preview not updating → check `quarto preview` is running in background
> - **MCP servers:** Connection failed → run `claude mcp list` to verify server status
> - **Git operations:** Permission denied → check SSH keys with `ssh -T git@github.com`

### 12.1 Common Issues

#### "Permission denied" for tools
```bash
# Check current permissions
> /permissions

# Add to allow list
# In ~/.claude/settings.json:
{
  "permissions": {
    "allow": ["Bash(your-command:*)"]
  }
}
```

#### Bash command doesn't work
```bash
# Check if sandboxed
> /status

# Exclude from sandbox
{
  "sandbox": {
    "excludedCommands": ["problematic-command"]
  }
}
```

#### Output hidden (delegate mode issue)
```bash
# Check settings
cat ~/.claude/settings.json | grep defaultMode

# Fix: Change from "delegate" to "acceptEdits"
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

#### MCP server not connecting
```bash
# Check server status
> /mcp

# Debug mode
claude --debug mcp

# Check server logs
claude mcp get server-name
```

#### Context too large
```bash
# Compact conversation
> /compact focus on current feature

# Check context usage
> /context

# Start fresh
> /clear
```

### 12.2 Health Check

```bash
claude
> /doctor
```

This checks:
- Authentication status
- Network connectivity
- Permission configuration
- MCP server health
- Terminal compatibility

### 12.3 Debug Mode

```bash
# Enable all debug output
claude --debug

# Debug specific categories
claude --debug api,mcp,hooks

# Exclude noisy categories
claude --debug "!statsig,!file"

# Verbose mode (show tool output)
# Press Ctrl+O during session
```

### 12.4 Log Locations

```bash
# Session transcripts
~/.claude/projects/*/

# General logs
~/.claude/logs/

# MCP server logs
# Visible in debug mode
```

### 12.5 Reset to Defaults

```bash
# Remove all settings
rm -rf ~/.claude/settings.json
rm -rf ~/.claude.json

# Remove project settings
rm -rf .claude/

# Restart
claude
> /login
```

---

## 13. macOS-Specific Tips

### 13.1 Terminal Setup

Claude Code works in any terminal, but some terminals offer better features than others. Here's a complete setup guide for each option.

---

#### **iTerm2 (Highly Recommended)**

iTerm2 is the best terminal for Claude Code on macOS. It supports all features including multi-line input, custom profiles, and status bars.

**Step 1: Install iTerm2**
```bash
# Using Homebrew (easiest)
brew install --cask iterm2

# Or download directly from: https://iterm2.com/downloads.html
```

**Step 2: Set up Shift+Enter for multi-line input**
```bash
# Automatic setup (run this inside Claude Code)
claude
> /terminal-setup

# You should see: "✓ iTerm2 key binding installed"
```

**Step 3: Verify it works**
```bash
# Try typing a multi-line message
> This is line one        # Press Shift+Enter
  This is line two        # Press Shift+Enter
  This is line three      # Press Enter to send all three lines
```

**If automatic setup fails, configure manually:**
1. Open **iTerm2** → **Settings** (Cmd+,)
2. Go to **Profiles** → **Keys** → **Key Mappings**
3. Click the **+** button to add a new mapping
4. Press **Shift+Enter** to record the shortcut
5. For "Action", select **Send Text with "vim" Special Chars**
6. In the text field, type: `\n` (backslash followed by letter n)
7. Click **OK** to save

**Optional: Enable Claude Code status bar in iTerm2**
1. Go to **Profiles** → **Session**
2. Check **Status bar enabled**
3. Click **Configure Status Bar**
4. Drag "User Variables" or "Custom Script" to your status bar
5. Configure it to show Claude Code session info

---

#### **VS Code Integrated Terminal**

VS Code's built-in terminal works well with Claude Code and integrates nicely with your editor.

**Step 1: Open terminal in VS Code**
- Press `` Ctrl+` `` (backtick) to toggle the terminal panel
- Or go to **View** → **Terminal**

**Step 2: Run terminal setup**
```bash
claude
> /terminal-setup
```

**Step 3: If manual setup needed**
1. Press `Cmd+Shift+P` to open Command Palette
2. Type "Preferences: Open Keyboard Shortcuts (JSON)"
3. Add this to the file:
```json
{
  "key": "shift+enter",
  "command": "workbench.action.terminal.sendSequence",
  "args": { "text": "\n" },
  "when": "terminalFocus"
}
```

**Tip:** VS Code also has a Claude Code extension that provides additional integration.

---

#### **Terminal.app (macOS Default)**

The built-in macOS Terminal works but has limitations.

**What works:**
- Basic Claude Code functionality
- All commands and slash commands
- File editing and bash execution

**What doesn't work:**
- Shift+Enter for multi-line input (Terminal.app doesn't support custom key bindings)
- Some advanced status bar features

**Workarounds for multi-line input:**
```bash
# Option 1: Use heredoc syntax
claude -p "$(cat <<'EOF'
Fix this function:
function broken() {
  return null
}
EOF
)"

# Option 2: Pipe from a file
echo "Fix the bug in auth.js" | claude

# Option 3: Type in TextEdit, copy, then paste into Terminal
# (Claude Code will receive the pasted text with newlines intact)
```

**Recommendation:** If you use Claude Code frequently, switch to iTerm2 for the full experience.

---

#### **Warp Terminal**

Warp is a modern terminal with AI features. Claude Code works with some caveats.

**Setup:**
```bash
claude
> /terminal-setup
```

**Notes:**
- Warp has its own AI features that may conflict with Claude Code
- Some keyboard shortcuts may be intercepted by Warp
- Generally works well for basic usage

---

#### **Alacritty, Kitty, and Other Terminals**

Most modern terminals work with Claude Code. Run `/terminal-setup` and follow the prompts. If automatic setup fails:

1. Check your terminal's documentation for custom key binding setup
2. Map Shift+Enter to send a literal newline character (`\n` or `0x0a`)
3. Test by typing multiple lines before pressing Enter

---

#### **Terminal Setup Troubleshooting**

| Problem | Solution |
|---------|----------|
| `/terminal-setup` says "unsupported terminal" | Use manual setup steps above |
| Shift+Enter still sends message | Restart your terminal after setup |
| Shift+Enter does nothing | Check terminal preferences for conflicting shortcuts |
| Works in iTerm2 but not VS Code | Run `/terminal-setup` again inside VS Code |
| Lost my key bindings after update | Re-run `/terminal-setup` |

### 13.2 Accessibility Permissions

For hooks and AppleScript to work properly:

1. Open **System Settings**
2. Go to **Privacy & Security** → **Accessibility**
3. Enable **iTerm** (or your terminal app)
4. Also check **Automation** permissions if needed

### 13.3 Opening Files from Claude Code

**Problem:** The `open` command doesn't work reliably from Claude Code's bash environment.

**Solution:** Use AppleScript instead:

```bash
# Markdown files (iA Writer)
osascript -e 'tell application "iA Writer"
    activate
    open POSIX file "/path/to/file.md"
end tell'

# Any file with default app
osascript -e 'tell application "Finder" to open POSIX file "/path/to/file"'

# VS Code
osascript -e 'tell application "Visual Studio Code"
    activate
    open POSIX file "/path/to/file"
end tell'

# TextEdit
osascript -e 'tell application "TextEdit" to open POSIX file "/path/to/file.txt"'
```

**Why this happens:**
- Claude Code runs in a detached process
- `XPC_SERVICE_NAME=0` breaks Launch Services
- AppleScript uses Apple Events which bypass this

### 13.4 Homebrew Integration

```bash
# Update Claude Code via Homebrew
brew upgrade claude-code

# Install helper tools
brew install gh        # GitHub CLI
brew install jq        # JSON processing
brew install ripgrep   # Fast search (used by Grep tool)
```

### 13.5 Sandboxing on macOS

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": [
      "docker",
      "brew"
    ],
    "network": {
      "allowLocalBinding": true
    }
  }
}
```

---

## 14. Quick Reference

### 14.1 CLI Commands Explained (Plain English)

#### Starting Claude Code

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `claude` | **Opens Claude Code.** Like opening an app - starts a conversation where you can ask Claude to help with your code. |
| `claude "fix the login bug"` | **Opens Claude Code with a task already given.** Instead of opening and then typing, you give Claude the task right away. |
| `claude -p "what does this do?"` | **Ask a quick question and get an answer.** Claude answers your question and then closes automatically. Good for quick lookups. |
| `claude -c` | **Continue where you left off.** Opens your most recent conversation so you can keep working on the same thing. |
| `claude -r "my-project"` | **Go back to a specific conversation.** If you named a conversation "my-project", this opens it again. |

#### Choosing Which AI Model to Use

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `claude --model opus` | **Use the smartest (but slowest) AI.** Best for complex problems that need deep thinking. |
| `claude --model sonnet` | **Use the balanced AI (default).** Good mix of smart and fast - recommended for most work. |
| `claude --model haiku` | **Use the fastest (but simpler) AI.** Best for quick, simple tasks where speed matters more than depth. |

#### Safety Modes (How Careful Claude Should Be)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `claude --permission-mode default` | **Claude asks permission for everything.** Safest option - Claude checks with you before doing anything. |
| `claude --permission-mode acceptEdits` | **Claude can edit files without asking.** You trust Claude to make changes. It still asks for unusual things. |
| `claude --permission-mode plan` | **Claude can only look, not touch.** Read-only mode - Claude can explore your code but can't change anything. |
| `claude --permission-mode bypassPermissions` | **Claude can do anything without asking.** ⚠️ Dangerous! Only use in test environments. |

#### Output Options

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `claude -p "analyze" --output-format json` | **Get the answer as structured data.** Instead of regular text, you get data that other programs can read. |
| `claude --verbose` | **Show everything Claude is doing.** See all the behind-the-scenes work, useful for understanding what's happening. |
| `claude --debug` | **Show technical details.** For troubleshooting when something isn't working right. |

#### Controlling How Claude Works

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `claude --max-turns 5` | **Limit how many steps Claude takes.** Prevents Claude from going on forever - stops after 5 back-and-forth exchanges. |
| `claude --fallback-model haiku` | **Use a backup AI if the main one is busy.** If Sonnet is overloaded, automatically switch to Haiku instead of waiting. |
| `claude --append-system-prompt "Be concise"` | **Give Claude extra instructions.** Add custom rules like "always be brief" or "focus on security". |

#### Managing External Connections (MCP)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `claude mcp list` | **See all connected tools.** Shows what external services (like GitHub, databases) Claude can access. |
| `claude mcp add ...` | **Connect a new tool.** Add a new external service for Claude to use. |
| `claude mcp remove github` | **Disconnect a tool.** Remove access to a specific service. |

---

### 14.2 Slash Commands Explained (Plain English)

**Slash commands** start with `/` and are typed inside Claude Code. They're like menu options.

#### Essential Commands (Use These Often)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `/help` | **Get help.** Shows all available commands and how to use Claude Code. |
| `/config` | **Open settings.** Change how Claude Code works - permissions, model, appearance. |
| `/status` | **Check current state.** See what model you're using, what mode you're in, connection status. |
| `/doctor` | **Run a health check.** Diagnoses problems - checks if everything is working correctly. |
| `/clear` | **Start fresh.** Erases the current conversation. Claude forgets everything you discussed. |
| `/exit` | **Close Claude Code.** Ends your session and returns to the regular terminal. |

#### Session Commands (Managing Your Conversations)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `/resume` | **Open past conversations.** Shows a list of previous sessions you can go back to. |
| `/rename my-feature` | **Name this conversation.** Give your current session a memorable name so you can find it later. |
| `/export notes.md` | **Save conversation to a file.** Creates a text file with everything you and Claude discussed. |

#### Tool Commands (Changing How Claude Works)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `/model opus` | **Switch to a different AI.** Change which AI model Claude uses mid-conversation. |
| `/mcp` | **Manage external connections.** See and control what external tools Claude can access. |
| `/permissions` | **See what Claude is allowed to do.** Shows which commands and files Claude can access. |

#### Project Commands (Setting Up Your Project)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `/init` | **Set up Claude for this project.** Creates a CLAUDE.md file where you can write instructions for Claude. |
| `/memory` | **Edit project instructions.** Open and modify the CLAUDE.md file that tells Claude about your project. |
| `/add-dir ../other-folder` | **Let Claude see another folder.** Give Claude access to files outside the current project. |

#### Information Commands (Learning About Your Usage)

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `/cost` | **See how much you've used.** Shows how many "tokens" (units of text) you've consumed. |
| `/context` | **Visualize Claude's memory.** Shows how much of Claude's memory is being used by your conversation. |
| `/stats` | **View usage statistics.** See your usage patterns over time - how much, when, which models. |

#### Special Mode Commands

| What You Type | What It Does (Plain English) |
|---------------|------------------------------|
| `/review` | **Start a code review.** Puts Claude in code review mode to analyze your changes. |
| `/vim` | **Enable vim-style editing.** For users who prefer vim keyboard shortcuts. |
| `/compact` | **Shrink the conversation.** Summarizes the conversation to free up Claude's memory. |

---

### 14.3 Keyboard Shortcuts Explained (Plain English)

These are keys you can press while using Claude Code for quick actions.

| Keys | What It Does (Plain English) |
|------|------------------------------|
| `?` | **Show all shortcuts.** Displays a help screen with every keyboard shortcut available. |
| `Tab` | **Auto-complete.** Start typing a file name or command, press Tab, and Claude finishes it for you. |
| `↑` (Up Arrow) | **Previous command.** Cycle through commands you've typed before, like pressing "up" in a phone's text history. |
| `↓` (Down Arrow) | **Next command.** If you went too far back with Up, go forward again. |
| `/` | **Start a slash command.** Begin typing a command like /help or /config. |
| `@` | **Reference a file.** Type @ then a filename to tell Claude to look at that specific file. |
| `Shift+Tab` | **Change safety mode.** Quickly toggle between different permission modes. |
| `Ctrl+O` | **Show/hide details.** Toggle verbose mode to see or hide what Claude is doing behind the scenes. |
| `Ctrl+C` | **Stop/Cancel.** Interrupt whatever Claude is currently doing. |
| `Ctrl+D` | **Exit.** Close Claude Code and return to your normal terminal. |
| `Shift+Enter` | **New line.** Type multiple lines before sending. **Setup required:** Run `/terminal-setup` inside Claude Code first, or manually configure your terminal (see Section 13.1 for iTerm2, VS Code, and Terminal.app instructions). Without setup, Shift+Enter won't work. |

---

### 14.4 Common Patterns Explained (Plain English)

#### "I want to..."

| I Want To... | What To Type |
|--------------|--------------|
| Start using Claude Code | `claude` |
| Ask a quick question | `claude -p "your question here"` |
| Continue yesterday's work | `claude -c` |
| Look at code without changing it | `claude --permission-mode plan` |
| Let Claude work faster without asking | `claude --permission-mode acceptEdits` |
| See what Claude is thinking | Press `Ctrl+O` during a session |
| Stop Claude mid-task | Press `Ctrl+C` |
| Start over fresh | Type `/clear` |
| Save our conversation | Type `/export myfile.md` |
| Check if everything's working | Type `/doctor` |

---

### 14.5 Settings File Explained (Plain English)

The settings file (`~/.claude/settings.json`) controls how Claude Code behaves. Here's what each part means:

```json
{
  "permissions": {
    "allow": ["Bash(safe-command:*)"],   // Commands Claude can run without asking
    "deny": ["Read(.env)"],              // Files Claude can NEVER read
    "defaultMode": "acceptEdits"         // How careful Claude should be
  },
  "model": "claude-sonnet-4-5-20250929", // Which AI brain to use
  "alwaysThinkingEnabled": false,        // Should Claude think extra hard?
  "statusLine": {                        // Customize the status bar
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

**What each setting means:**

| Setting | Plain English |
|---------|---------------|
| `permissions.allow` | **Trusted commands.** Commands in this list run automatically without asking you first. |
| `permissions.deny` | **Forbidden files.** Claude will never read these files, even if you ask. Good for secrets. |
| `permissions.defaultMode` | **Safety level.** How cautious Claude should be (see Permission Modes above). |
| `model` | **AI brain.** Which version of Claude to use (opus=smartest, sonnet=balanced, haiku=fastest). |
| `alwaysThinkingEnabled` | **Deep thinking.** When true, Claude thinks longer before answering. Better answers but slower. |
| `statusLine` | **Status bar.** Customize what information appears at the bottom of Claude Code. |

---

### 14.6 File Locations Explained (Plain English)

Claude Code stores files in specific places. Here's where everything lives and what it's for:

#### Your Personal Settings (Apply to Everything You Do)

```
~/.claude/                     ← Your home folder's .claude directory
├── settings.json              ← Your personal settings (trusted commands, preferences)
├── commands/                  ← Your custom slash commands (available everywhere)
├── agents/                    ← Your custom AI assistants (specialized helpers)
├── hooks/                     ← Automation scripts (run automatically on events)
├── rules/                     ← Custom rules for Claude's behavior
└── plans/                     ← Saved plans from planning sessions

~/.claude.json                 ← App preferences and connected external tools
```

**Plain English:**
- **settings.json** = Your preferences that apply to every project
- **commands/** = Custom shortcuts you create (like `/my-command`)
- **agents/** = Specialized AI helpers you define (like a "code reviewer" agent)
- **hooks/** = Scripts that run automatically (like "format code after every edit")

#### Project-Specific Settings (Apply Only to This Project)

```
.claude/                       ← In your project folder
├── settings.json              ← Team settings (shared with everyone via git)
├── settings.local.json        ← Your personal overrides (not shared, git-ignored)
├── commands/                  ← Project-specific shortcuts
├── agents/                    ← Project-specific AI helpers
└── CLAUDE.md                  ← Instructions for Claude about this project
```

**Plain English:**
- **settings.json** = Settings your whole team uses (safe to commit to git)
- **settings.local.json** = Your personal tweaks that only you use (don't commit this)
- **CLAUDE.md** = A "readme" specifically for Claude - tell it about your project's conventions

#### How Settings Combine (Priority Order)

```
1. Enterprise policies        ← Company rules (highest priority, can't override)
2. Command line flags         ← What you type when starting Claude
3. .claude/settings.local.json ← Your personal project settings
4. .claude/settings.json      ← Team project settings
5. ~/.claude/settings.json    ← Your personal global settings (lowest priority)
```

**In plain English:** If the same setting appears in multiple places, the one higher in this list wins. Your company's rules override everything, your project settings override your personal settings, and so on.

---

## 15. Glossary (Plain English Definitions)

If you're new to programming or Claude Code, here are simple explanations of terms used in this tutorial:

### General Terms

| Term | Plain English Definition |
|------|--------------------------|
| **CLI** | "Command Line Interface" - a text-based way to interact with software by typing commands instead of clicking buttons. |
| **Terminal** | The app where you type commands. On Mac, it's called "Terminal" or "iTerm2". |
| **Repository (Repo)** | A folder that contains your project's code, usually tracked by Git. |
| **Git** | Software that tracks changes to your code over time, like "Track Changes" in Word but for code. |
| **Commit** | A saved snapshot of your code at a specific point in time. Like a save point in a video game. |
| **Branch** | A separate version of your code where you can make changes without affecting the main version. |
| **Pull Request (PR)** | A request to merge your changes into the main codebase. Others can review before accepting. |

### Claude Code Terms

| Term | Plain English Definition |
|------|--------------------------|
| **Session** | A single conversation with Claude. When you close Claude Code, the session ends. |
| **Context** | What Claude "remembers" during your conversation - the code it's read, what you've discussed. |
| **Token** | A unit of text (roughly 4 characters or ¾ of a word). Claude counts usage in tokens. |
| **Model** | The AI "brain" - different models (Opus, Sonnet, Haiku) have different capabilities. |
| **Permission Mode** | How cautious Claude is - whether it asks before doing things or acts automatically. |
| **Slash Command** | A command starting with `/` that triggers a specific action, like `/help` or `/config`. |
| **Hook** | An automated script that runs when something happens (like "run spellcheck after every file save"). |
| **MCP** | "Model Context Protocol" - a way to connect Claude to external tools like databases or GitHub. |
| **Subagent** | A specialized AI helper that focuses on one task, like reviewing code or writing tests. |
| **Sandbox** | A restricted environment where Claude can run commands safely without affecting your real system. |

### File Types

| Term | Plain English Definition |
|------|--------------------------|
| **JSON** | A file format for storing settings. Looks like `{"name": "value"}`. Human-readable but structured. |
| **Markdown (.md)** | A simple text format that can include headers, lists, and formatting. This tutorial is written in Markdown. |
| **CLAUDE.md** | A special file where you write instructions for Claude about your project. |
| **settings.json** | A file containing your Claude Code preferences and permissions. |

### Technical Actions

| Term | Plain English Definition |
|------|--------------------------|
| **Execute** | Run a command or script. "Execute npm test" means "run the testing tool". |
| **Parse** | Read and interpret data. Claude "parses" your code to understand it. |
| **Pipe** | Send the output of one command as input to another. Like a factory assembly line. |
| **Debug** | Find and fix problems. "Debug mode" shows extra information to help troubleshoot. |
| **Verbose** | Showing more details than usual. "Verbose mode" means Claude shows everything it's doing. |

---

## 16. ADHD-Friendly Workflows

This section contains strategies specifically designed for developers with ADHD or anyone who struggles with focus, task-switching, or decision fatigue.

### 16.1 The Problem with Traditional Development

If you have ADHD, you probably recognize these struggles:

| Struggle | What It Feels Like |
|----------|-------------------|
| **Analysis Paralysis** | "There are 50 ways to do this. Which is best? I'll research for 3 hours..." |
| **Context Switching Tax** | "I was working on the login bug... wait, what file was I in?" |
| **Working Memory Overload** | "I need to remember: fix the bug, then update tests, then... what was third?" |
| **Hyperfocus Tunnel Vision** | "I spent 6 hours perfecting one function and forgot about the deadline." |
| **Decision Fatigue** | "Should I use async/await or promises? Let me read 10 articles..." |

Claude Code can help with ALL of these. Here's how.

---

### 16.2 Quick Wins: Immediate ADHD Helpers

#### **1. Let Claude Remember For You**

Instead of keeping a mental todo list, externalize it:

```bash
# Start your session by dumping your brain
> Here's what I need to do today:
  - Fix the login timeout bug
  - Add validation to the signup form
  - Write tests for the user service
  Let's start with the first one. Keep track of these for me.
```

Claude will remember and can remind you:
```bash
# Later in the session
> what was I supposed to do after this?

# Claude responds: "You have two remaining tasks:
# 1. Add validation to the signup form
# 2. Write tests for the user service
# Want to start on the signup validation?"
```

#### **2. Reduce Decision Fatigue**

Don't ask "how should I do this?" - let Claude decide:

```bash
# Instead of this (opens rabbit hole):
> What's the best way to implement caching?

# Do this (action-oriented):
> Add caching to the getUserById function. Pick the simplest approach that works.
```

#### **3. Break Hyperfocus Cycles**

Set boundaries at the start:

```bash
> I need to fix the payment bug, but I have a tendency to over-engineer.
  Keep the solution simple - if I start adding features, remind me to stop.
  Time limit: 30 minutes of work, then we ship it.
```

---

### 16.3 Session Templates for ADHD

Copy-paste these to start focused sessions:

#### **The "Just Ship It" Session**
```bash
claude -p "I need to [TASK]. Keep it simple:
- Minimum viable solution only
- No refactoring unrelated code
- No 'nice to have' features
- If I go off track, redirect me
Let's start."
```

> **📋 DT's Workflow:** Use "Just Ship It" for:
> - R package bug fixes: "Fix the NA handling in mediate() - don't refactor the whole function"
> - Teaching deadlines: "Create the homework solution for Week 12 - just the answers, no extra polish"
> - Research revisions: "Address reviewer comment #3 - minimal changes only"

#### **The "Brain Dump" Session**
```bash
claude -p "I have a bunch of scattered thoughts about [PROJECT].
I'm going to dump them all here, then help me organize them into
actionable tasks, prioritized by impact. Here's my dump:
[paste your notes]"
```

> **📋 DT's Workflow:** Use "Brain Dump" for:
> - Research planning: Dump ideas for a new mediation method, let Claude structure a paper outline
> - Teaching prep: Dump topics for a new course module, get organized lecture sequence
> - Dev-tools ideas: Dump feature requests for aiterm, get prioritized roadmap

#### **The "Accountability Partner" Session**
```bash
claude -p "I'm working on [PROJECT] for the next 2 hours.
My goal: [SPECIFIC DELIVERABLE]
Please:
1. Help me stay focused on this one goal
2. If I ask about unrelated things, gently redirect
3. Remind me of the goal if I seem to be drifting"
```

> **📋 DT's Workflow:** Use "Accountability Partner" for:
> - Paper writing: "Goal: finish the Methods section of the JASA paper"
> - Package development: "Goal: complete the vignette for rmediation"
> - Grading sessions: "Goal: grade all 30 STAT 440 submissions"

#### **The "Quick Fix Only" Session**
```bash
claude -p "I have exactly 15 minutes to fix [BUG].
No scope creep. No 'while we're here'. Just the fix.
Here's the error: [paste error]"
```

---

### 16.4 ADHD-Friendly Commands Cheatsheet

| When You Feel... | Use This Command | Why It Helps |
|------------------|------------------|--------------|
| **Overwhelmed by options** | `claude --permission-mode acceptEdits` | Removes decision prompts, Claude just does it |
| **Lost in the codebase** | `> where am I? summarize what I've done` | Instant context recovery |
| **Stuck on where to start** | `> what's the smallest first step?` | Breaks paralysis |
| **Distracted, need to refocus** | `/clear` then restart | Clean slate, fresh start |
| **Afraid of breaking things** | `claude --permission-mode plan` | Read-only mode, just explore |
| **Need to capture progress** | `/export progress.md` | Saves your work externally |
| **Forgot what you were doing** | `claude -c` | Continues last session with full context |

---

### 16.5 Custom Slash Commands for ADHD

Create these in `.claude/commands/` for one-word access:

#### `/focus.md` - Refocus prompt
```markdown
I got distracted. Help me refocus:
1. Summarize what we've accomplished so far
2. What was the original goal?
3. What's the single next step?
4. Is there anything I should finish before context-switching?
```

#### `/checkpoint.md` - Save mental state
```markdown
Create a checkpoint of our current work:
1. What files have been modified?
2. What's working now?
3. What's still broken?
4. What was I about to do next?

Save this summary - I might need to come back to it later.
```

#### `/simplify.md` - Fight over-engineering
```markdown
I think I'm over-engineering. Help me simplify:
1. What's the actual requirement?
2. What's the minimum code to meet it?
3. What can I remove from my current approach?
4. Suggest a simpler solution.
```

#### `/timebox.md` - Add time pressure
```markdown
I have $ARGUMENTS to complete this task.
- Set a hard scope limit
- Prioritize ruthlessly
- Tell me what to skip
- What's the MVP I can ship in this time?
```
Usage: `> /timebox 30 minutes`

---

### 16.6 Environment Setup for ADHD

#### **Reduce Visual Clutter**

```bash
# Minimal output mode
claude --output-format minimal

# Or in settings.json:
{
  "outputFormat": "minimal"
}
```

#### **Auto-Accept to Reduce Interruptions**

Every permission prompt is a potential distraction. Pre-approve safe operations:

```json
// ~/.claude/settings.json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm test:*)",
      "Bash(npm run:*)",
      "Bash(git status:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)"
    ]
  }
}
```

#### **Status Line for Context**

Keep your current task visible in the terminal status bar:

```json
// ~/.claude/settings.json
{
  "statusLine": {
    "type": "command",
    "command": "echo \"📍 $(basename $PWD) | $(git branch --show-current 2>/dev/null || echo 'no git')\""
  }
}
```

---

### 16.7 The ADHD Session Workflow

A complete workflow optimized for ADHD:

```
┌─────────────────────────────────────────────────┐
│  1. BRAIN DUMP (5 min)                          │
│     "Here's everything on my mind..."           │
│     Let Claude organize it                      │
├─────────────────────────────────────────────────┤
│  2. PICK ONE THING (1 min)                      │
│     "What's the highest impact item?"           │
│     Claude suggests, you decide                 │
├─────────────────────────────────────────────────┤
│  3. TIMEBOX IT (set timer)                      │
│     "I have 45 minutes for this"                │
│     External accountability                     │
├─────────────────────────────────────────────────┤
│  4. WORK WITH GUARDRAILS                        │
│     Claude redirects if you drift               │
│     "Remember, we're focused on X"              │
├─────────────────────────────────────────────────┤
│  5. CHECKPOINT (2 min)                          │
│     > /checkpoint                               │
│     Save progress before switching              │
├─────────────────────────────────────────────────┤
│  6. SHIP OR STOP                                │
│     Either finish and commit, or               │
│     explicitly pause and save state             │
└─────────────────────────────────────────────────┘
```

---

### 16.8 Tips for Common ADHD Challenges

#### **When You Can't Start (Task Initiation)**

```bash
# Give Claude permission to just begin
> I'm stuck. Just start coding the solution and explain as you go.
  I'll learn by watching.

# Or ask for the tiniest step
> What's a 5-minute version of this task?
```

#### **When You're Deep in a Rabbit Hole**

```bash
> STOP. I've been on this for [time].
  - Is this actually necessary for the original task?
  - If not, what should I be doing instead?
  - Can we revert the last 30 minutes of changes?
```

#### **When You Forgot Why You're Here**

```bash
# Continue last session
claude -c

# Then ask
> What were we working on? Give me a 30-second summary.
```

#### **When Everything Feels Urgent**

```bash
> I have these tasks and they all feel urgent:
  [list tasks]
  Help me triage:
  - What's actually blocking others?
  - What has a real deadline?
  - What can wait?
  - What can I delegate or skip?
```

#### **When You Need a Break But Can't Stop**

```bash
> I need to take a break but I'm afraid I'll lose context.
  Create a detailed checkpoint so I can walk away safely.
  Include: what's done, what's next, any gotchas to remember.
```

---

### 16.9 ADHD-Friendly Settings Profile

Complete settings for ADHD-optimized Claude Code:

```json
// ~/.claude/settings.json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(git:*)",
      "Bash(npm:*)",
      "Bash(python:*)",
      "Bash(ls:*)",
      "Bash(cat:*)"
    ]
  },
  "alwaysThinkingEnabled": false,
  "model": "claude-sonnet-4-5-20250929"
}
```

Why these settings:
- **acceptEdits**: Fewer interrupting prompts
- **allow list**: Pre-approve common commands
- **alwaysThinkingEnabled: false**: Faster responses, less waiting
- **sonnet model**: Fast enough to maintain flow state

---

### 16.10 Quick Reference Card

Print this or keep it visible:

```
╔═══════════════════════════════════════════════════════╗
║           ADHD QUICK REFERENCE FOR CLAUDE CODE        ║
╠═══════════════════════════════════════════════════════╣
║  STARTING                                             ║
║    claude -c          Resume where you left off       ║
║    /clear             Fresh start, clean slate        ║
║                                                       ║
║  STAYING FOCUSED                                      ║
║    "Keep it simple"   Tell Claude your constraints    ║
║    "Redirect me"      Ask Claude to be your guard     ║
║    /checkpoint        Save mental state               ║
║                                                       ║
║  WHEN STUCK                                           ║
║    "Just start"       Let Claude take initiative      ║
║    "Smallest step?"   Break paralysis                 ║
║    "Summarize"        Get your bearings               ║
║                                                       ║
║  BEFORE STOPPING                                      ║
║    /export FILE.md    Save conversation               ║
║    "Create checkpoint" Document current state         ║
║    git commit         Save your code changes          ║
╚═══════════════════════════════════════════════════════╝
```

---

### 16.11 ADHD-Friendly Plugins & Vetting Guide

Plugins can supercharge your ADHD workflow - but too many plugins can overwhelm Claude and create decision fatigue. Here's a curated guide to the most helpful plugins and how to vet community offerings.

#### **Why Plugins Matter for ADHD**

Plugins automate the things ADHD brains struggle with:
- **Remembering commands** → Plugins activate automatically based on context
- **Maintaining structure** → Plugins enforce consistent workflows
- **Reducing friction** → One-click actions replace multi-step processes
- **Externalizing memory** → Plugins track state so you don't have to

> **⚠️ Warning:** Don't install everything! Too many plugins can make Claude lose focus and slow down responses. Start with 2-3, master them, then add more as needed.

---

#### **Recommended ADHD-Friendly Plugins**

##### **From Official Anthropic Marketplace**

Install with: `/plugin marketplace add anthropics/claude-code`

| Plugin | What It Does | Why It Helps ADHD |
|--------|--------------|-------------------|
| **PR Review Agent** | Automated code review with confidence scoring | No need to remember what to check - it's automated |
| **Security Guidance** | Scans code for vulnerabilities | One less thing to remember during reviews |
| **Agent SDK Verifier** | Validates SDK applications | Catches mistakes you might miss when distracted |

##### **From Community Marketplace (Plugins Plus)**

Install with: `/plugin marketplace add jeremylongshore/claude-code-plugins-plus`

| Plugin | What It Does | Why It Helps ADHD |
|--------|--------------|-------------------|
| **neurodivergent-visual-org** | ADHD-friendly Mermaid diagrams and visual organization | Designed specifically for neurodivergent users |
| **domain-memory-agent** | Builds knowledge base for sustained context | Remembers project details so you don't have to |
| **git-commit-smart** | Auto-generates commit messages | Removes friction from version control |
| **geepers-agents** | 51 specialized development agents | Right tool activates automatically |

##### **Workflow Packages (From awesome-claude-code)**

These aren't single plugins but complete workflow systems:

| Package | What It Does | Best For |
|---------|--------------|----------|
| **Claude Code PM** | Complete project management system | Large projects needing structure |
| **AB Method** | Breaks large problems into focused missions | Analysis paralysis, overwhelm |
| **Agentic Workflow Patterns** | Master-Clone architecture for complex tasks | Multi-step projects |

---

#### **Plugin Installation for ADHD Success**

**Start with this minimal setup:**

```bash
# Step 1: Add official marketplace
> /plugin marketplace add anthropics/claude-code

# Step 2: Add community marketplace (after vetting - see below)
> /plugin marketplace add jeremylongshore/claude-code-plugins-plus

# Step 3: Browse and install ONE plugin to start
> /plugin
# Select a plugin, install it, use it for a week before adding more
```

**ADHD-Friendly Plugin Rules:**
1. **One at a time** - Install one plugin, learn it, then add another
2. **Disable unused plugins** - Keep only active ones enabled
3. **Prefer auto-activating skills** - Less to remember
4. **Avoid overlapping plugins** - Multiple PR reviewers = confusion

---

#### **Vetting Community Plugins: A Safety Checklist**

Community plugins can contain code that runs on your machine. Before installing, check these items:

##### **🟢 Green Flags (Safe to Install)**

| Check | How to Verify |
|-------|---------------|
| **Active maintenance** | Last commit within 3 months |
| **Multiple contributors** | Not just one person's side project |
| **Clear documentation** | README explains what it does and how |
| **Open source code** | You can read the actual code |
| **Stars/forks** | Community validation (50+ stars is good) |
| **Issues are addressed** | Maintainer responds to bug reports |
| **No permission creep** | Only requests permissions it needs |

##### **🟡 Yellow Flags (Proceed with Caution)**

| Warning Sign | What It Means |
|--------------|---------------|
| **No recent commits** | May be abandoned, could have unfixed bugs |
| **Single contributor** | Bus factor of 1, harder to vet |
| **Minimal documentation** | May not work as expected |
| **Few stars/forks** | Not widely tested |
| **Requests broad permissions** | Needs `Bash(*)` instead of specific commands |

##### **🔴 Red Flags (Don't Install)**

| Danger Sign | Why It's Risky |
|-------------|----------------|
| **Obfuscated code** | Can't verify what it does |
| **No source available** | Must trust blindly |
| **Requests secrets/credentials** | Could steal API keys |
| **Modifies system files** | Could damage your setup |
| **No license** | Legal ambiguity |
| **Negative security reports** | Known vulnerabilities |

---

#### **How to Vet a Plugin Step-by-Step**

Before installing any community plugin, follow this checklist:

```markdown
## Plugin Vetting Checklist

Plugin name: _________________
Repository: _________________

### 1. Repository Health
- [ ] Last commit within 6 months
- [ ] More than 1 contributor (or trusted author)
- [ ] Has a LICENSE file
- [ ] Has a README with clear instructions

### 2. Code Review (spend 5 minutes)
- [ ] Open the main code files
- [ ] No suspicious network calls to unknown URLs
- [ ] No file operations outside project directory
- [ ] No credential/secret harvesting

### 3. Permissions Check
- [ ] Review plugin.json for required permissions
- [ ] Permissions match stated functionality
- [ ] No wildcard permissions like Bash(*)

### 4. Community Validation
- [ ] Check GitHub stars (>20 is reasonable)
- [ ] Read recent issues for problems
- [ ] Search for reviews/mentions online

### 5. Test Safely
- [ ] Install in a test project first
- [ ] Monitor what commands it runs
- [ ] Check it does what it claims

Result: [ ] SAFE TO INSTALL  [ ] SKIP
```

---

#### **Quick Vetting Commands**

```bash
# Before installing, check the repo
gh repo view owner/plugin-name

# Check recent activity
gh api repos/owner/plugin-name --jq '.pushed_at, .stargazers_count, .open_issues_count'

# Read the plugin manifest
curl -s https://raw.githubusercontent.com/owner/plugin-name/main/.claude-plugin/plugin.json | jq .

# Check for security issues
gh api repos/owner/plugin-name/security-advisories
```

---

#### **ADHD-Specific Vetting Shortcuts**

If thorough vetting feels overwhelming, use these shortcuts:

| Trust Level | What to Do |
|-------------|------------|
| **Official Anthropic** | Install freely - vetted by Anthropic |
| **Featured in awesome-claude-code** | Generally safe - community curated |
| **1000+ stars** | Widely used, likely safe |
| **From known developer** | Check their other projects first |
| **Unknown source** | Use full checklist above |

> **📋 DT's Workflow:** I stick to official Anthropic plugins plus 2-3 from the curated awesome-claude-code list. For anything else, I spend 5 minutes on the vetting checklist. If I can't verify it quickly, I skip it - there are plenty of trusted alternatives.

---

#### **Managing Plugin Overload**

If you've installed too many plugins and Claude feels slow or unfocused:

```bash
# See what's enabled
> /plugin
# Look at "Enabled Plugins" count

# Disable everything except essentials
> /plugin
# Select each plugin → "Disable"

# Keep only 3-5 active at once
# Re-enable others only when needed for specific tasks
```

**The ADHD Plugin Rule:**
> *"If you can't remember what a plugin does without looking it up, you probably don't need it enabled."*

---

#### **Building Your Own ADHD Plugins**

The best ADHD plugins are often ones you build yourself, tailored to your specific friction points:

```bash
# Create a personal ADHD plugin
mkdir -p ~/.claude/plugins/my-adhd-helpers/.claude-plugin
```

**Example: Focus Enforcer Plugin**

```json
// ~/.claude/plugins/my-adhd-helpers/.claude-plugin/plugin.json
{
  "name": "my-adhd-helpers",
  "version": "1.0.0",
  "description": "Personal ADHD workflow helpers",
  "commands": ["commands/"]
}
```

```markdown
<!-- ~/.claude/plugins/my-adhd-helpers/commands/refocus.md -->
I got distracted. Help me refocus:

1. What was the original task I started with?
2. What have we accomplished so far?
3. What's the ONE next step?
4. Should I finish this before switching, or is it safe to pause?

Be direct. Don't let me wander.
```

Add to Claude Code:
```bash
> /plugin marketplace add ~/.claude/plugins/my-adhd-helpers
```

---

## Resources

### Official Resources
- **Official Documentation:** [code.claude.com/docs](https://code.claude.com/docs)
- **GitHub Repository:** [github.com/anthropics/claude-code](https://github.com/anthropics/claude-code)
- **Issue Tracker:** [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- **Community Discord:** [anthropic.com/discord](https://www.anthropic.com/discord)
- **In-app Help:** Type `/help` or ask "how do I..."

### Plugin Resources
- **Official Plugin Marketplace:** [github.com/anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- **Plugins Blog Post:** [claude.com/blog/claude-code-plugins](https://claude.com/blog/claude-code-plugins)
- **Plugin Documentation:** [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- **Community Plugins Hub:** [github.com/jeremylongshore/claude-code-plugins-plus](https://github.com/jeremylongshore/claude-code-plugins-plus)
- **Awesome Claude Code:** [github.com/hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)

### ADHD & Productivity Resources
- **ADHD + Obsidian + Claude:** [amgad.io/posts/building-ai-assistant-productivity-claude-obsidian](https://amgad.io/posts/building-ai-assistant-productivity-claude-obsidian/)
- **Neurodivergent Visual Org Plugin:** Part of claude-code-plugins-plus marketplace

---

*Tutorial version: December 2025*
*Claude Code version: 2.0.71+*
*Author: Generated with Claude Code*
