# Phase 3: Feature Implementation Plan

**Date:** 2025-12-24
**Status:** Planning
**Predecessors:** Phase 0 (Docs ✅), Phase 1 (Detection ✅), Phase 2 (Auto-Updates ✅)

---

## Overview

Phase 3 marks the transition from **documentation infrastructure** to **feature implementation**. With comprehensive docs in place and auto-update systems working, we can now focus on building the core aiterm features that power users actually need.

**Philosophy:** Ship practical features that solve real problems, not hypothetical AI-powered systems.

---

## Decision: What to Build in Phase 3?

### Original Plan: LLM-Powered Documentation

From IDEAS.md and ROADMAP.md, Phase 3 was planned as:
- GPT-4 generates doc updates from code
- Analyzes semantic changes (not just diffs)
- Writes tutorial content automatically
- Multi-file coordination

**Timeline:** 2-3 weeks
**Complexity:** High
**User Value:** Uncertain (experimental)

### Alternative: Core Feature Implementation

Build the features that aiterm users actually need:
1. **Hook Management System** - Install/manage Claude Code hooks
2. **Command Template Library** - Reusable command templates
3. **MCP Server Integration** - Discover/test/configure MCP servers
4. **StatusLine Builder** - Interactive statusLine generator

**Timeline:** 2-3 weeks
**Complexity:** Medium
**User Value:** High (proven demand)

---

## Recommendation: Hybrid Approach ⭐

**Phase 3A: Core Features (2 weeks)**
- Hook management (Priority 1)
- Command templates (Priority 2)
- MCP integration basics (Priority 3)

**Phase 3B: Enhanced Documentation (1 week - Optional)**
- Simple LLM helpers (not full automation)
- Documentation validation
- Link checking and fixing

**Total:** 2-3 weeks depending on optional features

---

## Phase 3A: Core Features (RECOMMENDED)

### 1. Hook Management System (Priority 1)

**Goal:** Make Claude Code hooks discoverable, installable, and manageable.

**Current State:**
- Hooks must be manually created in `~/.claude/hooks/`
- 9 hook types available (SessionStart, UserPromptSubmit, PreToolUse, etc.)
- No discovery or validation tools
- Users don't know what hooks exist or how to use them

**Features to Build:**

#### 1.1 Hook Discovery
```bash
aiterm hooks list
# Output:
# Available Hooks:
# ✅ SessionStart       ~/.claude/hooks/session-start.sh
# ❌ UserPromptSubmit   (not installed)
# ❌ PreToolUse         (not installed)
# ...
```

#### 1.2 Hook Templates
```bash
aiterm hooks install <template>
# Templates:
# - prompt-optimizer    (UserPromptSubmit - add @smart feature)
# - tool-validator      (PreToolUse - validate dangerous commands)
# - session-logger      (SessionStart - log session metadata)
# - cost-tracker        (SessionEnd - track API costs)
```

#### 1.3 Hook Validation
```bash
aiterm hooks validate
# Checks:
# ✅ Executable permissions
# ✅ Exit codes (0 = success)
# ✅ Output format
# ⚠️  Performance (< 500ms)
```

#### 1.4 Hook Testing
```bash
aiterm hooks test session-start
# Runs hook in test mode with sample data
# Shows output and timing
```

**Implementation:**
- `src/aiterm/cli/hooks.py` - CLI commands
- `src/aiterm/hooks/` - Hook management logic
- `templates/hooks/` - Hook templates (10-15 templates)
- `tests/test_hooks.py` - Hook tests

**Time Estimate:** 6-8 hours

---

### 2. Command Template Library (Priority 2)

**Goal:** Provide reusable command templates for common workflows.

**Current State:**
- 194 commands in user's `~/.claude/commands/` directory
- No easy way to discover/install useful commands
- Users reinvent common patterns (git workflows, test runners, etc.)

**Features to Build:**

#### 2.1 Command Discovery
```bash
aiterm commands browse
# Interactive menu:
# 📁 Git Workflows
#    → /git:sync - Smart git sync with safety checks
#    → /git:pr - Create PR with template
# 📁 Testing
#    → /test:watch - Watch mode test runner
#    → /test:coverage - Coverage report generator
# 📁 Documentation
#    → /docs:check - Link validation + orphan detection
```

#### 2.2 Command Installation
```bash
aiterm commands install git:sync
# Installs to ~/.claude/commands/git/sync.md
# Prompts for customization (repo URL, branch names)
```

#### 2.3 Command Validation
```bash
aiterm commands validate
# Checks all installed commands:
# ✅ Valid frontmatter (YAML)
# ✅ Required fields present
# ⚠️  Deprecated syntax detected
```

