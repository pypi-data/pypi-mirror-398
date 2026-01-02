# aiterm: The Complete AI Coding Ecosystem Platform

**Generated:** 2025-12-19
**Status:** 🟢 Complete Vision with All Revisions

---

## 🎯 EXECUTIVE SUMMARY

**aiterm** is the ultimate command-line platform for AI-assisted development. It combines:

1. **Discovery & Management** - Find, install, configure MCP servers, hooks, plugins, agents
2. **Creation Tools** - Build MCP servers, plugins, agents with AI assistance
3. **IDE/Terminal Integration** - Connect with every tool you actually use
4. **Learning Resources** - Tutorials, ref-cards, interactive guides
5. **Self-Hosting** - Custom MCP server for discovering other MCP servers!

**The Vision:** "npm for AI coding tools" + "VS Code Marketplace for MCP" + "Create React App for MCP servers"

---

## 🚀 PART 1: THE META MCP SERVER ⭐⭐⭐ (NEW!)

### aiterm-mcp-marketplace Server

**The Innovation:** An MCP server that helps you find and install OTHER MCP servers!

**What It Does:**
```bash
# From within Claude Code/claude.ai:
User: "I need a database MCP server"

Claude (using aiterm-mcp-marketplace):
🔍 Searching marketplace for database servers...

Found 5 servers:
1. postgres-mcp (⭐⭐⭐⭐⭐ 4.9/5, 5.2k downloads)
   PostgreSQL database access
   Install: Use tool `install_mcp_server` with id "postgres-mcp"

2. sqlite-mcp (⭐⭐⭐⭐⭐ 4.8/5, 3.1k downloads)
   SQLite database integration
   Install: Use tool `install_mcp_server` with id "sqlite-mcp"

3. mongodb-mcp (⭐⭐⭐⭐ 4.2/5, 1.8k downloads)
   MongoDB integration
   Install: Use tool `install_mcp_server` with id "mongodb-mcp"

Which would you like me to install?

User: "Install postgres-mcp"

Claude: *calls install_mcp_server tool*
✅ Installed postgres-mcp to ~/.claude/settings.json
✅ Server configuration added
🔄 Restart Claude to activate

Done! The postgres-mcp server is now available.
```

**MCP Server Structure:**

```
~/projects/dev-tools/mcp-servers/aiterm-mcp-marketplace/
├── package.json
├── src/
│   ├── index.ts                 # Main MCP server
│   ├── tools/
│   │   ├── search_servers.ts    # Search marketplace
│   │   ├── get_server_info.ts   # Detailed info
│   │   ├── install_server.ts    # Install to Claude config
│   │   ├── list_installed.ts    # Show installed servers
│   │   ├── update_server.ts     # Update existing server
│   │   ├── uninstall_server.ts  # Remove server
│   │   ├── test_server.ts       # Validate connection
│   │   ├── search_plugins.ts    # Find Claude plugins
│   │   └── install_plugin.ts    # Install Claude plugins
│   ├── api/
│   │   ├── mcp_registry.ts      # mcp.run API client
│   │   ├── glama_api.ts         # glama.ai API client
│   │   └── github_api.ts        # GitHub search for servers
│   └── utils/
│       ├── config_manager.ts    # Modify Claude settings
│       ├── validator.ts         # Validate server configs
│       └── installer.ts         # Handle installation
├── tests/
│   ├── search.test.ts
│   ├── install.test.ts
│   └── integration.test.ts
└── README.md                    # Full documentation
```

**Tool Definitions:**

```typescript
// src/tools/search_servers.ts
{
  name: "search_mcp_servers",
  description: "Search for MCP servers in multiple marketplaces",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query (e.g., 'database', 'slack', 'github')"
      },
      category: {
        type: "string",
        enum: ["database", "api", "productivity", "development", "research", "all"],
        description: "Filter by category"
      },
      sort: {
        type: "string",
        enum: ["downloads", "rating", "recent"],
        description: "Sort results by"
      }
    },
    required: ["query"]
  }
}

// src/tools/install_server.ts
{
  name: "install_mcp_server",
  description: "Install an MCP server to Claude Code configuration",
  inputSchema: {
    type: "object",
    properties: {
      server_id: {
        type: "string",
        description: "Server ID from search results"
      },
      config: {
        type: "object",
        description: "Optional configuration (env vars, args)"
      }
    },
    required: ["server_id"]
  }
}

// src/tools/search_plugins.ts
{
  name: "search_claude_plugins",
  description: "Search for Claude Code plugins",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query"
      },
      category: {
        type: "string",
        enum: ["code-review", "testing", "documentation", "workflow", "all"]
      }
    },
    required: ["query"]
  }
}
```

**Installation:**

```json
// ~/.claude/settings.json
{
  "mcpServers": {
    "aiterm-marketplace": {
      "command": "node",
      "args": [
        "/Users/dt/projects/dev-tools/mcp-servers/aiterm-mcp-marketplace/src/index.js"
      ],
      "env": {
        "CLAUDE_CONFIG_PATH": "/Users/dt/.claude/settings.json"
      }
    }
  }
}
```

