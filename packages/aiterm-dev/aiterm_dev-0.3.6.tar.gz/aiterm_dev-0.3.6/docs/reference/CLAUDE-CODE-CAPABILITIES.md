# Claude Code & Desktop Capabilities

**Research Date:** December 15, 2025
**Purpose:** Understanding enhancement possibilities for aiterm

---

## Executive Summary

**Three Pillars of Claude Ecosystem:**

1. **MCP (Model Context Protocol)** - Connect AI to external services (GitHub, Slack, databases)
2. **Desktop Extensions (.mcpb)** - 1-click MCP server installation (replaces manual config)
3. **Skills** - Reusable AI workflows with instructions + optional code

**All three work in:**
- Claude Desktop UI
- Claude Code CLI
- Claude API (with code execution)

**Status:** MCP is now industry standard (Linux Foundation), actively growing, NOT deprecated.

---

## Enhancement Opportunities for aiterm

### 🎯 What aiterm Can Optimize

#### 1. MCP Server Management
**Current Pain Points:**
- Manual `.mcp.json` editing
- Finding servers (scattered across GitHub, mcp.run, glama.ai)
- Testing configurations
- Managing credentials

**aiterm Opportunities:**
```bash
# Phase 2-3 features
aiterm mcp list                    # Show installed servers
aiterm mcp search <keyword>        # Search registry
aiterm mcp install <server>        # Install + configure
aiterm mcp test <server>          # Test connection
aiterm mcp config <server>        # Interactive config
aiterm mcp credentials <server>   # Secure credential mgmt
```

#### 2. Skills Management
**Current Pain Points:**
- Manual SKILL.md creation
- No discovery mechanism
- Sharing requires copy/paste
- No versioning

**aiterm Opportunities:**
```bash
# Phase 2-3 features
aiterm skills list                 # Show available skills
aiterm skills create <name>        # Interactive skill creator
aiterm skills install <name>       # From template library
aiterm skills share <name>         # Export for team
aiterm skills validate <name>      # Check SKILL.md format
```

**Skill Templates aiterm Could Provide:**
- **Research workflows** - Literature search, citation formatting
- **R package workflows** - Test → check → document → build
- **Code review standards** - Your project-specific review process
- **Data analysis** - Standard analysis patterns
- **Teaching** - Assignment grading, feedback templates

#### 3. Desktop Extensions Discovery
**Current State:**
- Must browse in app
- No CLI access
- No batch installation

**aiterm Opportunities:**
```bash
# Phase 3-4 features
aiterm ext list                    # Show available extensions
aiterm ext search <keyword>        # Search directory
aiterm ext recommend              # Based on project type
aiterm ext info <name>            # Show details
```

#### 4. Command System Enhancement
**Current Capabilities:**
- Custom slash commands in `.claude/commands/*.md`
- Simple argument passing
- No validation, no discovery

**aiterm Opportunities:**
```bash
# Phase 2 features
aiterm claude commands list                  # Show all commands
aiterm claude commands create <name>         # Interactive creator
aiterm claude commands template <type>       # From library
aiterm claude commands validate             # Check syntax
aiterm claude commands test <name>          # Dry run

# Command templates
aiterm claude commands template workflow     # /recap, /next, /focus
aiterm claude commands template research     # /literature, /cite
aiterm claude commands template dev          # /review, /test, /deploy
```

#### 5. Hooks System (Discovered Capability!)
**Current State:** Documented but underused

**Hook Types Available:**
- `SessionStart` - When Claude Code starts
- `SessionEnd` - When Claude Code exits
- `ToolUse` - Before/after tool use
- `UserPrompt` - Before user prompt processed

**aiterm Opportunities:**
```bash
# Phase 2 features
aiterm claude hooks list                     # Show available hooks
aiterm claude hooks install <name>           # From template library
aiterm claude hooks create <name>            # Interactive creator
aiterm claude hooks enable/disable <name>    # Toggle hooks

# Hook templates
aiterm claude hooks install session-start    # Show quota on startup
aiterm claude hooks install pre-commit       # Run tests before commit
aiterm claude hooks install cost-tracker     # Monitor API costs
aiterm claude hooks install context-aware    # Detect project, set vars
```

