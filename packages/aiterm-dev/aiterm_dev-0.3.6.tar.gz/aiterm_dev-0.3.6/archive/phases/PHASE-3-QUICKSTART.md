# Phase 3: Quick Start Guide

**TL;DR:** Build practical tools (hooks, commands, MCP), defer AI experiments.

---

## The Decision

**Phase 3A: Core Features** (2 weeks) ⭐ RECOMMENDED

Build tools that solve real pain points:
1. **Hook Management** - Discover and install Claude Code hooks
2. **Command Templates** - Browse and install reusable commands
3. **MCP Integration** - Test and validate MCP servers

**NOT:** AI-powered documentation generation (deferred to Phase 4)

---

## Why Core Features First?

### Pain Points We're Solving

**Current State:**
- 🔴 Users don't know what hooks exist (only 2/9 installed)
- 🔴 194 commands with no discovery mechanism
- 🔴 MCP servers tested by trial-and-error
- 🔴 Broken docs links, outdated examples

**After Phase 3A:**
- ✅ `aiterm hooks list` - See all available hooks
- ✅ `aiterm hooks install <template>` - One command installation
- ✅ `aiterm commands browse` - Interactive template browser
- ✅ `aiterm mcp test <server>` - Automated testing
- ✅ `aiterm docs validate-links` - Find broken links

---

## What You'll Build

### Week 1: Discovery & Templates

**Days 1-2: Hook Management**
```bash
# What users will do:
aiterm hooks list              # See installed hooks
aiterm hooks install prompt-optimizer
aiterm hooks validate          # Check all hooks work
aiterm hooks test session-start
```

**Deliverables:**
- 5 hook templates (session-start, prompt-optimizer, tool-validator, cost-tracker, session-logger)
- Hook discovery, installation, validation, testing
- ~6-8 hours

**Days 3-4: Command Templates**
```bash
# What users will do:
aiterm commands browse         # Interactive menu
aiterm commands install git:sync
aiterm commands validate       # Check all installed commands
aiterm commands run test:watch  # Run without installing
```

**Deliverables:**
- 20+ command templates (git workflows, testing, docs, R-dev, Python-dev)
- Command browser, installer, validator
- ~5-7 hours

**Day 5: Testing & Documentation**
- Integration tests for all features
- Update user guide with new commands
- ~2 hours

### Week 2: Integration & Polish

**Days 1-2: MCP Integration**
```bash
# What users will do:
aiterm mcp list                # Show configured servers
aiterm mcp test statistical-research
aiterm mcp validate            # Check settings.json
```

**Deliverables:**
- MCP server discovery, testing, validation
- Settings.json helpers
- ~4-6 hours

**Days 3-4: Documentation Helpers (Simple)**
```bash
# What users will do:
aiterm docs validate-links     # Find broken links (grep-based)
aiterm docs test-examples      # Validate code blocks (static)
```

**Deliverables:**
- Link validation (no LLM)
- Code example testing
- ~2-3 hours

**Day 5: Release**
- Final testing
- CHANGELOG update
- Tag v0.2.0-dev
- ~1 hour

---

## Architecture Overview

### Directory Structure
```
aiterm/
├── src/aiterm/
│   ├── cli/
│   │   ├── hooks.py       # Hook commands (NEW)
│   │   ├── commands.py    # Command commands (NEW)
│   │   ├── mcp.py         # MCP commands (NEW)
│   │   └── docs.py        # Doc helpers (NEW)
│   ├── hooks/             # Hook management logic (NEW)
│   ├── commands/          # Command library logic (NEW)
│   └── mcp/               # MCP integration logic (NEW)
├── templates/
│   ├── hooks/             # 5 hook templates (NEW)
│   └── commands/          # 20+ command templates (NEW)
└── tests/
    ├── test_hooks.py      # Hook tests (NEW)
    ├── test_commands.py   # Command tests (NEW)
    └── test_mcp.py        # MCP tests (NEW)
```

### Key Design Decisions

