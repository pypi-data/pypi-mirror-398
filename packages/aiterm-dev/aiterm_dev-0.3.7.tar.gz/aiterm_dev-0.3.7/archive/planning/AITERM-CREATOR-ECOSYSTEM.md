# aiterm: Creator Ecosystem & IDE Integration

**Generated:** 2025-12-19
**Expanded Vision:** Creation tools + IDE/Terminal integrations

---

## 🎯 EXPANDED SCOPE: From Manager to Creator

**Original Vision:** Manage MCP servers, hooks, plugins, agents
**Expanded Vision:** **CREATE** MCP servers, hooks, plugins, agents + **INTEGRATE** with all modern dev tools

```
┌─────────────────────────────────────────────────────────────┐
│ aiterm: Complete AI Coding Ecosystem Tool                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ LAYER 1: Management (existing plan)                        │
│ - Discover, install, test, configure                       │
│ - MCP servers, hooks, plugins, agents, commands            │
│                                                             │
│ LAYER 2: Creation (NEW!)                                   │
│ - Scaffold new MCP servers from templates                  │
│ - Generate custom plugins with AI assistance               │
│ - Create agents with interactive builders                  │
│ - Build hooks with best-practice templates                 │
│                                                             │
│ LAYER 3: Integration (NEW!)                                │
│ - IDE extensions (Zed, Cursor, Positron, VSCodium)        │
│ - Terminal plugins (Warp, Alacritty, Kitty)               │
│ - Editor integrations (Neovim, Emacs, Vim)                │
│ - Unified settings sync across tools                       │
└─────────────────────────────────────────────────────────────┘
```

---

## PART 1: CREATION TOOLS (Build Your Own)

### 1.1 MCP Server Creation Studio ⭐⭐⭐

**Vision:** From idea to working MCP server in minutes

#### Interactive MCP Builder

```bash
aiterm mcp create my-custom-server
```

**Wizard Flow:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 MCP Server Creator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? What does your server do? (one sentence)
  ▸ Integrates with Trello for project management

? Choose a template:
  ❯ API Integration (REST/GraphQL)
    Database Connection (Postgres/MySQL/MongoDB)
    File System Access
    Web Scraping/Automation
    Data Processing Pipeline
    LLM Integration (call other AI models)
    Custom (start from scratch)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 API Integration Template Selected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? API base URL:
  ▸ https://api.trello.com/1

? Authentication method:
  ❯ API Key
    OAuth 2.0
    Bearer Token
    Basic Auth
    No auth

? What tools should your server provide?

  Available actions from Trello API:
  [x] list_boards
  [x] create_card
  [x] update_card
  [ ] delete_card
  [x] search_cards
  [ ] add_comment

? Programming language:
  ❯ TypeScript (recommended)
    Python
    Go
    Rust

? Include tests?
  ❯ Yes (pytest/jest)
    No

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Generating Server...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Created directory structure
✅ Generated package.json
✅ Created tool definitions
✅ Added authentication handlers
✅ Generated TypeScript types
✅ Created test suite (5 tests)
✅ Added README.md with usage examples
✅ Created docker-compose.yml

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 MCP Server Ready!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Location: ~/projects/mcp-servers/trello-mcp/

Next steps:
1. cd ~/projects/mcp-servers/trello-mcp
2. npm install
3. aiterm mcp test trello-mcp  # Test locally
4. aiterm mcp publish trello-mcp  # Publish to marketplace
```

#### Generated Structure

```
trello-mcp/
├── src/
│   ├── index.ts                 # Main server entry
│   ├── tools/                   # Tool implementations
│   │   ├── list_boards.ts
│   │   ├── create_card.ts
│   │   ├── update_card.ts
│   │   └── search_cards.ts
│   ├── auth/                    # Authentication
│   │   └── api_key.ts
│   ├── types/                   # TypeScript types
│   │   └── trello.ts
│   └── utils/
│       └── api_client.ts
├── tests/                       # Test suite
│   ├── tools/
│   │   └── list_boards.test.ts
│   └── integration.test.ts
├── package.json
├── tsconfig.json
├── README.md                    # Generated documentation
├── .env.example                 # Environment template
└── docker-compose.yml           # For testing
```

#### AI-Assisted Code Generation

```bash
aiterm mcp create my-server --ai-assist
```

**AI Assistant Features:**
- Analyze API documentation automatically
- Generate tool schemas from OpenAPI/Swagger
- Suggest optimal tool names and descriptions
- Generate TypeScript types from JSON examples
- Create comprehensive tests with edge cases
- Write detailed README with examples

**Example:**
```bash
aiterm mcp create github-advanced --ai-assist --from-docs="https://docs.github.com/en/rest"

