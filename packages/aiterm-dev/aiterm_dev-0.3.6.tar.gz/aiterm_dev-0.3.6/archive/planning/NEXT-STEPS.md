# Next Steps: aiterm v0.3.0 Planning

**Updated:** 2025-12-26
**Current Status:** v0.2.1 released to PyPI & Homebrew

---

## ✅ COMPLETED (v0.2.0-v0.2.1)

- [x] **v0.2.0:** Hook management, command library, MCP integration, docs helpers
- [x] **v0.2.1:** PyPI publishing (`pip install aiterm-dev`), Homebrew fix, 9 REFCARDs
- [x] **Distribution:** Available via Homebrew, PyPI, uv, pipx
- [x] **Documentation:** 27+ pages deployed to GitHub Pages
- [x] **Trusted Publishing:** GitHub Actions OIDC configured

---

## 📋 NEXT ACTIONS (v0.3.0)

### 1. Commit All Brainstorm Documents ✅

```bash
cd ~/projects/dev-tools/aiterm

# Add all new brainstorm files
git add \
  BRAINSTORM-PROJECT-SCOPE.md \
  INTEGRATION-BRAINSTORM.md \
  AITERM-VISION-BRAINSTORM.md \
  AITERM-CREATOR-ECOSYSTEM.md \
  AITERM-COMPLETE-VISION.md \
  NEXT-STEPS.md

# Commit
git commit -m "docs: comprehensive vision brainstorm for aiterm v0.2+

- Complete scope analysis and overlap resolution
- Integration plans for zsh-claude → zsh-config
- Focused vision: 'npm for AI coding tools'
- Creation tools for MCP servers, plugins, agents, hooks
- IDE/terminal integration strategy (Positron, Emacs, Zed, VS Code)
- Meta MCP server (aiterm-mcp-marketplace)
- Learning resources (tutorials, ref-cards, interactive guides)
- Revised priorities based on DT's actual tool usage

Key decisions:
- Keep aiterm focused on AI tool management (no ADHD workflows)
- Integrate zsh-claude into zsh-configuration (full merge)
- Build meta MCP server for discovering/installing servers
- Focus integrations on Positron, Emacs, Zed, VS Code (skip Cursor, Neovim, Warp)
- Comprehensive documentation with tutorials and ref-cards

See AITERM-COMPLETE-VISION.md for full details."

# Push
git push origin dev
```

### 2. Create aiterm-mcp-marketplace Server 🆕

**Priority:** 🔥🔥🔥 HIGHEST (meta-tool, unique innovation)

**Location:** `~/projects/dev-tools/mcp-servers/aiterm-mcp-marketplace/`

**Timeline:** 1-2 weeks

