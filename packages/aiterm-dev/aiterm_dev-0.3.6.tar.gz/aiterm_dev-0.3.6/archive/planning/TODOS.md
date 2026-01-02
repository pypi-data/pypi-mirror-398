# TODOS - aiterm

Tasks and next steps for the aiterm project.

**Updated:** 2025-12-19
**Version:** 0.1.0 (Released) → 0.2.0-dev (R-Development MCP Consolidation)

---

## CURRENT FOCUS: R-Development MCP Consolidation ⭐

**Discovery:** 59% of Claude CLI commands (35/59) are R-ecosystem related!

**Phase 1: Quick Wins (Week 1)**
- [ ] Backup ~/.claude/commands/
- [ ] Archive 6 meta documents
- [ ] Deprecate 4 github commands (use github plugin)
- [ ] Deprecate 3 git commands (use commit-commands plugin)
- [ ] Update git.md, github.md hubs
- [ ] Result: 59 → 46 files (-22%)

**Phase 2: R-Development MCP (Week 2-3)** ⭐ HIGH VALUE
- [ ] Rename statistical-research → r-development MCP
- [ ] Update ~/.claude/settings.json
- [ ] Implement r_ecosystem_health tool
- [ ] Implement r_package_check_quick tool
- [ ] Implement manuscript_section_writer tool
- [ ] Implement reviewer_response_generator tool
- [ ] Implement pkgdown_build tool
- [ ] Implement pkgdown_deploy tool
- [ ] Test all tools with MediationVerse packages
- [ ] Deprecate 2 code commands (ecosystem-health, rpkg-check)
- [ ] Deprecate 8 research commands
- [ ] Update code.md, research.md, site.md hubs
- [ ] Result: 46 → 36 files (-39%), r-development MCP: 20 tools

**Phase 3: Teaching MCP (Week 4-5)**
- [ ] Create teaching-toolkit MCP server
- [ ] Implement 10 teaching tools + SQLite question bank
- [ ] Canvas API integration
- [ ] Deprecate 9 teach commands
- [ ] Result: 36 → 27 files

**See:** COMMAND-MCP-REFACTORING-ANALYSIS-REVISED.md, REFACTORING-ACTION-PLAN-REVISED.md

---

## Immediate (v0.1.0 - COMPLETE ✅)

- [x] ✅ Create PR: `claude/recap-dev-main-branches-3eCZB` → `dev`
- [x] ✅ Review and merge PR
- [x] ✅ Tag v0.1.0 release

---

## v0.1.1 (Bug Fixes & Polish)

- [ ] Implement full `aiterm init` wizard (currently placeholder)
- [ ] Add more detailed `aiterm doctor` diagnostics
- [ ] Add `aiterm profile install` command
- [ ] Add `aiterm profile test` command
- [ ] Shell integration script for zsh/bash

---

## v0.2.0 (R-Development MCP + MCP Creation Tools) ⭐

**PRIORITY: MCP Creation Wizard**
- [ ] `aiterm mcp create` - Interactive MCP server creation wizard
- [ ] `aiterm mcp templates list` - Show available templates
- [ ] `aiterm mcp validate <server>` - Validate MCP structure
- [ ] Template library (10+ templates: simple-api, research-tools, r-package-dev, etc.)
- [ ] Interactive web tutorial for MCP creation

**MCP Management:**
- [ ] `aiterm mcp list` - Show configured MCP servers with status
- [ ] `aiterm mcp install <server>` - Install + configure
- [ ] `aiterm mcp test <server>` - Test connection and tools
- [ ] `aiterm mcp recommend` - Suggest based on project type

**Hook Management (Lower Priority):**
- [ ] `aiterm claude hooks list` - Show available hooks
- [ ] `aiterm claude hooks install <name>` - Install from template
- [ ] `aiterm claude hooks create <name>` - Interactive hook creator
- [ ] `aiterm claude hooks validate` - Check hook syntax

---

## v0.3.0 (Plugin & Agent Creation)

- [ ] `aiterm plugin create` - Interactive plugin creation wizard
- [ ] `aiterm plugin validate` - Check plugin.json structure
- [ ] `aiterm agent create` - Interactive agent configuration
- [ ] `aiterm claude commands list` - Show custom commands
- [ ] `aiterm claude commands create` - From template

---

## v0.4.0 (Multi-Terminal & Gemini)

- [ ] Warp terminal support
- [ ] Alacritty support
- [ ] Kitty support
- [ ] `aiterm gemini init` - Gemini CLI integration
- [ ] `aiterm switch claude|gemini` - Switch AI tools

---

## Technical Debt

- [ ] Increase test coverage to 90%+
- [ ] Add integration tests for iTerm2
- [ ] Add type hints throughout
- [ ] Add docstrings to all functions
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Pre-commit hooks (ruff, mypy, black)

---

## Documentation

- [ ] Quickstart video tutorial
- [ ] Update MkDocs site with v0.1.0 features
- [ ] API documentation
- [ ] Contributing guide
- [ ] Recipe book (common patterns)

---

## Distribution

- [ ] Publish to PyPI
- [ ] Homebrew formula
- [ ] Docker image (optional)

---

## Community

- [ ] GitHub discussions enabled
- [ ] Issue templates
- [ ] PR template
- [ ] Example gallery

---

## Long-term Ideas (v1.0+)

See IDEAS.md for full roadmap:
- Web UI (Streamlit)
- Template marketplace
- AI workflow optimizer
- Cross-tool intelligence
- VSCode extension