# AI analyzes GitHub REST API docs
# Generates 50+ tools covering all endpoints
# Creates proper authentication flows
# Adds rate limiting and error handling
# Generates comprehensive test suite
```

#### Templates Library

```bash
aiterm mcp templates
```

**Output:**
```
Available MCP Server Templates:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API Integration Templates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ rest-api              RESTful API integration
⭐ graphql-api           GraphQL API client
⭐ oauth2-api            OAuth 2.0 authenticated API
  webhook-receiver       Receive and process webhooks
  rate-limited-api       API with rate limiting

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database Templates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ postgres              PostgreSQL connection
⭐ mongodb               MongoDB integration
  mysql                  MySQL database
  redis                  Redis cache/queue
  sqlite                 SQLite local database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing Templates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ data-processor        Transform data pipelines
⭐ file-watcher          Monitor file changes
  email-processor        Email parsing/sending
  pdf-generator          PDF creation
  image-processor        Image manipulation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Integration Templates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ llm-integration       Call other AI models
⭐ slack-bot             Slack integration
  discord-bot            Discord bot
  telegram-bot           Telegram bot
  twitter-api            Twitter/X integration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Research Templates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ zotero-integration    Bibliography management
⭐ pubmed-search         PubMed literature search
  arxiv-search           arXiv paper search
  semantic-scholar       Semantic Scholar API
  citation-processor     Format citations
```

#### Publishing to Marketplace

```bash
aiterm mcp publish trello-mcp

# Validation
✅ Tests passing (5/5)
✅ Documentation complete
✅ package.json valid
✅ TypeScript compiles
✅ No security vulnerabilities

# Package
📦 Creating package...
📦 Bundling source...
📦 Including README...

# Upload
🚀 Publishing to marketplace...
🚀 Uploaded to mcp.run
🚀 Submitted for review

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Published: trello-mcp v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Marketplace URL: https://mcp.run/servers/trello-mcp
Install command: aiterm mcp install trello-mcp

Next steps:
- Share with community
- Gather feedback
- Iterate on features
```

**Effort:** 🏗️ Large (2-3 weeks)
**Priority:** 🔥🔥 Very High (differentiation!)

---

### 1.2 Plugin Creation Studio ⭐⭐

**Vision:** Build Claude Code plugins with guided workflow

```bash
aiterm plugin create my-research-plugin
```

**Wizard:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Plugin Creator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Plugin purpose?
  ▸ Research workflow automation

? What components will your plugin include?

  [x] Skills (slash commands)
  [x] Agents (specialized subagents)
  [ ] Hooks (event handlers)
  [x] MCP Servers (custom servers)
  [ ] Commands (built-in commands)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Skills Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How many skills? 3

Skill 1:
? Name: research-literature
? Description: Search and summarize academic papers
? Allowed tools: [Read, WebFetch, Bash]
? Supporting files: [templates/summary.md]

Skill 2:
? Name: research-methods
? Description: Generate statistical methods sections
? Allowed tools: [Read, Write]
? Supporting files: [templates/methods.md]

Skill 3:
? Name: research-cite
? Description: Format citations in multiple styles
? Allowed tools: [Read]
? Supporting files: [data/citation-styles.json]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agents Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How many agents? 1

Agent 1:
? Name: literature-reviewer
? Description: Deep literature review agent
? Allowed tools: [Read, WebFetch, Write]
? Model: sonnet (faster) / opus (smarter): opus

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Generating Plugin...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Created plugin structure
✅ Generated plugin.json
✅ Created 3 skills with SKILL.md files
✅ Created 1 agent configuration
✅ Added supporting templates
✅ Generated README.md
✅ Created test suite

Plugin ready: ~/projects/plugins/my-research-plugin/
```

**Generated Structure:**

```
my-research-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   ├── research-literature/
│   │   ├── SKILL.md             # Skill definition
│   │   └── templates/
│   │       └── summary.md
│   ├── research-methods/
│   │   ├── SKILL.md
│   │   └── templates/
│   │       └── methods.md
│   └── research-cite/
│       ├── SKILL.md
│       └── data/
│           └── citation-styles.json
├── agents/
│   └── literature-reviewer/
│       └── AGENT.md             # Agent configuration
├── tests/
│   └── integration.test.js
└── README.md
```

**AI-Assisted Skill Generation:**