**Steps:**
```bash
# 1. Create directory
cd ~/projects/dev-tools/mcp-servers
mkdir aiterm-mcp-marketplace
cd aiterm-mcp-marketplace

# 2. Initialize project
npm init -y
npm install @modelcontextprotocol/sdk typescript @types/node

# 3. Create structure
mkdir -p src/{tools,api,utils} tests

# 4. Implement tools (8 tools)
# - search_mcp_servers
# - get_server_info
# - install_mcp_server
# - list_installed_servers
# - update_mcp_server
# - uninstall_mcp_server
# - search_claude_plugins
# - install_claude_plugin

# 5. Implement API clients
# - mcp_registry.ts (mcp.run)
# - glama_api.ts (glama.ai)
# - github_api.ts (GitHub search)

# 6. Implement utilities
# - config_manager.ts (modify ~/.claude/settings.json)
# - validator.ts (validate server configs)
# - installer.ts (handle installation)

# 7. Write tests
# - Unit tests for each tool
# - Integration tests
# - API mock tests

# 8. Documentation
# - README.md with examples
# - API documentation
# - Usage guide

# 9. Install to Claude
# Add to ~/.claude/settings.json:
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

### 3. Update MCP Servers Documentation

**Files to Update:**
- `~/projects/dev-tools/mcp-servers/README.md` - Add aiterm-mcp-marketplace
- `~/projects/dev-tools/_MCP_SERVERS.md` - Add new server to index

### 4. Begin Phase 1 Implementation (v0.2.0)

**Start with Quick Wins:**

**Week 1:**
1. ✅ Commit brainstorm documents (done!)
2. 🆕 Create aiterm-mcp-marketplace server (1 week)
3. 📚 Write "Your First MCP Server" tutorial (2-3 days)
4. 📄 Create "aiterm Commands" ref-card (1-2 days)

**Week 2:**
1. Implement `aiterm mcp search` command (2-3 days)
2. Implement `aiterm mcp install` command (2-3 days)
3. Implement `aiterm mcp test` command (2-3 days)

**Week 3:**
1. Implement `aiterm mcp create` wizard (3-5 days)
2. Create 5 MCP server templates (2-3 days)
3. Write MCP creation tutorials (2-3 days)

---

## 📚 DOCUMENTATION PRIORITIES

### Immediate (Week 1-2)

1. **Tutorial: Your First MCP Server**
   ```markdown
   docs/tutorials/mcp-creation/01-your-first-server.md
   - Step-by-step guide (10 minutes)
   - Code examples
   - Testing instructions
   - Installation guide
   ```

2. **Ref-Card: aiterm Commands**
   ```markdown
   docs/ref-cards/aiterm-commands.md
   - All CLI commands in tables
   - Quick reference format
   - Printable (PDF export)
   - Examples for each command
   ```

3. **Ref-Card: MCP Server API**
   ```markdown
   docs/ref-cards/mcp-server-api.md
   - Tool definition schema
   - Input/output formats
   - Best practices
   - Common patterns
   ```

### Short-term (Week 3-4)

4. **Tutorial: API Integration**
   ```markdown
   docs/tutorials/mcp-creation/02-api-integration.md
   - REST API server example
   - Authentication handling
   - Error handling
   - Testing strategies
   ```

5. **Interactive Tutorial: MCP Creator**
   ```html
   docs/interactive/mcp-creator/index.html
   - Web-based MCP server builder
   - Live code preview
   - Download generated code
   - Test server online
   ```

6. **Examples: Real-World Servers**
   ```
   docs/examples/servers/
   - simple-api/ (basic REST API)
   - database-postgres/ (PostgreSQL integration)
   - slack-bot/ (Slack MCP server)
   ```

---

## 🎯 INTEGRATION PRIORITIES (Based on DT's Tools)

### Phase 1 (v0.3.0) - Your Daily Drivers

**1. Positron Integration** ⭐⭐⭐
- **Why:** Data science IDE, perfect for R packages
- **Effort:** 1 week
- **Features:**
  - Extension for Positron
  - R package context detection
  - Auto-activate statistical-research MCP server
  - Data viewer integration

**2. Emacs/Spacemacs Integration** ⭐⭐⭐
- **Why:** Your primary R editor
- **Effort:** 1 week
- **Features:**
  - Elisp package
  - Mode line integration
  - ESS (Emacs Speaks Statistics) integration
  - Projectile integration

**3. Zed Integration** ⭐⭐
- **Why:** Modern, fast editor
- **Effort:** 3-5 days
- **Features:**
  - Rust extension
  - Fast startup
  - Modern UI

**4. VS Code Integration** ⭐⭐
- **Why:** Widely used, good ecosystem
- **Effort:** 3-5 days
- **Features:**
  - TypeScript extension
  - Status bar integration
  - Command palette

### Phase 2 (v0.4+) - Nice-to-Have

**5. OpenCode Integration** ⭐
- Only if it's different from VS Code
- **Effort:** 1-2 days

**6. iTermAI Integration** ⭐
- Only if it has unique features beyond iTerm2
- **Effort:** 1-2 days

### Skipped (Not Installed)

- ❌ Cursor (not installed)
- ❌ Neovim (not in PATH)
- ❌ Warp (not installed)
- ❌ VSCodium (not installed)
- ❌ Alacritty (not installed)
- ❌ Kitty (not installed)

---

## 🗂️ MCP SERVERS CONSOLIDATION (Already Done! ✅)

**Status:** Already organized in `~/projects/dev-tools/mcp-servers/` ✅

**Existing Servers (5):**
1. statistical-research/ ✅
2. shell/ ✅
3. project-refactor/ ✅
4. obsidian-ops/ ✅
5. docling/ ✅

**NEW Server to Add:**
6. aiterm-mcp-marketplace/ 🆕

**Actions:**
- ✅ Already in unified location
- 🆕 Create aiterm-mcp-marketplace
- ✅ Update README.md with new server
- ✅ Add to _MCP_SERVERS.md index

---

## 📝 README & CLAUDE.md UPDATES

### README.md Updates Needed

1. Change tagline from "Terminal Optimizer" to "AI Coding Ecosystem Platform"
2. Add "npm for AI coding tools" pitch
3. Update features list:
   - Add MCP server management
   - Add MCP creation tools
   - Add meta MCP server
   - Add IDE integrations
   - Add learning resources
4. Update roadmap references
5. Add links to new documentation

### CLAUDE.md Updates Needed

1. Update project overview with new scope
2. Add MCP servers location (`~/projects/dev-tools/mcp-servers/`)
3. Add DT's actual IDE/terminal setup
4. Update integration priorities (Positron, Emacs, Zed, VS Code)
5. Add documentation structure
6. Add guidelines for MCP server development
7. Add success criteria for v0.2.0, v0.3.0

**Already done in AITERM-COMPLETE-VISION.md!** Just need to copy to main files.

---

## 🎓 LEARNING RESOURCES STRUCTURE

### Directory Structure to Create

```bash
mkdir -p docs/{tutorials,ref-cards,interactive,examples,api}
mkdir -p docs/tutorials/{getting-started,mcp-creation,plugin-development,ide-integration}
mkdir -p docs/ref-cards
mkdir -p docs/interactive/{mcp-creator,hook-builder,plugin-wizard}
mkdir -p docs/examples/{servers,plugins,hooks}
mkdir -p docs/api
```

### Initial Files to Create

**Tutorials (Week 1-2):**
1. `docs/tutorials/getting-started/01-installation.md`
2. `docs/tutorials/mcp-creation/01-your-first-server.md`

**Ref-Cards (Week 1-2):**
1. `docs/ref-cards/aiterm-commands.md`
2. `docs/ref-cards/mcp-server-api.md`

**Examples (Week 2-3):**
1. `docs/examples/servers/simple-api/`
2. `docs/examples/servers/database-postgres/`

**Interactive (Week 3-4):**
1. `docs/interactive/mcp-creator/index.html`

---

## 🚀 PHASE BREAKDOWN

### Phase 1: Foundation (v0.2.0) - Week 1-3

**Deliverables:**
- ✅ Brainstorm documents committed
- 🆕 aiterm-mcp-marketplace server working
- 📚 2+ tutorials written
- 📄 2+ ref-cards created
- 💻 MCP management CLI (search, install, test)
- 🎨 MCP creation wizard (5 templates)

**Success Criteria:**
- Can search for MCP servers from Claude
- Can install servers conversationally
- Can create new servers from templates in 5 minutes
- Documentation covers basics

### Phase 2: IDE Integration (v0.3.0) - Week 4-6

**Deliverables:**
- 🔌 Positron extension working
- 🔌 Emacs package working
- 🔌 Zed extension working
- 🔌 VS Code extension working
- 📚 IDE integration tutorials
- 📄 Integration API ref-card

**Success Criteria:**
- aiterm commands accessible from Positron
- Emacs mode line shows context
- Zed command palette has aiterm commands
- VS Code status bar shows MCP servers

### Phase 3: Advanced Features (v0.4.0) - Week 7-9

**Deliverables:**
- 🎮 Interactive MCP creator (web UI)
- 🎮 Interactive hook builder (web UI)
- 📚 10+ tutorials complete
- 📄 5+ ref-cards complete
- 🪝 Hook management system
- 🔄 Settings sync

**Success Criteria:**
- Interactive tutorials launch in browser
- Complete tutorial coverage
- All ref-cards printable
- Hook creation from templates

### Phase 4: Intelligence (v1.0.0) - Month 3

**Deliverables:**
- 🤖 AI-assisted MCP generation
- 💡 Context-aware recommendations
- 🏪 Template marketplace
- 📦 Public release (PyPI, Homebrew)

**Success Criteria:**
- MCP servers generated from API docs
- Recommendations based on project type
- 100+ external users
- Community contributions

---

## 🎯 DECISION POINTS

### Questions for DT

1. **aiterm-mcp-marketplace Priority?**
   - Start with meta MCP server first? (my recommendation: YES!)
   - Or start with CLI management first?

2. **IDE Integration Order?**
   - Positron → Emacs → Zed → VS Code? (my recommendation)
   - Or Emacs → Positron → Zed → VS Code?

3. **Documentation Priority?**
   - Tutorials first or ref-cards first?
   - My recommendation: Both in parallel (tutorials Week 1, ref-cards Week 1-2)

4. **Interactive Tutorials Timeline?**
   - Week 3-4 or defer to v0.4.0?
   - My recommendation: Week 3-4 (high impact for learning)

---

## 📊 SUCCESS METRICS

### v0.2.0 (Week 3)
- [ ] aiterm-mcp-marketplace server working
- [ ] Can search and install servers from Claude
- [ ] MCP creation from templates working
- [ ] 2+ tutorials published
- [ ] 2+ ref-cards created

### v0.3.0 (Week 6)
- [ ] 4 IDE integrations working (Positron, Emacs, Zed, VS Code)
- [ ] IDE integration tutorials complete
- [ ] 5+ tutorials published
- [ ] 3+ ref-cards created

### v0.4.0 (Week 9)
- [ ] Interactive tutorials live
- [ ] 10+ tutorials complete
- [ ] 5+ ref-cards complete
- [ ] Hook management working

### v1.0.0 (Month 3)
- [ ] AI-assisted generation working
- [ ] 100+ external users
- [ ] PyPI package published
- [ ] Community marketplace launched

---

## 🔄 ITERATIVE APPROACH

**Week 1:**
- Day 1-2: Commit brainstorms, start aiterm-mcp-marketplace
- Day 3-4: Continue marketplace server, write first tutorial
- Day 5: Create first ref-card, test marketplace server

**Week 2:**
- Day 1-2: Finish marketplace server, test with Claude
- Day 3-4: Implement `aiterm mcp search|install`
- Day 5: Write API integration tutorial

**Week 3:**
- Day 1-2: Implement `aiterm mcp create` wizard
- Day 3-4: Create 5 MCP templates
- Day 5: Write MCP creation tutorials

**Week 4-6:**
- IDE integrations (one per week)
- Continue documentation

**Week 7-9:**
- Interactive tutorials
- Hook management
- Polish

---

**Last Updated:** 2025-12-19
**Status:** 🟢 Ready to execute
**Next Action:** Commit brainstorms, then create aiterm-mcp-marketplace server!