**1. Template Storage**
- Built-in templates: `aiterm/templates/`
- User overrides: `~/.aiterm/hooks/`, `~/.aiterm/commands/`
- Installation: Copy (don't symlink) so users can edit

**2. Hook Installation**
```bash
aiterm hooks install prompt-optimizer
# Copies: templates/hooks/prompt-optimizer.sh
# To: ~/.claude/hooks/prompt-optimizer.sh
# Sets executable permissions
```

**3. Command Installation**
```bash
aiterm commands install git:sync
# Copies: templates/commands/git/sync.md
# To: ~/.claude/commands/git/sync.md
# Prompts for customization (repo URL, branch)
```

**4. MCP Testing**
```bash
aiterm mcp test statistical-research
# Reads: ~/.claude/settings.json
# Calls: Server via Claude Code CLI
# Reports: Tool count, response times, errors
```

---

## Timeline

| Week | Days | Focus | Hours | Deliverables |
|------|------|-------|-------|-------------|
| **1** | 1-2 | Hook management | 6-8 | 5 templates, CLI commands |
| **1** | 3-4 | Command templates | 5-7 | 20+ templates, browser |
| **1** | 5 | Testing & docs | 2 | Integration tests, guides |
| **2** | 1-2 | MCP integration | 4-6 | Server testing, validation |
| **2** | 3-4 | Doc helpers | 2-3 | Link validation, examples |
| **2** | 5 | Release prep | 1 | v0.2.0-dev tag |
| | | **TOTAL** | **20-27** | **v0.2.0-dev release** |

---

## Success Criteria

### Must Have ✅
- [ ] `aiterm hooks list` shows installed hooks
- [ ] `aiterm hooks install <template>` works for 5+ templates
- [ ] `aiterm commands browse` shows 20+ templates
- [ ] `aiterm commands install <name>` installs correctly
- [ ] `aiterm mcp list` shows configured servers
- [ ] `aiterm mcp test <server>` validates functionality
- [ ] All features have 80%+ test coverage
- [ ] Documentation updated with new features

### Nice to Have 🎯
- [ ] `aiterm docs validate-links` finds broken links
- [ ] `aiterm docs test-examples` validates code blocks
- [ ] Command templates support customization prompts
- [ ] Hook templates include usage examples

### Deferred to Phase 4 ⏸️
- [ ] AI-powered documentation generation
- [ ] LLM semantic analysis
- [ ] Multi-file consistency checks
- [ ] Screenshot/diagram automation

---

## What's NOT in Phase 3

### Deferred to Phase 4 (AI Features)
- ❌ GPT-4 analyzes code changes
- ❌ LLM generates documentation
- ❌ AI writes tutorial content
- ❌ Multi-document semantic coordination

**Why defer?**
1. Unproven value (experimental)
2. High complexity (15-20 hours)
3. External dependencies (API costs)
4. Need validation of demand first

**When to revisit?**
- After Phase 3A complete and validated
- After 1+ month of real aiterm usage
- If user explicitly requests AI features

---

## Getting Started (Day 1)

### 1. Create Directory Structure
```bash
mkdir -p src/aiterm/{hooks,commands,mcp}
mkdir -p templates/{hooks,commands}
mkdir -p tests
touch src/aiterm/cli/{hooks,commands,mcp,docs}.py
```

### 2. Start with Hook Discovery
```python
# src/aiterm/hooks/manager.py
class HookManager:
    """Manage Claude Code hooks."""

    HOOK_DIR = Path.home() / ".claude" / "hooks"
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "hooks"

    def list_installed(self) -> List[Hook]:
        """List installed hooks."""
        pass

    def list_available(self) -> List[Template]:
        """List available templates."""
        pass

    def install(self, template: str) -> bool:
        """Install hook from template."""
        pass
```

### 3. Create First Hook Template
```bash
# templates/hooks/prompt-optimizer.sh
#!/bin/bash
# UserPromptSubmit Hook: Optimize prompts with project context
# ...
```

### 4. Test Installation Flow
```bash
aiterm hooks install prompt-optimizer
# Should copy template to ~/.claude/hooks/
# Should set executable permissions
# Should show success message
```

---

## Quick Reference

### Commands to Build

**Hook Management:**
- `aiterm hooks list` - Show installed hooks
- `aiterm hooks install <template>` - Install hook template
- `aiterm hooks validate` - Validate all hooks
- `aiterm hooks test <hook>` - Test specific hook

**Command Templates:**
- `aiterm commands browse` - Interactive template browser
- `aiterm commands install <name>` - Install command template
- `aiterm commands validate` - Validate all commands
- `aiterm commands run <name>` - Run without installing

**MCP Integration:**
- `aiterm mcp list` - List configured servers
- `aiterm mcp test <server>` - Test server functionality
- `aiterm mcp validate` - Validate settings.json

**Documentation:**
- `aiterm docs validate-links` - Find broken links
- `aiterm docs test-examples` - Validate code examples

---

## Resources

**Planning Documents:**
- `PHASE-3-PLAN.md` - Full implementation plan (18K)
- `PHASE-3-DECISION-MATRIX.md` - Feature comparison (12K)
- `PHASE-3-QUICKSTART.md` - This document

**Related Documentation:**
- `PHASE-0-DOCUMENTATION-COMPLETE.md` - Phase 0 results
- `PHASE-2-AUTO-UPDATES-PLAN.md` - Phase 2 auto-updates
- `IDEAS.md` - Long-term vision
- `ROADMAP.md` - Project roadmap

**User Workflow:**
- `~/.claude/commands/workflow/` - Workflow plugin commands
- `~/.claude/hooks/` - Existing hooks
- `~/projects/dev-tools/mcp-servers/` - MCP servers

---

## Questions?

**Need clarification?** Read:
1. `PHASE-3-DECISION-MATRIX.md` - Why core features?
2. `PHASE-3-PLAN.md` - Detailed implementation

**Ready to start?**
- Confirm Phase 3A scope
- Begin Day 1: Hook management
- Create first 3 templates

**Want different scope?**
- Adjust priorities in planning docs
- Revise timeline
- Get final approval

---

**Ready to build Phase 3A (Core Features)?** 🚀