```bash
aiterm plugin skill generate --ai-assist

# AI Assistant:
? Describe what you want the skill to do:
  ▸ I want to analyze R package dependencies and suggest updates

# AI generates:
# - Complete SKILL.md with proper frontmatter
# - R script to parse DESCRIPTION file
# - Logic to check CRAN for updates
# - Output formatting
# - Example usage
```

**Effort:** 🔧 Medium (1 week)
**Priority:** 🔥 High

---

### 1.3 Agent Creation Studio ⭐

**Vision:** Build specialized agents with guided configuration

```bash
aiterm agent create --interactive
```

**Wizard:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent Creator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Agent name:
  ▸ statistical-consultant

? Agent purpose: (one sentence)
  ▸ Provides expert statistical advice and validates analysis plans

? Agent specialty:
  ❯ Research & Data Science
    Code Development
    Documentation Writing
    Testing & QA
    Security Review
    Custom

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Tool Selection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Which tools should this agent have access to?

File Operations:
  [x] Read (read files)
  [ ] Write (create new files)
  [ ] Edit (modify existing files)

Execution:
  [x] Bash (run R scripts, check packages)
  [ ] Python
  [ ] Docker

Web Access:
  [x] WebFetch (fetch statistical resources)
  [x] WebSearch (search for methods)

Analysis:
  [ ] TodoWrite (task management)
  [ ] Grep (code search)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 Model Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Primary model:
  ❯ opus (smarter, better for complex stats)
    sonnet (faster, good for routine tasks)
    haiku (fastest, for simple queries)

? Fallback model (if primary overloaded):
  ❯ sonnet
    None

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 System Prompt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I've generated a starting prompt based on "statistical consultant":

---
You are an expert statistical consultant with deep knowledge of:
- Experimental design and causal inference
- Regression models (linear, logistic, mixed-effects)
- Statistical power and sample size calculations
- Multiple testing corrections
- Bayesian and frequentist approaches

When analyzing data or reviewing analysis plans:
1. Check assumptions (normality, independence, etc.)
2. Suggest appropriate statistical tests
3. Identify potential confounders
4. Recommend sensitivity analyses
5. Explain results in plain language

You have access to R for running statistical tests.
---

? Edit this prompt? [y/N]: y
```

Opens in `$EDITOR` for customization.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Behavior Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Max iterations (prevent infinite loops):
  ▸ 25

? Timeout per invocation (seconds):
  ▸ 600 (10 minutes)

? Automatic approval mode:
  ❯ Plan mode (agent plans, user approves)
    Full autonomy (agent executes freely)
    Delegate mode (ask permission for each tool)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Generating Agent...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Created agent configuration
✅ Generated AGENT.md
✅ Created test invocation script
✅ Added example prompts
✅ Created documentation

Agent ready: ~/.claude/agents/statistical-consultant/
```

**Test Agent:**

```bash
aiterm agent test statistical-consultant

# Runs test invocation:
Test prompt: "Review my analysis plan for a randomized trial with 3 arms"

Agent response:
I'll review your trial design. Let me check a few key aspects:

1. Randomization method: What's your randomization approach?
2. Sample size: Have you done power calculations?
3. Primary outcome: Is it clearly defined and measurable?
4. Multiple testing: With 3 arms, you'll need corrections...

[Agent continues with detailed statistical review]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Test Passed
Agent responded appropriately with statistical expertise
```

**Effort:** ⚡ Quick (2-3 days)
**Priority:** Medium

---

### 1.4 Hook Creation Studio ⭐⭐

**Vision:** Build custom hooks with templates and validation

```bash
aiterm hook create --interactive
```

**Wizard:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🪝 Hook Creator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Hook name:
  ▸ project-context-loader

? Hook type:
  ❯ SessionStart (runs when Claude starts)
    UserPromptSubmit (enhances user prompts)
    PreToolUse (before tool execution)
    PostToolUse (after tool execution)
    PermissionRequest (auto-approve decisions)
    SessionEnd (cleanup on exit)
    Stop (control when Claude stops)
    PreCompact (before context shrinking)
    Notification (custom alerts)

? What should this hook do?
  ▸ Load project-specific context (.STATUS, TODOS.md) on session start

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Hook Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SessionStart hooks receive:
- CWD (current working directory)
- SESSION_ID
- CLAUDE_VERSION
- MODEL

? What files should this hook read?
  [x] .STATUS (project status)
  [x] TODOS.md (task list)
  [x] CLAUDE.md (project context)
  [ ] Custom: ___________

? Output format:
  ❯ Markdown block (will be shown to user)
    JSON data (for machine processing)
    Silent (no output, just logging)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Generating Hook...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Created hook script