**Implementation:**
- `src/aiterm/cli/commands.py` - CLI commands
- `templates/commands/` - Command library (20-30 templates)
- Command categories: git, testing, docs, workflows, mcp, r-dev, python-dev

**Time Estimate:** 5-7 hours

---

### 3. MCP Server Integration (Priority 3)

**Goal:** Simplify MCP server discovery, testing, and configuration.

**Current State:**
- MCP servers configured in `~/.claude/settings.json`
- Manual JSON editing required
- No validation or testing tools
- Users struggle with server configuration

**Features to Build:**

#### 3.1 MCP Server Discovery
```bash
aiterm mcp list
# Shows configured servers:
# ✅ statistical-research  (14 tools, running)
# ✅ shell                 (5 tools, running)
# ❌ filesystem            (not running)
```

#### 3.2 MCP Server Testing
```bash
aiterm mcp test statistical-research
# Tests all tools:
# ✅ execute_r_code         (200ms)
# ✅ search_literature      (450ms)
# ❌ query_zotero          (timeout)
```

#### 3.3 MCP Server Validation
```bash
aiterm mcp validate
# Checks settings.json:
# ✅ Valid JSON syntax
# ✅ All server paths exist
# ⚠️  Server 'shell' not in PATH
```

#### 3.4 MCP Server Templates (Future)
```bash
aiterm mcp create <name>
# Interactive wizard:
# - Language? (Python/Node/Shell)
# - Tool count? (1-20)
# - Generates scaffold
```

**Implementation:**
- `src/aiterm/cli/mcp.py` - CLI commands
- `src/aiterm/mcp/` - MCP logic (discovery, testing, validation)
- Leverage existing `~/projects/dev-tools/mcp-servers/` organization

**Time Estimate:** 4-6 hours

---

## Phase 3B: Enhanced Documentation (OPTIONAL)

### Simple LLM Helpers (Not Full Automation)

Instead of building a full AI documentation system, add targeted helpers:

#### 1. Documentation Quality Check
```bash
aiterm docs check
# Uses LLM to:
# ✅ Find broken examples
# ✅ Identify outdated screenshots
# ✅ Suggest missing sections
# ⚠️  Inconsistent terminology
```

#### 2. Link Validation
```bash
aiterm docs validate-links
# Checks all markdown files:
# ✅ Internal links (265/268 valid)
# ❌ Broken: api/AITERM-API.md#context-object
# ⚠️  External link slow: https://example.com
```

#### 3. Code Example Validation
```bash
aiterm docs test-examples
# Extracts and tests all code blocks:
# ✅ Python examples (12/12 passed)
# ✅ Bash examples (8/8 passed)
# ❌ CLI example failed: aiterm context show --format=json
```

**Implementation:**
- `src/aiterm/cli/docs.py` - CLI commands
- Optional dependency on `anthropic` SDK for LLM features
- Falls back gracefully if API key not configured

**Time Estimate:** 3-4 hours (optional)

---

## Phase 3 Timeline

### Week 1: Hook Management + Command Templates
**Days 1-2:** Hook management system
- Hook discovery and listing
- Hook validation and testing
- 3-5 hook templates

**Days 3-4:** Command template library
- Command browsing and installation
- 10-15 command templates
- Command validation

**Day 5:** Testing and documentation
- Integration tests
- Update docs with new features
- User guide updates

### Week 2: MCP Integration + Polish
**Days 1-2:** MCP server integration
- Server discovery and listing
- Server testing and validation
- Settings.json helpers

**Day 3:** Documentation helpers (optional)
- Link validation
- Code example testing
- Quality checks

**Days 4-5:** Release preparation
- Comprehensive testing
- Documentation updates
- CHANGELOG generation
- v0.2.0-dev tag

---

## Success Criteria

### Must Have (Phase 3A)
- ✅ `aiterm hooks list` shows installed hooks
- ✅ `aiterm hooks install <template>` works for 5+ templates
- ✅ `aiterm commands browse` shows 20+ templates
- ✅ `aiterm commands install <name>` installs to correct location
- ✅ `aiterm mcp list` shows configured servers
- ✅ `aiterm mcp test <server>` validates server functionality
- ✅ All features tested (80%+ coverage)
- ✅ Documentation updated

### Nice to Have (Phase 3B)
- ✅ `aiterm docs validate-links` finds broken links
- ✅ `aiterm docs test-examples` validates code blocks
- ✅ LLM-powered quality suggestions

### Deferred to Phase 4
- Full AI documentation generation
- Multi-file consistency checking
- Screenshot/diagram auto-generation
- Interactive doc review interface

---

## Implementation Order

### 1. Foundation (Day 1)
```bash
# Create directory structure
src/aiterm/hooks/
src/aiterm/commands/
src/aiterm/mcp/
templates/hooks/
templates/commands/
```

