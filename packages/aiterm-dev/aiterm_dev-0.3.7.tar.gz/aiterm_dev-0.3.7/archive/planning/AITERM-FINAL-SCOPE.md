# aiterm: Final Scope (Revised Based on Actual Setup)

**Generated:** 2025-12-19
**Status:** 🟢 Final scope based on DT's actual Claude Code setup

---

## 🎯 CRITICAL FINDINGS FROM ~/.claude/

### Existing Claude Code Features (Already Built-in!)

**MCP Management** ✅ **Already exists in Claude Code CLI:**
```bash
claude mcp list                    # List MCP servers
claude mcp add <name> <command>    # Add MCP server
claude mcp remove <name>           # Remove MCP server
claude mcp get <name>              # Get server details
```

**Plugin Management** ✅ **Already exists in Claude Code CLI:**
```bash
claude plugin install <plugin>     # Install plugin
claude plugin uninstall <plugin>   # Uninstall plugin
claude plugin enable <plugin>      # Enable plugin
claude plugin disable <plugin>     # Disable plugin
claude plugin update <plugin>      # Update plugin
```

**What This Means:**
- ❌ **Don't duplicate** `claude mcp` and `claude plugin` commands
- ✅ **Do extend** with features Claude doesn't have
- ✅ **Do integrate** with existing Claude commands

---

## 🔍 YOUR ACTUAL CLAUDE SETUP

### Installed MCP Servers (3)
1. **statistical-research** (Bun) ✅
   - Path: `/Users/dt/projects/dev-tools/mcp-servers/statistical-research/`
   - Runtime: Bun
   - Tools: 14 tools (R execution, Zotero, literature)

2. **project-refactor** (Node) ✅
   - Path: `/Users/dt/projects/dev-tools/mcp-servers/project-refactor/`
   - Runtime: Node.js
   - Tools: 4 tools (project renaming)

3. **docling** (Python/uv) ✅
   - Path: `/Users/dt/projects/dev-tools/mcp-servers/docling/`
   - Runtime: uv (Python)
   - Tools: Document processing