✅ Added error handling
✅ Included validation logic
✅ Generated tests
✅ Created documentation

Hook ready: ~/.claude/hooks/project-context-loader.sh
```

**Generated Hook (Bash):**

```bash
#!/usr/bin/env bash
# Hook: project-context-loader
# Type: SessionStart
# Description: Load project context on session start

set -euo pipefail

# Read environment variables
CWD="${CLAUDECODE_CWD:-$(pwd)}"
SESSION_ID="${CLAUDECODE_SESSION_ID:-unknown}"

# Initialize output
OUTPUT=""

# Check for .STATUS file
if [[ -f "$CWD/.STATUS" ]]; then
    OUTPUT+="## Project Status\n\n"
    OUTPUT+="$(cat "$CWD/.STATUS")\n\n"
fi

# Check for TODOS.md
if [[ -f "$CWD/TODOS.md" ]]; then
    OUTPUT+="## Active Tasks\n\n"
    OUTPUT+="$(head -20 "$CWD/TODOS.md")\n\n"
fi

# Check for CLAUDE.md
if [[ -f "$CWD/CLAUDE.md" ]]; then
    OUTPUT+="## Project Context\n\n"
    OUTPUT+="Project has CLAUDE.md with specific instructions.\n\n"
fi

# Output to Claude
if [[ -n "$OUTPUT" ]]; then
    echo -e "$OUTPUT"
fi

exit 0
```

**AI-Assisted Hook Generation:**

```bash
aiterm hook create auto-linter --ai-assist

# AI Assistant:
? Describe what you want this hook to do:
  ▸ Run ESLint after every file edit and show results

# AI generates:
# - PostToolUse hook
# - Detects JavaScript/TypeScript edits
# - Runs eslint on modified files
# - Formats output nicely
# - Handles errors gracefully
# - Includes config validation
```

**Effort:** 🔧 Medium (3-5 days)
**Priority:** 🔥 High

---

## PART 2: IDE & TERMINAL INTEGRATIONS (Connect Everything)

### 2.1 IDE Integration Framework ⭐⭐⭐

**Vision:** aiterm works seamlessly with ALL modern editors

#### Supported IDEs & Editors

```
┌─────────────────────────────────────────────────────────────┐
│ IDE/Editor Integrations                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Modern IDEs:                                                │
│ ⭐ Zed (native Rust editor)                                 │
│ ⭐ Cursor (AI-first fork of VS Code)                        │
│ ⭐ Positron (data science IDE)                              │
│ ⭐ VSCodium (open-source VS Code)                           │
│ ⭐ VS Code (most popular)                                   │
│                                                             │
│ Traditional Editors:                                        │
│ ⭐ Neovim (extensible Vim)                                  │
│ ⭐ Emacs (extensible Lisp editor)                           │
│   Vim                                                       │
│   Sublime Text                                              │
│                                                             │
│ JetBrains IDEs:                                             │
│   IntelliJ IDEA                                             │
│   PyCharm                                                   │
│   WebStorm                                                  │
│   RStudio (R development)                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Integration Types

**Type 1: Extension/Plugin (for Zed, Cursor, VS Code, etc.)**

```bash
aiterm integrate zed
```

**What It Does:**
1. Generates Zed extension in Rust
2. Provides commands in Zed command palette
3. Status bar integration
4. Settings sync

**Generated Zed Extension:**

```rust
// zed-aiterm/src/lib.rs
use zed_extension_api as zed;

struct AitermExtension;

impl zed::Extension for AitermExtension {
    fn new() -> Self {
        AitermExtension
    }

    fn activate(&mut self, worktree: &zed::Worktree) {
        // Detect project context
        let context = detect_project_context(worktree);

        // Switch terminal profile
        switch_terminal_profile(&context);

        // Show in status bar
        show_status(&context);
    }

    fn commands(&self) -> Vec<zed::Command> {
        vec![
            zed::Command {
                name: "aiterm: Switch Profile",
                run: Box::new(|_| switch_profile_interactive()),
            },
            zed::Command {
                name: "aiterm: Show MCP Servers",
                run: Box::new(|_| show_mcp_servers()),
            },
            zed::Command {
                name: "aiterm: Manage Hooks",
                run: Box::new(|_| manage_hooks()),
            },
        ]
    }
}

zed::register_extension!(AitermExtension);
```

**Zed Extension Features:**
- Command palette integration
- Status bar context display
- Automatic profile switching on project open
- MCP server status in sidebar
- Hook management UI

**Type 2: Language Server Protocol (LSP) Integration**