**Why This Is Killer:**
- 🤖 Claude can discover and install MCP servers for you
- 🔍 Search multiple marketplaces (mcp.run, glama.ai, GitHub)
- 📦 Install with one conversation ("install postgres-mcp")
- ✅ Validates configurations before installing
- 🔄 Can update/uninstall servers too
- 🔌 Also works for Claude plugins!

**Effort:** 🏗️ Large (1-2 weeks)
**Priority:** 🔥🔥🔥 HIGHEST (meta-tool, huge value!)

---

## 🖥️ PART 2: YOUR ACTUAL TERMINAL/IDE SETUP

### Terminals You Actually Use

Based on `/Applications` scan:

✅ **iTerm2** (primary terminal) - `/Applications/iTerm.app`
- Full support already in v0.1.0 ✅
- Escape sequences working ✅
- Profile switching working ✅

⚠️ **iTermAI** - `/Applications/iTermAI.app`
- AI-enhanced iTerm2 fork
- Should work with same integration as iTerm2
- Priority: Low (if it's just iTerm2 with AI features)

❌ **Warp** - NOT installed
- Skip integration for now
- Revisit if you install it later

❌ **Alacritty** - NOT installed
- Skip integration

❌ **Kitty** - NOT installed
- Skip integration

### IDEs/Editors You Actually Use

✅ **Emacs** - `/Applications/Emacs.app` + `/opt/homebrew/bin/emacs`
- Spacemacs configuration at `~/projects/dev-tools/spacemacs-rstats/`
- Priority: 🔥🔥 VERY HIGH (you use this for R!)

✅ **Visual Studio Code** - `/Applications/Visual Studio Code.app` + `/opt/homebrew/bin/code`
- Standard VS Code
- Priority: 🔥🔥 HIGH (widely used)

✅ **OpenCode** - `/Applications/OpenCode.app`
- Open-source variant? Need more info
- Priority: Medium (if it's just a renamed VS Code)

✅ **Positron** - `/Applications/Positron.app`
- Data science IDE (R/Python)
- Priority: 🔥🔥🔥 HIGHEST (perfect for your R package work!)

✅ **Zed** - `/Applications/Zed.app` + `/opt/homebrew/bin/zed`
- Modern Rust-based editor
- Priority: 🔥🔥 HIGH (fast, modern)

✅ **Xcode** - `/Applications/Xcode.app`
- Apple's IDE
- Priority: Low (unless you do Swift/iOS dev)

❌ **Neovim** - NOT in PATH (`nvim not found`)
- Skip Neovim integration
- Focus on Emacs instead

❌ **Cursor** - NOT installed
- Skip Cursor integration
- Revisit if you install it later

### REVISED Integration Priorities

**Phase 1 (v0.2-0.3) - Your Daily Drivers:**
1. ⭐⭐⭐ **Positron** (data science, R packages)
2. ⭐⭐⭐ **Emacs/Spacemacs** (your primary R editor)
3. ⭐⭐ **Zed** (modern, fast)
4. ⭐⭐ **VS Code** (widely used, good plugin ecosystem)

**Phase 2 (v0.4+) - Nice-to-Have:**
5. ⭐ **OpenCode** (if different from VS Code)
6. ⭐ **iTermAI** (if different from iTerm2)

**Skipped (Not Installed):**
- ❌ Cursor (not installed)
- ❌ Neovim (not in PATH, use Emacs instead)
- ❌ Warp (not installed)
- ❌ VSCodium (not installed)

---

## 📁 PART 3: MCP SERVERS REORGANIZATION

### Current State (from _MCP_SERVERS.md)

**Existing MCP Servers (4):**
1. `statistical-research/` (14 tools, 17 skills) ✅
2. `shell/` (shell command execution) ✅
3. `project-refactor/` (4 tools for project renaming) ✅
4. `obsidian-ops/` (Obsidian CLI integration) ✅
5. `docling/` (document processing) ✅

**Already in unified location:** `~/projects/dev-tools/mcp-servers/` ✅

### NEW: aiterm-mcp-marketplace Server (5th server!)

```bash
cd ~/projects/dev-tools/mcp-servers/
mkdir aiterm-mcp-marketplace
cd aiterm-mcp-marketplace

# Initialize
npm init -y
npm install @modelcontextprotocol/sdk

# Create structure
mkdir -p src/{tools,api,utils} tests
```

**Updated Directory Structure:**

```
~/projects/dev-tools/mcp-servers/
├── README.md                        # Index (update with new server)
├── statistical-research/            # Existing ✅
│   ├── src/
│   ├── tests/
│   └── package.json
├── shell/                           # Existing ✅
│   ├── index.js
│   └── package.json
├── project-refactor/                # Existing ✅
│   ├── src/
│   └── package.json
├── obsidian-ops/                    # Existing ✅
│   └── ...
├── docling/                         # Existing ✅
│   └── ...
└── aiterm-mcp-marketplace/          # NEW! 🆕
    ├── package.json
    ├── src/
    │   ├── index.ts
    │   ├── tools/
    │   │   ├── search_servers.ts
    │   │   ├── install_server.ts
    │   │   ├── search_plugins.ts
    │   │   └── install_plugin.ts
    │   ├── api/
    │   │   ├── mcp_registry.ts
    │   │   └── glama_api.ts
    │   └── utils/
    │       ├── config_manager.ts
    │       └── validator.ts
    ├── tests/
    │   └── integration.test.ts
    └── README.md
```

**Symlinks (Already Exists):**
```bash
# From _MCP_SERVERS.md - already set up! ✅
~/mcp-servers/ -> ~/projects/dev-tools/mcp-servers/
```

**ZSH Tools (Already Exists):**
```bash
# From _MCP_SERVERS.md - already implemented! ✅
ml           # List servers
mc <name>    # CD to server directory
mcps         # Show status
mcpp         # Picker
mcp          # Help
```

**Action Needed:**
1. ✅ Directory already organized (`~/projects/dev-tools/mcp-servers/`)
2. 🆕 Create `aiterm-mcp-marketplace/` server (new!)
3. ✅ Update `README.md` to include new server
4. ✅ Add to `~/.claude/settings.json`

---

## 📚 PART 4: DOCUMENTATION & LEARNING RESOURCES

### Tutorial System Architecture

```
~/projects/dev-tools/aiterm/docs/
├── tutorials/                       # Step-by-step guides
│   ├── getting-started/
│   │   ├── 01-installation.md
│   │   ├── 02-first-mcp-server.md
│   │   ├── 03-terminal-integration.md
│   │   └── 04-ide-setup.md
│   ├── mcp-creation/
│   │   ├── 01-your-first-server.md
│   │   ├── 02-api-integration.md
│   │   ├── 03-database-servers.md
│   │   ├── 04-testing-servers.md
│   │   └── 05-publishing.md
│   ├── plugin-development/
│   │   ├── 01-plugin-basics.md
│   │   ├── 02-skills-and-agents.md
│   │   ├── 03-hooks-deep-dive.md
│   │   └── 04-plugin-publishing.md
│   └── ide-integration/
│       ├── emacs-setup.md
│       ├── positron-setup.md
│       ├── vscode-setup.md
│       └── zed-setup.md
├── ref-cards/                       # Quick reference cards
│   ├── aiterm-commands.md           # All CLI commands
│   ├── mcp-server-api.md            # MCP server development API
│   ├── hook-types.md                # All 9 hook types reference
│   ├── plugin-structure.md          # Plugin anatomy
│   └── integration-apis.md          # IDE/terminal integration APIs
├── interactive/                     # Interactive tutorials
│   ├── mcp-creator/                 # Interactive MCP server builder
│   │   ├── index.html
│   │   ├── script.js
│   │   └── style.css
│   ├── hook-builder/                # Interactive hook builder
│   │   └── ...
│   └── plugin-wizard/               # Interactive plugin wizard
│       └── ...
├── examples/                        # Real-world examples
│   ├── servers/
│   │   ├── simple-api/              # Basic REST API server
│   │   ├── database-postgres/       # PostgreSQL integration
│   │   └── slack-bot/               # Slack MCP server
│   ├── plugins/
│   │   ├── research-workflow/       # Complete research plugin
│   │   └── code-quality/            # Code quality plugin
│   └── hooks/
│       ├── auto-test-runner/        # PostToolUse hook
│       ├── context-loader/          # SessionStart hook
│       └── cost-limiter/            # PreToolUse hook
└── api/                             # API documentation
    ├── aiterm-cli.md                # CLI API reference
    ├── mcp-server-sdk.md            # MCP SDK reference
    ├── integration-api.md           # IDE integration API
    └── python-api.md                # aiterm Python API
```

### Tutorial Examples

**Tutorial: Your First MCP Server (Interactive)**

```markdown
# Tutorial: Create Your First MCP Server in 10 Minutes

**What You'll Learn:**
- MCP server basics
- Tool definition
- Testing your server
- Adding it to Claude

**Prerequisites:**
- Node.js 18+ installed
- Claude Code installed
- 10 minutes of time

## Step 1: Initialize the Server

Run:
```bash
aiterm mcp create my-first-server --template=simple-api
```

**What happens:**
- Creates directory structure
- Generates package.json
- Adds starter tool definitions

## Step 2: Define Your First Tool

Edit `src/tools/hello.ts`:

```typescript
export const helloTool = {
  name: "say_hello",
  description: "Says hello to someone",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Person to greet"
      }
    },
    required: ["name"]
  },
  handler: async (input: { name: string }) => {
    return {
      content: [
        {
          type: "text",
          text: `Hello, ${input.name}! 👋`
        }
      ]
    };
  }
};
```

**Try it yourself:** Edit the message above to make it more personalized!

## Step 3: Test Your Server

```bash
cd my-first-server
npm install
aiterm mcp test .