**Hook Template Library:**
```yaml
# session-start.yaml
name: "Quota Display"
trigger: SessionStart
script: |
  #!/bin/bash
  # Show quota status
  ~/.claude/statusline-p10k.sh --quota-only

  # Show project context
  aiterm context show
```

#### 6. Settings Management
**Current Pain Points:**
- Manual JSON editing
- No validation
- No presets
- Auto-approvals hard to manage

**aiterm Already Planned:**
```bash
aiterm claude settings show
aiterm claude settings backup
aiterm claude settings validate
aiterm claude approvals add-preset <name>
aiterm claude approvals list
```

**Additional Opportunities:**
```bash
# Phase 2-3
aiterm claude settings diff              # Compare with default
aiterm claude settings migrate           # Upgrade format
aiterm claude settings export            # For team sharing
aiterm claude settings import <file>     # Load team config
```

---

## Integration Patterns

### Pattern 1: Context-Aware Skills
**Idea:** aiterm detects project type, auto-suggests relevant skills

```bash
cd ~/projects/r-packages/medfit
aiterm context detect

# aiterm responds:
📦 R Package detected: medfit

💡 Recommended skills:
  1. r-package-workflow (test → check → document)
  2. statistical-methods (analysis templates)
  3. cran-submission (prepare for CRAN)

Install? (y/n)
```

### Pattern 2: MCP + Context Integration
**Idea:** Auto-configure MCP servers based on project

```bash
cd ~/projects/research/paper
aiterm context detect

# aiterm responds:
📝 Research project detected

💡 Recommended MCP servers:
  1. zotero-mcp (bibliography management)
  2. filesystem (local file access)
  3. r-execution (run R code)

Install? (y/n)
```

### Pattern 3: Workflow Automation
**Idea:** Combine hooks + skills + context

```yaml
# .claude/workflows/r-package-dev.yaml
name: "R Package Development"
triggers:
  - context: rpkg

hooks:
  SessionStart:
    - show-quota
    - check-git-status
    - display-test-coverage

skills:
  - r-package-workflow
  - code-review-standards

mcp_servers:
  - filesystem
  - github

commands:
  - /check (runs devtools::check())
  - /test (runs devtools::test())
  - /document (runs devtools::document())
```

Usage:
```bash
aiterm workflow install r-package-dev
cd ~/projects/r-packages/medfit
# Workflow auto-activates!
```

---

## MCP Server Ecosystem (Relevant to DT)

### Statistical/Research
- **zotero-mcp** - Bibliography management
- **r-mcp** - Execute R code (your existing Statistical Research MCP!)
- **python-mcp** - Execute Python
- **jupyter-mcp** - Notebook interaction

### Development
- **filesystem** - Local file access ✅ (you use this)
- **github** - Issues, PRs, repos
- **gitlab** - Similar for GitLab
- **git-mcp** - Advanced git operations

### Data
- **postgres-mcp** - Database queries
- **sqlite-mcp** - Local databases
- **mongodb-mcp** - NoSQL
- **csv-mcp** - CSV file operations

### Productivity
- **slack-mcp** - Send messages, search
- **google-drive-mcp** - Access Drive
- **notion-mcp** - Database queries
- **calendar-mcp** - Calendar integration

---

## Skills Use Cases for DT

### Research Skills
```markdown
# .claude/skills/statistical-analysis/SKILL.md
---
name: "Statistical Analysis Workflow"
description: "Standard analysis pipeline for research projects"
---

When analyzing data:
1. Load with {readr} or {haven}
2. Check assumptions (normality, homoscedasticity)
3. Descriptive statistics table (Table 1)
4. Main analysis with sensitivity
5. Generate publication-quality plots
6. Export results to LaTeX tables
```