```bash
aiterm lsp start
```

**What It Provides:**
- Code completions for MCP tool names
- Hover documentation for hooks
- Diagnostics for plugin.json validation
- Code actions (create hook, add MCP server)

**Type 3: Settings Sync**

```bash
aiterm sync zed
```

**What It Does:**
- Reads Zed settings from `~/.config/zed/settings.json`
- Syncs with aiterm configuration
- Ensures consistent behavior across tools

#### Cursor Integration ⭐

**Vision:** Deep integration with Cursor's AI features

```bash
aiterm integrate cursor
```

**Generated Extension:**

```typescript
// cursor-aiterm/src/extension.ts
import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    // Status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );

    // Detect project context
    const detectContext = () => {
        exec('aiterm detect --json', (error, stdout) => {
            if (!error) {
                const context = JSON.parse(stdout);
                statusBarItem.text = `$(project) ${context.type}`;
                statusBarItem.show();

                // Switch terminal profile
                exec(`aiterm switch`);
            }
        });
    };

    // Run on activation
    detectContext();

    // Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('aiterm.switchProfile', () => {
            // Show profile picker
            exec('aiterm profile list --json', (error, stdout) => {
                const profiles = JSON.parse(stdout);
                vscode.window.showQuickPick(profiles).then(selected => {
                    exec(`aiterm switch --profile=${selected}`);
                });
            });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('aiterm.mcpStatus', () => {
            // Show MCP server status
            exec('aiterm mcp list --json', (error, stdout) => {
                const servers = JSON.parse(stdout);
                // Display in webview
                showMCPStatus(servers);
            });
        })
    );
}
```

**Cursor-Specific Features:**
- Integration with Cursor's AI chat (suggest MCP servers)
- Context-aware code completions using aiterm
- Automatic MCP server recommendations
- Hook suggestions based on project type

#### Positron Integration ⭐

**Vision:** Specialized for data science workflows

```bash
aiterm integrate positron
```

**Positron-Specific Features:**
- R package context detection
- Automatic statistical-research MCP server activation
- Jupyter notebook integration
- Python environment detection
- Data viewer integration

**Generated Extension:**

```typescript
// positron-aiterm/src/extension.ts
import * as positron from '@positron/api';

export function activate(context: positron.ExtensionContext) {
    // Detect R package
    if (positron.workspace.hasFile('DESCRIPTION')) {
        // Activate R-specific MCP servers
        activateMCP('r-execution');
        activateMCP('statistical-research');

        // Show R package tools in sidebar
        showRPackageTools();
    }

    // Detect Python project
    if (positron.workspace.hasFile('pyproject.toml')) {
        activateMCP('python-env');
        activateMCP('jupyter-mcp');
    }
}
```

#### VSCodium Integration ⭐

**Vision:** Open-source VS Code with aiterm

```bash
aiterm integrate vscodium
```

**Same as VS Code integration:**
- Full extension support
- Settings sync
- Command palette
- Status bar

#### Neovim Integration ⭐⭐

**Vision:** Lua plugin for Neovim

```bash
aiterm integrate neovim
```

**Generated Plugin:**

```lua
-- nvim-aiterm/lua/aiterm/init.lua
local M = {}

-- Detect project context on buffer enter
vim.api.nvim_create_autocmd("BufEnter", {
    callback = function()
        local result = vim.fn.system("aiterm detect --json")
        local context = vim.fn.json_decode(result)

        -- Set statusline
        vim.g.aiterm_context = context.type

        -- Switch terminal profile
        vim.fn.system("aiterm switch")

        -- Show notification
        vim.notify("Project: " .. context.type, vim.log.levels.INFO)
    end
})

-- Commands
vim.api.nvim_create_user_command("AitermSwitch", function()
    -- Interactive profile picker
    local profiles = vim.fn.json_decode(
        vim.fn.system("aiterm profile list --json")
    )
    vim.ui.select(profiles, {
        prompt = "Select profile:"
    }, function(choice)
        vim.fn.system("aiterm switch --profile=" .. choice)
    end)
end, {})

vim.api.nvim_create_user_command("AitermMCP", function()
    -- Show MCP servers in floating window
    local servers = vim.fn.json_decode(
        vim.fn.system("aiterm mcp list --json")
    )
    show_mcp_window(servers)
end, {})

return M
```

**Neovim-Specific Features:**
- Lua API for scripting
- Telescope integration (fuzzy finder for MCP servers)
- Statusline components (lualine, galaxyline)
- Autocommands for context switching
- Keybindings for quick actions