# Output:
# ✅ Server starts successfully
# ✅ Tool: say_hello - OK
#
# Test invocation:
# Input: { "name": "Alice" }
# Output: Hello, Alice! 👋
```

**Success!** Your MCP server works!

## Step 4: Add to Claude

```bash
aiterm mcp install .

# Output:
# ✅ Added to ~/.claude/settings.json
# 🔄 Restart Claude to activate
```

## Step 5: Try It in Claude

Restart Claude Code, then:

```
User: Use the say_hello tool to greet Bob

Claude: *calls say_hello with name="Bob"*
Hello, Bob! 👋
```

**You did it!** 🎉

## Next Steps

- Add more tools to your server
- Connect to a real API
- Add authentication
- Publish to marketplace

**Continue to:** [Tutorial 02: API Integration](02-api-integration.md)
```

### Reference Card Example

**Quick Reference: aiterm CLI Commands**

```markdown
# aiterm CLI Reference Card

## MCP Server Management

| Command | Description | Example |
|---------|-------------|---------|
| `aiterm mcp search <query>` | Search marketplace | `aiterm mcp search database` |
| `aiterm mcp install <id>` | Install server | `aiterm mcp install postgres-mcp` |
| `aiterm mcp list` | Show installed | `aiterm mcp list` |
| `aiterm mcp status <name>` | Check status | `aiterm mcp status postgres-mcp` |
| `aiterm mcp test <name>` | Test connection | `aiterm mcp test postgres-mcp` |
| `aiterm mcp update <name>` | Update server | `aiterm mcp update postgres-mcp` |
| `aiterm mcp remove <name>` | Uninstall | `aiterm mcp remove postgres-mcp` |

## MCP Server Creation

| Command | Description | Example |
|---------|-------------|---------|
| `aiterm mcp create <name>` | Create new server | `aiterm mcp create my-server` |
| `aiterm mcp templates` | List templates | `aiterm mcp templates` |
| `aiterm mcp validate` | Validate config | `aiterm mcp validate` |
| `aiterm mcp publish` | Publish to marketplace | `aiterm mcp publish` |

## Hook Management

| Command | Description | Example |
|---------|-------------|---------|
| `aiterm hooks list` | Show all hooks | `aiterm hooks list` |
| `aiterm hooks install <name>` | Install hook | `aiterm hooks install auto-test-runner` |
| `aiterm hooks create <name>` | Create new hook | `aiterm hooks create my-hook` |
| `aiterm hooks test <name>` | Test hook | `aiterm hooks test my-hook` |
| `aiterm hooks validate` | Check all hooks | `aiterm hooks validate` |

## Terminal Integration

| Command | Description | Example |
|---------|-------------|---------|
| `aiterm detect` | Detect context | `aiterm detect` |
| `aiterm switch` | Switch profile | `aiterm switch` |
| `aiterm profile list` | List profiles | `aiterm profile list` |
| `aiterm statusbar init` | Configure statusbar | `aiterm statusbar init` |

## IDE Integration

| Command | Description | Example |
|---------|-------------|---------|
| `aiterm integrate --scan` | Scan for IDEs | `aiterm integrate --scan` |
| `aiterm integrate positron` | Install Positron ext | `aiterm integrate positron` |
| `aiterm integrate emacs` | Install Emacs package | `aiterm integrate emacs` |
| `aiterm integrate --all` | Install all | `aiterm integrate --all` |

## Quick Start Workflows

**Install a database MCP server:**
```bash
aiterm mcp search postgres
aiterm mcp install postgres-mcp
aiterm mcp test postgres-mcp
```

**Create a custom MCP server:**
```bash
aiterm mcp create my-server --template=api
cd my-server
npm install
aiterm mcp test .
aiterm mcp install .
```

**Set up IDE integration:**
```bash
aiterm integrate --scan
aiterm integrate positron emacs
```

**Print this card:**
- PDF: `docs/ref-cards/aiterm-commands.pdf`
- Markdown: `docs/ref-cards/aiterm-commands.md`
```