### Installed Plugins (12)
**From claude-plugins-official:**
1. commit-commands
2. pr-review-toolkit
3. feature-dev
4. explanatory-output-style ✅ (you're using this now!)
5. learning-output-style ✅ (you're using this now!)
6. plugin-dev
7. code-review
8. frontend-design
9. ralph-wiggum
10. github

**From cc-marketplace:**
11. infrastructure-maintainer
12. codebase-documenter

### Existing Hooks (1)
1. **UserPromptSubmit:** `prompt-optimizer.sh` ✅
   - Path: `~/.claude/hooks/prompt-optimizer.sh`
   - Status: Active
   - Features: @smart prompt enhancement

### Existing Commands (194 files!)
**Command Hubs:**
- `/code` → symlink to zsh-claude-workflow ✅
- `/math` → symlink to zsh-claude-workflow ✅
- `/research` → symlink to zsh-claude-workflow ✅
- `/teach` → symlink to zsh-claude-workflow ✅
- `/write` → symlink to zsh-claude-workflow ✅
- `/git/*` → Multiple git workflow commands ✅
- `/github/*` → GitHub integration commands ✅
- `/help/*` → Help system ✅
- `/site/*` → Documentation site commands ✅
- `/workflow/*` → ADHD workflow commands ✅

**INSIGHT:** You already have a MASSIVE command library! (194 command files)

### StatusLine
- **Active:** `statusline-p10k.sh` ✅
- Path: `~/.claude/statusline-p10k.sh`
- Update interval: 300ms (built-in)

---

## 🚫 WHAT TO SKIP (Already Done Elsewhere)

### 1. MCP Management - Built into Claude Code CLI ✅
**Skip:**
- `aiterm mcp list` (use `claude mcp list`)
- `aiterm mcp add` (use `claude mcp add`)
- `aiterm mcp remove` (use `claude mcp remove`)

**Keep (Unique Features):**
- `aiterm mcp create` - MCP server creation wizard 🆕
- `aiterm mcp templates` - Template library 🆕
- `aiterm mcp validate` - Deep validation 🆕
- `aiterm mcp test` - Connection testing 🆕

### 2. Plugin Management - Built into Claude Code CLI ✅
**Skip:**
- `aiterm plugin install` (use `claude plugin install`)
- `aiterm plugin update` (use `claude plugin update`)

**Keep (Unique Features):**
- `aiterm plugin create` - Plugin creation wizard 🆕
- `aiterm plugin templates` - Template library 🆕
- `aiterm plugin validate` - Deep validation 🆕

### 3. Hook Management - Partially Done ✅
**Already Have:**
- `prompt-optimizer.sh` (UserPromptSubmit hook)

**Add (Unique Features):**
- `aiterm hook create` - Hook creation wizard 🆕
- `aiterm hook templates` - Template library (9 hook types) 🆕
- `aiterm hook test` - Dry-run testing 🆕
- `aiterm hook validate` - Syntax checking 🆕

### 4. IDE Integrations - Done in Other Projects ✅
**Skip (per your request):**
- ❌ Emacs integration (already done elsewhere)
- ❌ Cursor integration (already done elsewhere)
- ❌ Warp integration (already done elsewhere)

**Keep (Not duplicated):**
- ✅ Positron integration (unique to aiterm)
- ✅ Zed integration (unique to aiterm)
- ✅ VS Code integration (unique to aiterm)

---

## ✅ REVISED AITERM SCOPE (What aiterm SHOULD Do)

### 1. MCP Server Creation Studio ⭐⭐⭐

**The #1 Priority - No Overlap!**

```bash
# Create new MCP server from templates
aiterm mcp create my-server
# → Interactive wizard
# → 10+ templates (API, database, workflow)
# → AI-assisted code generation
# → Generated code ready to use

# Test your server locally
aiterm mcp test my-server
# → Validates server structure
# → Tests each tool
# → Shows latency metrics

# Validate server configuration
aiterm mcp validate my-server
# → Checks package.json
# → Validates tool schemas
# → Tests with fixtures

# List available templates
aiterm mcp templates
# → Shows 10+ templates
# → REST API, GraphQL, Database, etc.
```

**Why This Matters:**
- Claude CLI can ADD servers, but not CREATE them
- This is the missing piece!
- Lowers barrier to MCP development

### 2. Plugin/Hook/Agent Creation Studios ⭐⭐

**Creation > Management**

```bash
# Create plugin from templates
aiterm plugin create my-plugin
# → Interactive wizard
# → Generates skills, agents, hooks
# → Complete plugin structure

# Create hook from templates
aiterm hook create my-hook --type=SessionStart
# → Template selection (9 hook types)
# → Best-practice scaffolding
# → Validation included

# Create agent configuration
aiterm agent create my-agent
# → Interactive configuration
# → Tool selection
# → System prompt builder
```

**Why This Matters:**
- No creation tools exist in Claude CLI
- aiterm fills the gap!

### 3. Terminal Integration (Existing v0.1.0) ✅

**Keep All Existing Features:**

```bash
# Context detection (8 types)
aiterm detect

# Profile switching
aiterm switch

# Claude settings management
aiterm claude settings
aiterm claude backup
aiterm claude approvals list
aiterm claude approvals add <preset>
```

**Why This Matters:**
- No overlap with Claude CLI
- Terminal integration is unique to aiterm

### 4. Meta MCP Server: aiterm-mcp-marketplace ⭐⭐⭐

**The Killer Feature!**

An MCP server that helps Claude discover and install OTHER MCP servers!

```typescript
// Tools provided:
- search_mcp_servers    // Search mcp.run, glama.ai
- get_server_info       // Get detailed info
- install_mcp_server    // Call `claude mcp add` for you
- list_installed        // Call `claude mcp list`
- search_plugins        // Search for plugins
- install_plugin        // Call `claude plugin install`
```

**Usage:**
```
User (in Claude): "I need a database server"

Claude (using aiterm-marketplace):
🔍 Searching...
Found 5 servers:
1. postgres-mcp (⭐⭐⭐⭐⭐ 4.9/5)
2. sqlite-mcp (⭐⭐⭐⭐⭐ 4.8/5)

Which should I install?

User: "Install postgres-mcp"

Claude: *calls install_mcp_server tool*
*tool executes: `claude mcp add postgres-mcp ...`*
✅ Installed!
```

**Why This Matters:**
- Makes MCP discovery conversational
- Bridges gap between marketplace and CLI
- No one else has this!

### 5. Learning Resources ⭐⭐

**Tutorials, Ref-Cards, Interactive Guides**

```
docs/
├── tutorials/           # Step-by-step guides
│   ├── mcp-creation/    # Create your first server
│   ├── hook-development/# Build custom hooks
│   └── plugin-building/ # Complete plugin workflow
├── ref-cards/           # Quick references (printable!)
│   ├── mcp-server-api.md
│   ├── hook-types.md
│   └── aiterm-commands.md
├── interactive/         # Web-based tutorials
│   ├── mcp-creator/     # Interactive server builder
│   ├── hook-builder/    # Interactive hook builder
│   └── plugin-wizard/   # Interactive plugin wizard
└── examples/            # Real-world examples
    ├── servers/         # Example MCP servers
    ├── plugins/         # Example plugins
    └── hooks/           # Example hooks
```

**Why This Matters:**
- Claude CLI has NO learning resources
- Lowers barrier to entry
- Community building

---

## 📋 REVISED FEATURE LIST

### aiterm Commands (No Duplication!)

**MCP Creation (Unique to aiterm):**
```bash
aiterm mcp create <name>           # Create new server
aiterm mcp templates               # List templates
aiterm mcp test <path>             # Test server
aiterm mcp validate <path>         # Validate server
aiterm mcp publish <path>          # Publish to marketplace
```

**Plugin Creation (Unique to aiterm):**
```bash
aiterm plugin create <name>        # Create plugin
aiterm plugin templates            # List templates
aiterm plugin validate <path>      # Validate plugin
```

**Hook Creation (Unique to aiterm):**
```bash
aiterm hook create <name>          # Create hook
aiterm hook templates              # List hook types
aiterm hook test <path>            # Dry-run test
aiterm hook validate <path>        # Check syntax
```

**Agent Creation (Unique to aiterm):**
```bash
aiterm agent create <name>         # Create agent
aiterm agent templates             # List templates
aiterm agent test <path>           # Test agent
```

**Terminal Integration (Existing v0.1.0):**
```bash
aiterm detect                      # Detect context
aiterm switch                      # Switch profile
aiterm profile list                # List profiles
aiterm statusbar init              # Configure statusbar
```

**Claude Settings (Existing v0.1.0):**
```bash
aiterm claude settings             # View settings
aiterm claude backup               # Backup settings
aiterm claude approvals list       # List approvals
aiterm claude approvals add <preset>  # Add preset
```

**Documentation:**
```bash
aiterm docs                        # Open docs
aiterm tutorial <name>             # Start tutorial
aiterm examples                    # Show examples
```

---

## 🎯 REVISED INTEGRATION PRIORITIES

### Keep (Not Duplicated)

**1. Positron** ⭐⭐⭐
- Data science IDE
- R package development
- Unique integration

**2. Zed** ⭐⭐
- Modern, fast editor
- Rust-based
- Unique integration

**3. VS Code** ⭐⭐
- Widely used
- Good ecosystem
- Unique integration

### Skip (Already Done Elsewhere)

**Per Your Request:**
- ❌ Emacs (done in another project)
- ❌ Cursor (done in another project)
- ❌ Warp (done in another project)
- ❌ Neovim (not installed anyway)

---

## 🗂️ MCP SERVERS (Already Organized! ✅)

**Location:** `~/projects/dev-tools/mcp-servers/` ✅

**Existing (3 in settings.json):**
1. statistical-research/ ✅
2. project-refactor/ ✅
3. docling/ ✅

**Additional (in directory but not in settings.json):**
4. shell/
5. obsidian-ops/

**NEW (To Create):**
6. aiterm-mcp-marketplace/ 🆕

**Note:** Already have ZSH tools (`ml`, `mc`, `mcps`, etc.) ✅

---

## 📚 COMMAND LIBRARY (Already Massive! ✅)

**Existing:** 194 command files in `~/.claude/commands/` ✅

**Command Hubs (Symlinked to zsh-claude-workflow):**
- /code → Code development commands ✅
- /math → Mathematical tools ✅
- /research → Research workflows ✅
- /teach → Teaching tools ✅
- /write → Writing assistance ✅

**Additional Hubs:**
- /git/* → Git workflows ✅
- /github/* → GitHub integration ✅
- /help/* → Help system ✅
- /site/* → Documentation commands ✅
- /workflow/* → ADHD workflows ✅

**Action:** Don't duplicate - leverage existing commands!

---

## 🚀 FINAL IMPLEMENTATION ROADMAP

### Phase 1: Creation Tools (v0.2.0) - Week 1-3 🔥

**Priority 1: MCP Server Creation** ⭐⭐⭐
1. `aiterm mcp create` wizard (1 week)
   - Interactive prompts
   - 10+ templates
   - Code generation
2. `aiterm mcp test` (2-3 days)
   - Local testing
   - Connection validation
3. `aiterm mcp templates` (2-3 days)
   - Template library
   - Documentation

**Priority 2: Meta MCP Server** ⭐⭐⭐
4. Create `aiterm-mcp-marketplace` (1 week)
   - 8 tools (search, install, get info, etc.)
   - Integration with mcp.run, glama.ai
   - Calls `claude mcp add` under the hood

**Priority 3: Documentation** ⭐⭐
5. Tutorials (ongoing)
   - "Your First MCP Server" tutorial
   - MCP Server API ref-card
   - Interactive MCP creator

**Deliverable:** v0.2.0 with MCP creation + meta server

---

### Phase 2: More Creation Tools (v0.3.0) - Week 4-6 🚀

**Plugin/Hook/Agent Creation:**
1. `aiterm plugin create` wizard (1 week)
2. `aiterm hook create` wizard (3-5 days)
3. `aiterm agent create` wizard (2-3 days)
4. Complete documentation (ongoing)

**Deliverable:** v0.3.0 with full creation suite

---

### Phase 3: IDE Integration (v0.4.0) - Week 7-9 🌐

**Focus on Non-Duplicated IDEs:**
1. Positron extension (1 week)
2. Zed extension (3-5 days)
3. VS Code extension (3-5 days)
4. Integration documentation (ongoing)

**Deliverable:** v0.4.0 with IDE integrations

---

### Phase 4: Polish & Release (v1.0.0) - Month 3 🌟

**Public Release:**
1. AI-assisted code generation (2 weeks)
2. Template marketplace (1 week)
3. PyPI package (1 week)
4. Marketing & documentation (ongoing)

**Deliverable:** v1.0.0 public release

---

## 🎉 KEY INSIGHTS

### What Makes aiterm Unique

**1. Creation Focus** ✅
- Claude CLI manages servers, aiterm CREATES them
- No overlap, pure value-add

**2. Meta MCP Server** ✅
- Conversational server discovery
- Bridges marketplace ↔ CLI
- Unique innovation

**3. Learning Resources** ✅
- Tutorials, ref-cards, interactive guides
- Lowers barrier to entry
- Community building

**4. Terminal Integration** ✅
- No overlap with Claude CLI
- Unique aiterm feature

### What NOT to Duplicate

**1. MCP Management** ❌
- `claude mcp list|add|remove` already exist
- Use Claude CLI, don't reimplement

**2. Plugin Management** ❌
- `claude plugin install|update|enable` already exist
- Use Claude CLI, don't reimplement

**3. IDE Integrations** ❌
- Emacs, Cursor, Warp done in other projects
- Skip to avoid duplication

### The Value Proposition

**Before aiterm:**
- Creating MCP servers: Hours of boilerplate
- Finding servers: Manual marketplace browsing
- Learning: No resources

**After aiterm:**
- Creating MCP servers: 5-10 minutes with wizard
- Finding servers: Ask Claude conversationally
- Learning: Tutorials + interactive guides

---

## 📝 UPDATED README TAGLINE

**OLD:**
> "Terminal Optimizer for AI-Assisted Development"

**NEW:**
> "The MCP Creation Platform for Claude Code"

**Even Better:**
> "Create MCP servers in minutes, not hours"

**Or:**
> "From zero to MCP server in 10 minutes"

---

## 🎯 SUCCESS CRITERIA (Revised)

### v0.2.0 (Week 3)
- [ ] `aiterm mcp create` creates working servers from templates
- [ ] `aiterm mcp test` validates server functionality
- [ ] `aiterm-mcp-marketplace` MCP server working
- [ ] Can discover and install servers from Claude conversationally
- [ ] 2+ tutorials published
- [ ] 2+ ref-cards created

### v0.3.0 (Week 6)
- [ ] Plugin/hook/agent creation wizards working
- [ ] Template libraries complete (10+ MCP templates, 9 hook templates)
- [ ] 5+ tutorials published
- [ ] 3+ ref-cards created

### v0.4.0 (Week 9)
- [ ] Positron extension working
- [ ] Zed extension working
- [ ] VS Code extension working
- [ ] 10+ tutorials complete
- [ ] 5+ ref-cards complete

### v1.0.0 (Month 3)
- [ ] AI-assisted MCP generation working
- [ ] 100+ external users
- [ ] PyPI package published
- [ ] Community marketplace launched

---

**Last Updated:** 2025-12-19
**Status:** 🟢 Final scope - no duplication with Claude CLI or other projects
**Next Action:** Create `aiterm mcp create` wizard + `aiterm-mcp-marketplace` server