#### Emacs Integration ⭐⭐

**Vision:** Emacs Lisp package

```bash
aiterm integrate emacs
```

**Generated Package:**

```elisp
;;; aiterm.el --- aiterm integration for Emacs -*- lexical-binding: t; -*-

;;; Commentary:
;; Provides aiterm functionality in Emacs

;;; Code:

(defun aiterm-detect-context ()
  "Detect project context and switch profile."
  (interactive)
  (let* ((json-output (shell-command-to-string "aiterm detect --json"))
         (context (json-read-from-string json-output))
         (project-type (cdr (assoc 'type context))))

    ;; Update mode line
    (setq aiterm-current-context project-type)
    (force-mode-line-update)

    ;; Switch terminal profile
    (shell-command "aiterm switch")

    ;; Show message
    (message "Project: %s" project-type)))

(defun aiterm-mcp-status ()
  "Show MCP server status."
  (interactive)
  (let* ((json-output (shell-command-to-string "aiterm mcp list --json"))
         (servers (json-read-from-string json-output)))
    (with-current-buffer (get-buffer-create "*aiterm-mcp*")
      (erase-buffer)
      (insert "MCP Servers:\n\n")
      (dolist (server servers)
        (insert (format "- %s: %s\n"
                       (cdr (assoc 'name server))
                       (cdr (assoc 'status server)))))
      (pop-to-buffer (current-buffer)))))

;; Hooks
(add-hook 'find-file-hook #'aiterm-detect-context)

;; Mode line
(setq-default mode-line-format
  (append mode-line-format
          '(:eval (when (boundp 'aiterm-current-context)
                    (format " [%s]" aiterm-current-context)))))

(provide 'aiterm)
;;; aiterm.el ends here
```

**Emacs-Specific Features:**
- Mode line integration
- Helm/Ivy completion for MCP servers
- Org-mode integration (capture hooks to org)
- Magit integration (git hooks)
- Projectile integration (project detection)

**Effort (All IDE Integrations):** 🏗️ MASSIVE (4-6 weeks for all)
**Priority:** 🔥 Very High (huge value-add!)

---

### 2.2 Terminal Integration Framework ⭐⭐

**Vision:** Plugins for modern terminals

#### Warp Integration ⭐

**Generated Plugin:**

```bash
aiterm integrate warp
```

**What It Creates:**
1. Warp workflow files (`~/.warp/workflows/`)
2. Custom commands in Warp
3. Theme integration
4. Status bar blocks

**Warp Workflow Example:**

```yaml
# ~/.warp/workflows/aiterm-switch.yaml
name: Switch Profile
command: aiterm switch --interactive
description: Switch terminal profile based on project context
tags: [aiterm, context]
arguments:
  - name: profile
    description: Profile to switch to
    optional: true
```

**Warp Block (Status Bar):**

```typescript
// warp-aiterm/src/status-block.ts
export function getStatusBlock(): string {
    const context = execSync('aiterm detect --json').toString();
    const data = JSON.parse(context);

    return `[${data.type}] ${data.name}`;
}
```

#### Alacritty Integration

```bash
aiterm integrate alacritty
```

**What It Does:**
- Generates Alacritty config snippets
- Creates shell integration script
- Provides color scheme switcher

**Generated Config:**

```yaml
# ~/.config/alacritty/aiterm-themes/r-dev.yml
colors:
  primary:
    background: '#1e1e2e'
    foreground: '#cdd6f4'
  normal:
    blue: '#89b4fa'
    green: '#a6e3a1'
    # ... (full color scheme)
```

**Shell Integration:**

```bash
# ~/.config/alacritty/aiterm-integration.sh
#!/bin/bash

# Detect context on cd
cd() {
    builtin cd "$@"
    aiterm switch --quiet
    # Reload Alacritty config
    touch ~/.config/alacritty/alacritty.yml
}
```

#### Kitty Integration

```bash
aiterm integrate kitty
```

**What It Does:**
- Uses Kitty's remote control protocol
- Switches themes dynamically
- Updates tab titles

**Generated Script:**

```bash
# ~/.config/kitty/aiterm-integration.sh
#!/bin/bash

# Detect context
CONTEXT=$(aiterm detect --json | jq -r '.type')

# Switch Kitty theme
case "$CONTEXT" in
    "r-package")
        kitty @ set-colors --all ~/.config/kitty/themes/r-dev.conf
        ;;
    "python")
        kitty @ set-colors --all ~/.config/kitty/themes/python-dev.conf
        ;;
esac

# Update tab title
kitty @ set-tab-title "$CONTEXT"
```