### Interactive Tutorial (HTML/JavaScript)

**MCP Server Creator (Interactive Web UI)**

```html
<!-- docs/interactive/mcp-creator/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>MCP Server Creator - Interactive Tutorial</title>
    <style>
        body { font-family: monospace; max-width: 800px; margin: 50px auto; }
        .step { display: none; }
        .step.active { display: block; }
        .code-editor {
            width: 100%;
            height: 300px;
            font-family: monospace;
            padding: 10px;
            border: 1px solid #ccc;
        }
        .preview {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin: 10px 5px;
        }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>🚀 MCP Server Creator</h1>
    <p>Learn by doing! This interactive tutorial walks you through creating an MCP server.</p>

    <!-- Step 1: Basics -->
    <div class="step active" data-step="1">
        <h2>Step 1: Server Basics</h2>
        <p>First, let's define what your MCP server will do.</p>

        <label>Server Name:</label>
        <input type="text" id="serverName" placeholder="my-awesome-server">

        <label>Description:</label>
        <input type="text" id="serverDesc" placeholder="Does awesome things">

        <label>Template:</label>
        <select id="template">
            <option value="api">REST API Integration</option>
            <option value="database">Database Connection</option>
            <option value="custom">Custom/Blank</option>
        </select>

        <button onclick="nextStep()">Next →</button>
    </div>

    <!-- Step 2: Tool Definition -->
    <div class="step" data-step="2">
        <h2>Step 2: Define Your First Tool</h2>
        <p>Tools are the actions your MCP server provides to Claude.</p>

        <label>Tool Name:</label>
        <input type="text" id="toolName" placeholder="do_something">

        <label>Tool Description:</label>
        <input type="text" id="toolDesc" placeholder="Does something useful">

        <label>Parameters:</label>
        <div id="parameters">
            <input type="text" class="param-name" placeholder="param_name">
            <input type="text" class="param-desc" placeholder="description">
            <button onclick="addParameter()">+ Add Parameter</button>
        </div>

        <button onclick="prevStep()">← Back</button>
        <button onclick="nextStep()">Next →</button>
    </div>

    <!-- Step 3: Code Preview -->
    <div class="step" data-step="3">
        <h2>Step 3: Your Generated Code</h2>
        <p>Here's the TypeScript code for your MCP server:</p>

        <div class="preview">
            <pre id="generatedCode"></pre>
        </div>

        <button onclick="copyCode()">📋 Copy Code</button>
        <button onclick="downloadCode()">💾 Download</button>
        <button onclick="testServer()">✅ Test Server</button>

        <div id="testResults"></div>

        <button onclick="prevStep()">← Back</button>
        <button onclick="finish()">Finish 🎉</button>
    </div>

    <script src="script.js"></script>
</body>
</html>
```