### 2. Hook Management (Days 2-3)
```python
# src/aiterm/hooks/manager.py
class HookManager:
    def list_installed() -> List[Hook]
    def list_available() -> List[Template]
    def install(template: str) -> bool
    def validate(hook: str) -> ValidationResult
    def test(hook: str) -> TestResult
```

### 3. Command Templates (Days 4-5)
```python
# src/aiterm/commands/library.py
class CommandLibrary:
    def browse(category: str = None) -> List[Command]
    def install(command: str) -> bool
    def validate_all() -> ValidationReport
```

### 4. MCP Integration (Days 6-7)
```python
# src/aiterm/mcp/manager.py
class MCPManager:
    def list_servers() -> List[Server]
    def test_server(name: str) -> TestResult
    def validate_config() -> ValidationResult
```

### 5. Documentation (Day 8-9)
- Update all docs with new features
- Create user guide sections
- Add integration examples

### 6. Testing & Release (Day 10)
- Integration tests
- Manual testing
- CHANGELOG update
- Tag v0.2.0-dev

---

## Architecture Decisions

### 1. Template Storage

**Decision:** Ship templates with package, allow user overrides

```
aiterm/
├── templates/          # Built-in templates (read-only)
│   ├── hooks/
│   └── commands/
~/.aiterm/              # User templates (overrides)
├── hooks/
└── commands/
```

### 2. Hook Installation

**Decision:** Copy templates to `~/.claude/hooks/`, don't symlink

**Rationale:**
- Users should be able to edit hooks
- Avoid confusion with symlinked files
- Make it obvious where hooks are

### 3. Command Installation

**Decision:** Support both installation and in-place execution

```bash
# Install for permanent use
aiterm commands install git:sync

# Run once without installing
aiterm commands run git:sync
```

### 4. MCP Server Testing

**Decision:** Test via Claude Code CLI, not direct server calls

**Rationale:**
- Tests the full integration (not just server)
- Respects settings.json configuration
- Shows real-world behavior

---

## Migration from Current Setup

### User's Existing Hooks
```bash
~/.claude/hooks/
├── prompt-optimizer.sh    # Keep (existing)
└── statusline-p10k.sh     # Keep (existing)
```

**Action:** Don't touch existing hooks, add discovery for them

### User's Existing Commands
```bash
~/.claude/commands/        # 194 files
```

**Action:**
- Scan and categorize existing commands
- Suggest cleanup (archive rarely used)
- Offer to migrate to new templates

### User's MCP Servers
```bash
~/projects/dev-tools/mcp-servers/
├── statistical-research/
├── shell/
└── project-refactor/
```

**Action:** Support existing setup, add testing/validation tools

---

## Risk Assessment

### Risk: Hook Template Complexity
**Mitigation:** Start with 5 simple templates, expand based on feedback

### Risk: Command Template Maintenance
**Mitigation:** Keep templates generic, avoid project-specific logic

### Risk: MCP Server Testing Fragility
**Mitigation:** Graceful failures, clear error messages

### Risk: Scope Creep
**Mitigation:** Defer Phase 3B if schedule slips, ship core features first

---

## Next Steps

**Immediate (Today):**
1. Review this plan with user
2. Get confirmation on Phase 3A vs 3B scope
3. Create initial directory structure

**Day 1 (Tomorrow):**
1. Implement hook discovery (`aiterm hooks list`)
2. Create 3 hook templates (session-start, prompt-optimizer, cost-tracker)
3. Test installation flow

**Week 1 Goal:**
- Hook management working
- Command templates working
- Basic documentation updated

**Week 2 Goal:**
- MCP integration working
- Comprehensive testing
- Ready for v0.2.0-dev release

---

## Questions for User

1. **Scope:** Phase 3A only, or include Phase 3B (doc helpers)?
2. **Priority:** Hooks > Commands > MCP, or different order?
3. **Templates:** What hooks/commands are most useful? (based on your workflow)
4. **Timeline:** 2 weeks acceptable, or need faster/slower?
5. **Testing:** Manual testing sufficient, or need automated integration tests?

---

## Summary

**Phase 3 Recommendation: Focus on Core Features (3A)**

Instead of experimental AI documentation, build practical tools:
- ✅ Hook management (discover, install, validate, test)
- ✅ Command templates (browse, install, run)
- ✅ MCP integration (list, test, validate)

**Timeline:** 2 weeks
**User Value:** High (solves real pain points)
**Risk:** Low (proven patterns)

**Optional Phase 3B:** Simple doc helpers (link validation, example testing)

**Deferred to Phase 4:** Full AI documentation automation (once we validate the need)

---

**Ready to start Phase 3A implementation?**