**Effort (All Terminal Integrations):** 🔧 Medium (2-3 weeks)
**Priority:** 🔥 High

---

### 2.3 Universal Integration CLI ⭐⭐⭐

**Vision:** One command to integrate with anything

```bash
aiterm integrate --scan
```

**Output:**

```
Scanning system for supported tools...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found Editors/IDEs:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Cursor (/Applications/Cursor.app)
✅ Zed (/Applications/Zed.app)
✅ Positron (/Applications/Positron.app)
⚠️  VS Code (detected but using VSCodium)
✅ VSCodium (/Applications/VSCodium.app)
✅ Neovim (/opt/homebrew/bin/nvim)
✅ Emacs (/Applications/Emacs.app)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found Terminals:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ iTerm2 (/Applications/iTerm.app)
✅ Warp (/Applications/Warp.app)
✅ Alacritty (~/.config/alacritty/)
✅ Kitty (~/.config/kitty/)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Integration Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cursor       [Not integrated]  aiterm integrate cursor
Zed          [Not integrated]  aiterm integrate zed
Positron     [Not integrated]  aiterm integrate positron
VSCodium     [Not integrated]  aiterm integrate vscodium
Neovim       [Not integrated]  aiterm integrate neovim
Emacs        [Not integrated]  aiterm integrate emacs

iTerm2       [✅ Integrated]   v0.1.0 features
Warp         [Not integrated]  aiterm integrate warp
Alacritty    [Not integrated]  aiterm integrate alacritty
Kitty        [Not integrated]  aiterm integrate kitty
```

**Batch Integration:**

```bash
aiterm integrate --all

# Or selectively:
aiterm integrate cursor zed positron neovim

# Interactive:
aiterm integrate --interactive
? Which tools to integrate? (select multiple)
  [x] Cursor
  [x] Zed
  [ ] Positron
  [x] Neovim
  [ ] Emacs
  [x] Warp
```

**Effort:** 🔧 Medium (1 week for CLI framework)
**Priority:** 🔥 Very High (makes integration easy!)

---

## PART 3: UNIFIED SETTINGS SYNC ⭐⭐

**Vision:** Consistent configuration across all tools