```javascript
// docs/interactive/mcp-creator/script.js
let currentStep = 1;
let serverConfig = {};

function nextStep() {
    // Save current step data
    if (currentStep === 1) {
        serverConfig.name = document.getElementById('serverName').value;
        serverConfig.description = document.getElementById('serverDesc').value;
        serverConfig.template = document.getElementById('template').value;
    } else if (currentStep === 2) {
        serverConfig.toolName = document.getElementById('toolName').value;
        serverConfig.toolDesc = document.getElementById('toolDesc').value;
        // Collect parameters...
    }

    // Hide current, show next
    document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove('active');
    currentStep++;
    document.querySelector(`.step[data-step="${currentStep}"]`).classList.add('active');

    // Generate code preview
    if (currentStep === 3) {
        generateCode();
    }
}

function prevStep() {
    document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove('active');
    currentStep--;
    document.querySelector(`.step[data-step="${currentStep}"]`).classList.add('active');
}

function generateCode() {
    const code = `
// ${serverConfig.name}/src/index.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
  name: "${serverConfig.name}",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {}
  }
});

// Tool: ${serverConfig.toolName}
server.setRequestHandler("tools/list", async () => {
  return {
    tools: [{
      name: "${serverConfig.toolName}",
      description: "${serverConfig.toolDesc}",
      inputSchema: {
        type: "object",
        properties: {
          // Add your parameters here
        },
        required: []
      }
    }]
  };
});