### Teaching Skills
```markdown
# .claude/skills/grade-assignment/SKILL.md
---
name: "Assignment Grading"
description: "Consistent grading workflow for student submissions"
---

Grading criteria:
1. Code runs without errors (40%)
2. Correct statistical method (30%)
3. Interpretation clarity (20%)
4. Code style and documentation (10%)

Provide:
- Numeric grade
- 2-3 sentence feedback
- 1 suggestion for improvement
```

### Package Development Skills
```markdown
# .claude/skills/r-package-release/SKILL.md
---
name: "R Package Release Checklist"
description: "Pre-release checks for R packages"
---

Before releasing:
1. Run devtools::check() - must pass
2. Update NEWS.md with changes
3. Update version in DESCRIPTION
4. Run pkgdown::build_site()
5. Update README with new version
6. Create GitHub release
7. Submit to CRAN (if public)
```

---

## Enhancement Priority Matrix

### High Priority (Phase 2)
- ✅ Hook management system
- ✅ Command template library
- ✅ Skills creation workflow
- ✅ MCP server installation helper

### Medium Priority (Phase 3)
- MCP server discovery/search
- Skills marketplace/sharing
- Workflow automation system
- Team config sharing

### Low Priority (Phase 4)
- Desktop Extension CLI access
- Advanced hook orchestration
- Multi-project workflows
- Integration with other tools

---

## Technical Implementation Notes

### File Locations
```
~/.claude/                          # Personal config
├── settings.json                   # Main settings
├── skills/                         # Personal skills
│   └── my-skill/
│       └── SKILL.md
├── commands/                       # Custom commands
│   └── my-command.md
└── hooks/                          # Hooks (if supported)
    └── session-start.sh

.claude/                            # Project config
├── CLAUDE.md                       # Project context
├── skills/                         # Project-specific skills
├── commands/                       # Project commands
└── .mcp.json                      # MCP servers
```

### Settings.json Structure
```json
{
  "autoApprove": [
    "Bash(ls:*)",
    "Read(*)"
  ],
  "statusLine": {
    "type": "command",
    "command": "/path/to/script.sh"
  },
  "hooks": {
    "SessionStart": "/path/to/hook.sh"
  }
}
```

### .mcp.json Structure
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

---

## Integration with Existing DT Setup

### Current Setup
- ✅ Statistical Research MCP (14 tools, 17 skills) - **Already using MCP!**
- ✅ Shell MCP server - **Already using MCP!**
- ✅ Filesystem MCP - **Already using MCP!**
- ✅ StatusLine script (`~/.claude/statusline-p10k.sh`)
- ✅ Quota tracking (`qu` command)
- ✅ Workflow commands (`/recap`, `/next`, `/focus`)

### aiterm Enhancements
```bash
# Migrate workflow commands to official Claude Code commands
aiterm claude commands migrate-from ~/.claude/commands/

# Create skills from your workflow
aiterm skills create research-workflow
aiterm skills create teaching-workflow

# Manage your MCP servers
aiterm mcp list
# Shows: statistical-research, shell, filesystem

aiterm mcp config statistical-research
# Interactive config editor

# Create hooks for quota display
aiterm claude hooks install session-start
# Uses your existing qu + statusline scripts
```

---

## References

- **MCP Spec**: https://modelcontextprotocol.io
- **MCP Registry**: https://mcp.run
- **Skills Docs**: https://docs.claude.com/en/docs/claude-code/skills
- **Claude Code Docs**: https://code.claude.com/docs
- **Awesome Claude Code**: https://github.com/hesreallyhim/awesome-claude-code

---

**Next Steps for aiterm:**
1. Update IDEAS.md with specific MCP/Skills/Hooks features
2. Add to ROADMAP.md (Phase 2 priorities)
3. Design CLI commands for MCP/Skills management
4. Create template library structure

**Key Insight:** We're not just optimizing terminal profiles—we're building a **Claude Code power-user toolkit** that manages the entire ecosystem (MCP + Skills + Hooks + Commands + Context).