### Settings Sync Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ aiterm Settings (Single Source of Truth)                   │
├─────────────────────────────────────────────────────────────┤
│ ~/.config/aiterm/config.json                                │
│                                                             │
│ {                                                           │
│   "terminal": {                                             │
│     "profiles": [...],                                      │
│     "contexts": [...]                                       │
│   },                                                        │
│   "claude": {                                               │
│     "mcp_servers": [...],                                   │
│     "hooks": [...],                                         │
│     "plugins": [...]                                        │
│   },                                                        │
│   "integrations": {                                         │
│     "cursor": { "enabled": true, "sync": true },            │
│     "zed": { "enabled": true, "sync": true },               │
│     "neovim": { "enabled": true, "sync": false }            │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                        ↓ syncs to
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Cursor       │ Zed          │ Neovim       │ Warp         │
│ settings.json│ settings.json│ init.lua     │ config.yaml  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Commands

```bash
aiterm sync status
# Shows which tools are in sync

aiterm sync push
# Push aiterm config to all tools

aiterm sync pull cursor
# Pull Cursor settings into aiterm

aiterm sync diff zed
# Show differences between aiterm and Zed config

aiterm sync watch
# Watch for changes and auto-sync
```

**Effort:** 🏗️ Large (2 weeks)
**Priority:** Medium (nice-to-have)

---

## PART 4: IMPLEMENTATION ROADMAP (REVISED)

### Phase 1: Foundation (v0.2.0) - Week 1-3 🔥

**Core Management + Creation Basics**

1. ⭐⭐⭐ MCP Server Management (2 weeks)
   - Discovery, install, test, config
   - Marketplace integration

2. ⭐⭐⭐ Hook Management (1 week)
   - Template library
   - Validation & testing

3. ⭐⭐ MCP Creation Studio (1 week)
   - `aiterm mcp create` wizard
   - 5 starter templates
   - AI-assisted generation

4. ⭐ Hook Creation Studio (3-5 days)
   - `aiterm hook create` wizard
   - Best-practice templates

5. ⭐ Quota Tracking (2-3 days)
   - Quick win!

**Deliverable:** v0.2.0 with management + basic creation

---

### Phase 2: Expansion (v0.3.0) - Week 4-6 🚀

**More Creation + IDE Integration**

1. ⭐⭐ Plugin Creation Studio (1 week)
   - `aiterm plugin create` wizard
   - Component scaffolding

2. ⭐⭐⭐ Cursor Integration (1 week)
   - VS Code extension
   - Status bar, commands

3. ⭐⭐⭐ Zed Integration (1 week)
   - Rust extension
   - Native integration

4. ⭐⭐ Neovim Integration (3-5 days)
   - Lua plugin
   - Telescope integration

5. ⭐ Agent Creation Studio (2-3 days)
   - `aiterm agent create` wizard

**Deliverable:** v0.3.0 with creation tools + IDE integrations

---

### Phase 3: Advanced Integration (v0.4.0) - Week 7-9 🌐

**More IDEs + Terminal Plugins**

1. ⭐⭐ Positron Integration (1 week)
   - Data science features
   - R package support

2. ⭐⭐ VSCodium Integration (3-5 days)
   - Same as VS Code

3. ⭐ Emacs Integration (1 week)
   - Elisp package
   - Org-mode integration

4. ⭐⭐ Warp Integration (3-5 days)
   - Workflow files
   - Status blocks

5. ⭐ Alacritty + Kitty Integration (3-5 days each)
   - Config generation
   - Shell integration

**Deliverable:** v0.4.0 with comprehensive IDE/terminal support

---

### Phase 4: Intelligence (v1.0.0) - Month 3 🧠

**AI-Assisted Creation + Settings Sync**

1. ⭐⭐⭐ AI-Assisted MCP Generation (2 weeks)
   - Analyze API docs automatically
   - Generate from OpenAPI/Swagger
   - Create comprehensive tests

2. ⭐⭐ AI-Assisted Plugin Generation (1 week)
   - Generate skills from descriptions
   - Auto-create agents
   - Smart hook suggestions

3. ⭐⭐ Settings Sync (1 week)
   - Unified config
   - Push/pull across tools
   - Watch mode

4. ⭐ Context-Aware Recommendations (3-5 days)
   - Suggest MCP servers by project
   - Hook recommendations

5. ⭐ Template Marketplace (1 week)
   - Share templates
   - Community contributions

**Deliverable:** v1.0.0 public release with AI-powered creation

---

## PART 5: SUCCESS METRICS (REVISED)

### v0.2.0 Success (Week 3)
- [ ] MCP management working (install, test, validate)
- [ ] Hook management working (template library)
- [ ] `aiterm mcp create` creates working server
- [ ] `aiterm hook create` creates valid hook
- [ ] 5+ MCP templates available
- [ ] 10+ hook templates available

### v0.3.0 Success (Week 6)
- [ ] Plugin creation working
- [ ] Cursor extension published
- [ ] Zed extension published
- [ ] Neovim plugin working
- [ ] Users can create plugins from templates

### v0.4.0 Success (Week 9)
- [ ] 5+ IDE integrations working
- [ ] 4+ terminal integrations working
- [ ] Positron support for R developers
- [ ] Emacs package in MELPA

### v1.0.0 Success (Month 3)
- [ ] AI-assisted MCP generation working
- [ ] Settings sync across all tools
- [ ] 100+ external users
- [ ] 20+ community-created MCP servers
- [ ] Template marketplace launched

---

## PART 6: KILLER FEATURES (What Makes This AMAZING)

### 🔥 Feature 1: MCP Creation from API Docs

```bash
aiterm mcp create github-advanced \
  --from-docs="https://docs.github.com/en/rest" \
  --ai-assist

# AI reads entire GitHub API docs
# Generates 50+ tools covering all endpoints
# Creates proper TypeScript types
# Adds OAuth 2.0 flow
# Includes rate limiting
# Generates 100+ tests
# Result: Production-ready MCP server in minutes!
```

### 🔥 Feature 2: One-Command IDE Integration

```bash
aiterm integrate --all

# Scans system for all supported tools
# Generates extensions for each
# Installs automatically
# Result: aiterm works everywhere!
```

### 🔥 Feature 3: AI-Powered Plugin Builder

```bash
aiterm plugin create my-research-plugin --ai-assist

# Describe what you want:
"I want to automate my research workflow:
- Search PubMed for papers
- Extract citations
- Generate bibliography
- Summarize methods sections"

# AI generates:
# - 4 skills with proper tool access
# - Agent for literature review
# - MCP server for PubMed
# - Hook for auto-citation
# - Complete tests
# Result: Full plugin in 5 minutes!
```

---

**Last Updated:** 2025-12-19
**Status:** 🟢 Ready for implementation
**Next Action:** Choose Phase 1 start date, begin with MCP Creation Studio