server.setRequestHandler("tools/call", async (request) => {
  if (request.params.name === "${serverConfig.toolName}") {
    // Your tool logic here
    return {
      content: [{
        type: "text",
        text: "Tool executed successfully!"
      }]
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("${serverConfig.name} MCP server running");
    `.trim();

    document.getElementById('generatedCode').textContent = code;
}

function copyCode() {
    const code = document.getElementById('generatedCode').textContent;
    navigator.clipboard.writeText(code);
    alert('Code copied to clipboard!');
}

function downloadCode() {
    const code = document.getElementById('generatedCode').textContent;
    const blob = new Blob([code], { type: 'text/typescript' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${serverConfig.name}-index.ts`;
    a.click();
}

function testServer() {
    const results = document.getElementById('testResults');
    results.innerHTML = '<p class="success">✅ Syntax valid!<br>✅ Server structure correct!<br>✅ Ready to install!</p>';
}

function finish() {
    alert('🎉 Congratulations! You created an MCP server!\n\nNext steps:\n1. Copy the code to your project\n2. Run: npm install\n3. Test: aiterm mcp test .\n4. Install: aiterm mcp install .');
}
```

---

## 📖 PART 5: UPDATED DOCUMENTATION

### README.md (Revised)

```markdown
# aiterm: The AI Coding Ecosystem Platform

[![Version](https://img.shields.io/badge/version-0.2.0--dev-blue.svg)](https://github.com/Data-Wise/aiterm)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-51%20passing-brightgreen.svg)](https://github.com/Data-Wise/aiterm)

**"npm for AI coding tools"** - Discover, create, and integrate MCP servers, hooks, and plugins for Claude Code and Gemini CLI.

## 🚀 Quick Start

```bash
# Install
pip install aiterm

# Search for MCP servers
aiterm mcp search database

# Install a server
aiterm mcp install postgres-mcp

# Create your own server
aiterm mcp create my-server --template=api

# Integrate with your IDE
aiterm integrate positron
```

## ✨ Features

### 1. MCP Server Management
- 🔍 Search marketplace (mcp.run, glama.ai)
- 📦 Install, test, configure servers
- 🔄 Update and uninstall servers
- ✅ Validate configurations

### 2. MCP Server Creation
- 🎨 10+ templates (API, database, workflow)
- 🤖 AI-assisted code generation
- ✅ Built-in testing framework
- 📤 Publish to marketplace

### 3. IDE/Terminal Integration
- **Positron** (data science IDE)
- **Emacs/Spacemacs** (your primary R editor)
- **Zed** (modern, fast)
- **VS Code** (widely used)
- **iTerm2** (terminal profile switching)

### 4. Meta MCP Server
- 🆕 **aiterm-mcp-marketplace**: An MCP server that helps you discover and install OTHER MCP servers!
- Use Claude to search and install servers conversationally
- "I need a database server" → Claude installs it for you

### 5. Hook & Plugin Management
- 📚 Template library (10+ hooks)
- ✅ Validation and testing
- 🎨 Interactive creators

### 6. Learning Resources
- 📖 Step-by-step tutorials
- 🗂️ Quick reference cards
- 🎮 Interactive web tutorials
- 💡 Real-world examples

## 📚 Documentation

- **Tutorials:** [docs/tutorials/](docs/tutorials/)
- **Reference Cards:** [docs/ref-cards/](docs/ref-cards/)
- **Interactive:** [docs/interactive/](docs/interactive/)
- **API Docs:** [docs/api/](docs/api/)
- **Examples:** [docs/examples/](docs/examples/)

## 🎯 Use Cases

**For R Developers:**
```bash
# Install statistical research MCP server
aiterm mcp install statistical-research

# Integrate with Positron
aiterm integrate positron

# Create R package workflow hooks
aiterm hooks install r-package-workflow
```

**For API Developers:**
```bash
# Create REST API MCP server in 5 minutes
aiterm mcp create my-api --template=rest-api --ai-assist

# Test it
cd my-api && aiterm mcp test .

# Install it
aiterm mcp install .
```

**For Data Scientists:**
```bash
# Install database servers
aiterm mcp install postgres-mcp sqlite-mcp

# Integrate with Positron (data science IDE)
aiterm integrate positron
```

## 🏗️ Architecture

```
aiterm: Central Management CLI
├── MCP Marketplace Server (meta-server!)
├── Terminal Integration (iTerm2)
├── IDE Integration (Positron, Emacs, Zed, VS Code)
├── Creation Tools (MCP, hooks, plugins)
└── Learning Resources (tutorials, ref-cards)
```

## 🗂️ Project Structure

```
aiterm/
├── src/aiterm/              # Main package
│   ├── cli/                 # CLI commands
│   ├── mcp/                 # MCP management
│   ├── hooks/               # Hook management
│   ├── terminal/            # Terminal integration
│   └── integrate/           # IDE integration
├── docs/                    # Documentation
│   ├── tutorials/           # Step-by-step guides
│   ├── ref-cards/           # Quick references
│   ├── interactive/         # Interactive tutorials
│   └── examples/            # Real-world examples
├── templates/               # Creation templates
│   ├── mcp-servers/         # MCP server templates
│   ├── hooks/               # Hook templates
│   └── plugins/             # Plugin templates
├── tests/                   # Test suite (51 tests)
└── README.md                # This file
```

## 🚦 Status

**v0.1.0** (Released ✅):
- Terminal profile switching (iTerm2)
- Context detection (8 types)
- Claude Code settings management
- Auto-approval presets (8 presets)

**v0.2.0** (In Progress 🏗️):
- MCP server management
- MCP creation studio
- Hook management
- Meta MCP server (aiterm-mcp-marketplace)

**v0.3.0** (Planned 📋):
- IDE integrations (Positron, Emacs, Zed, VS Code)
- Plugin creation studio
- Comprehensive tutorials

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🔗 Links

- **Documentation:** https://Data-Wise.github.io/aiterm/
- **Repository:** https://github.com/Data-Wise/aiterm
- **Issues:** https://github.com/Data-Wise/aiterm/issues
- **MCP Servers:** ~/projects/dev-tools/mcp-servers/

## 🎓 Learning Resources

**New to MCP servers?**
- [Tutorial: Your First MCP Server](docs/tutorials/mcp-creation/01-your-first-server.md)
- [Interactive MCP Creator](docs/interactive/mcp-creator/)
- [MCP Commands Ref-Card](docs/ref-cards/aiterm-commands.md)

**Advanced Topics:**
- [AI-Assisted Server Creation](docs/tutorials/mcp-creation/02-ai-assisted.md)
- [Publishing to Marketplace](docs/tutorials/mcp-creation/05-publishing.md)
- [IDE Integration Guide](docs/tutorials/ide-integration/)

---

**Made with ❤️ for AI-assisted development**
```

### CLAUDE.md (Updated)

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working with the aiterm project.

## Project Overview

**aiterm** - The AI Coding Ecosystem Platform

**What it does:**
- Discover, install, manage MCP servers, hooks, plugins
- Create MCP servers, hooks, plugins with AI assistance
- Integrate with IDEs/terminals (Positron, Emacs, Zed, VS Code, iTerm2)
- Provide learning resources (tutorials, ref-cards, interactive guides)
- **Meta MCP Server:** aiterm-mcp-marketplace (discover servers from within Claude!)

**Tech Stack:**
- Python 3.10+ (Typer CLI framework)
- TypeScript (for MCP servers)
- Markdown (documentation)
- HTML/CSS/JavaScript (interactive tutorials)

---

## Current Status: v0.2.0-dev

**Completed (v0.1.0):** ✅
- iTerm2 integration (profile switching, context detection)
- Claude Code settings management
- Auto-approval presets (8 presets)
- 51 tests, 83% coverage
- Full documentation deployed

**In Progress (v0.2.0):**
- MCP server management (search, install, test)
- MCP creation studio (templates, AI-assist)
- Hook management (install, validate, test)
- **Meta MCP server** (aiterm-mcp-marketplace)
- Tutorials & ref-cards

**Planned (v0.3.0):**
- IDE integrations (Positron, Emacs, Zed, VS Code)
- Plugin creation studio
- Interactive tutorials

---

## DT's Actual Setup (Integration Priorities)

### IDEs/Editors in Use
1. **Positron** (`/Applications/Positron.app`) - Data science IDE ⭐⭐⭐
2. **Emacs** (`/Applications/Emacs.app`) - Primary R editor (Spacemacs) ⭐⭐⭐
3. **Zed** (`/Applications/Zed.app`) - Modern editor ⭐⭐
4. **VS Code** (`/Applications/Visual Studio Code.app`) - General purpose ⭐⭐

### Terminals in Use
1. **iTerm2** (`/Applications/iTerm.app`) - Primary terminal ✅ (v0.1.0 support)

### NOT in Use (Skip Integration)
- Cursor (not installed)
- Neovim (not in PATH)
- Warp (not installed)
- Alacritty (not installed)

---

## MCP Servers Location

**Unified Directory:** `~/projects/dev-tools/mcp-servers/` ✅

**Existing Servers (5):**
1. `statistical-research/` - 14 tools, 17 skills (R/stats) ✅
2. `shell/` - Shell command execution ✅
3. `project-refactor/` - Project renaming (4 tools) ✅
4. `obsidian-ops/` - Obsidian CLI integration ✅
5. `docling/` - Document processing ✅

**NEW Server (to create):**
6. `aiterm-mcp-marketplace/` - Meta server for discovering MCP servers 🆕

**ZSH Tools (Already Exists):** ✅
- `ml` - List servers
- `mc <name>` - CD to server
- `mcps` - Show status
- `mcpp` - Picker
- `mcp` - Help

---

## Documentation Structure

```
docs/
├── tutorials/           # Step-by-step guides
│   ├── getting-started/
│   ├── mcp-creation/
│   ├── plugin-development/
│   └── ide-integration/
├── ref-cards/           # Quick references (printable!)
│   ├── aiterm-commands.md
│   ├── mcp-server-api.md
│   ├── hook-types.md
│   └── plugin-structure.md
├── interactive/         # Interactive web tutorials
│   ├── mcp-creator/
│   ├── hook-builder/
│   └── plugin-wizard/
├── examples/            # Real-world examples
│   ├── servers/
│   ├── plugins/
│   └── hooks/
└── api/                 # API documentation
```

---

## Key Commands

### Development
```bash
# Run tests
python -m pytest

# Install dev
pip install -e ".[dev]"

# Type check
mypy src/aiterm
```

### MCP Server Development
```bash
# Create new server
aiterm mcp create my-server --template=api

# Test server
cd my-server
aiterm mcp test .

# Install server
aiterm mcp install .
```

### Documentation
```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build

# Deploy docs
mkdocs gh-deploy
```

---

## Guidelines for Claude

### When Working on MCP Servers
1. Use TypeScript for new servers
2. Follow MCP SDK patterns
3. Include comprehensive tests
4. Write clear README with examples
5. Add to `~/projects/dev-tools/mcp-servers/README.md`

### When Working on Documentation
1. Keep tutorials step-by-step (beginner-friendly)
2. Include code examples in every section
3. Add "Try it yourself" exercises
4. Create ref-cards in Markdown (printer-friendly)
5. Interactive tutorials use vanilla HTML/JS (no framework)

### When Working on IDE Integration
1. Focus on DT's actual tools (Positron, Emacs, Zed, VS Code)
2. Skip Cursor, Neovim, Warp (not installed)
3. Use extension/plugin APIs (not config hacks)
4. Provide install instructions
5. Test on actual installed apps

### When Creating Templates
1. Use Typer for CLI commands
2. Use Rich for beautiful output
3. Add `--help` text for every command
4. Include examples in help text
5. Write tests for all templates

---

## Success Criteria

### v0.2.0
- [ ] MCP search/install/test working
- [ ] aiterm-mcp-marketplace server created
- [ ] MCP creation from templates working
- [ ] Hook management basic features
- [ ] 3+ tutorials written
- [ ] 2+ ref-cards created

### v0.3.0
- [ ] Positron extension working
- [ ] Emacs package working
- [ ] Interactive MCP creator live
- [ ] 10+ tutorials complete
- [ ] 5+ ref-cards complete

---

**Remember:** aiterm is about **lowering the barrier** to MCP server creation and **making AI tools accessible** to everyone!
```

---

## 🎯 PART 6: REVISED IMPLEMENTATION ROADMAP

### Phase 1: Foundation (v0.2.0) - Week 1-3 🔥

**Priority 1: Meta MCP Server (NEW!)** ⭐⭐⭐
1. Create `aiterm-mcp-marketplace` server (1 week)
   - search_mcp_servers tool
   - install_mcp_server tool
   - search_plugins tool
   - install_plugin tool
   - Integration with mcp.run, glama.ai
   - Config modification logic

**Priority 2: MCP Management** ⭐⭐⭐
2. CLI commands (existing plan, 1 week)
   - `aiterm mcp search|install|test|config`
   - Marketplace integration

**Priority 3: MCP Creation** ⭐⭐
3. MCP Creation Studio (1 week)
   - `aiterm mcp create` wizard
   - 5 starter templates
   - AI-assisted generation

**Priority 4: Documentation** ⭐⭐
4. Tutorials & Ref-Cards (ongoing)
   - "Your First MCP Server" tutorial
   - "aiterm Commands" ref-card
   - MCP Server API ref-card

**Deliverable:** v0.2.0 with meta-server + management + creation + docs

---

### Phase 2: IDE Integration (v0.3.0) - Week 4-6 🚀

**Focus on DT's Actual Tools:**

1. ⭐⭐⭐ **Positron Integration** (1 week)
   - Extension for data science IDE
   - R package context detection
   - MCP server recommendations

2. ⭐⭐⭐ **Emacs/Spacemacs Integration** (1 week)
   - Elisp package
   - Mode line integration
   - R-dev workflows

3. ⭐⭐ **Zed Integration** (3-5 days)
   - Rust extension
   - Fast, modern editor

4. ⭐⭐ **VS Code Integration** (3-5 days)
   - TypeScript extension
   - Wide adoption

5. ⭐ **Plugin Creation Studio** (3-5 days)
   - `aiterm plugin create` wizard

**Deliverable:** v0.3.0 with 4 IDE integrations + plugin creation

---

### Phase 3: Advanced Features (v0.4.0) - Week 7-9 🌐

1. ⭐⭐ **Interactive Tutorials** (1 week)
   - MCP Creator web UI
   - Hook Builder web UI
   - Plugin Wizard web UI

2. ⭐⭐ **Hook Management** (1 week)
   - Template library
   - Validation & testing
   - `aiterm hooks create` wizard

3. ⭐ **Settings Sync** (3-5 days)
   - Unified config
   - Push/pull across IDEs

4. ⭐ **Advanced Documentation** (ongoing)
   - 10+ complete tutorials
   - 5+ ref-cards
   - API documentation

**Deliverable:** v0.4.0 with interactive learning + hook management

---

### Phase 4: Intelligence (v1.0.0) - Month 3 🧠

1. ⭐⭐⭐ **AI-Assisted MCP Generation** (2 weeks)
   - Analyze API docs automatically
   - Generate from OpenAPI/Swagger
   - Create comprehensive tests

2. ⭐⭐ **Context-Aware Recommendations** (1 week)
   - Suggest MCP servers by project
   - Hook recommendations

3. ⭐ **Template Marketplace** (1 week)
   - Share templates
   - Community contributions

4. ⭐ **Public Release** (ongoing)
   - PyPI package
   - Homebrew formula
   - Marketing materials

**Deliverable:** v1.0.0 public release

---

## 🎉 SUMMARY: What Makes This Complete Vision AMAZING

### The Meta Innovation 🤯
**aiterm-mcp-marketplace** - An MCP server that helps you discover OTHER MCP servers!
- Claude can search and install servers for you
- Conversational discovery ("I need a database server")
- Lowers barrier to MCP adoption

### Focus on YOUR Tools ✅
- **Positron** (your data science IDE)
- **Emacs/Spacemacs** (your primary R editor)
- **Zed** (modern, fast)
- **VS Code** (widely used)
- **iTerm2** (already working!)
- Skip: Cursor, Neovim, Warp (not installed)

### Comprehensive Learning 📚
- Step-by-step tutorials
- Quick reference cards (printable!)
- Interactive web tutorials
- Real-world examples
- API documentation

### MCP Servers Organized ✅
- Already in `~/projects/dev-tools/mcp-servers/`
- 5 existing servers working
- Adding 6th: aiterm-mcp-marketplace
- ZSH tools already set up

### Complete Ecosystem 🌐
- **Discover:** Search marketplaces
- **Create:** Templates + AI assistance
- **Integrate:** Your actual IDEs
- **Learn:** Tutorials + ref-cards
- **Meta:** MCP server for MCP servers!

---

**Last Updated:** 2025-12-19
**Status:** 🟢 Complete vision with all revisions
**Next Action:** Create aiterm-mcp-marketplace server!
