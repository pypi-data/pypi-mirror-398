# Release Notes: v0.2.0-dev

**Release Date:** 2025-12-24
**Status:** Development Release
**Focus:** Core Features (Phase 3A Complete)

---

## Overview

v0.2.0-dev is a major feature release that adds four complete systems to aiterm:
- Hook Management
- Command Library
- MCP Server Management
- Documentation Validation

This release represents the completion of Phase 3A and sets the foundation for aiterm as a comprehensive Claude Code enhancement platform.

---

## What's New

### 🪝 Hook Management System

Discover, install, and manage Claude Code hooks with ease.

**Commands:**
```bash
aiterm hooks list                    # List installed hooks
aiterm hooks install <template>      # Install hook from template
aiterm hooks validate                # Validate hook configurations
aiterm hooks test <hook>             # Test hook execution
aiterm hooks uninstall <hook>        # Remove installed hook
```

**Included Templates:**
- `session-logger` - Log Claude Code sessions
- `cost-tracker` - Track API costs
- `tool-validator` - Validate dangerous operations
- `context-switcher` - Auto-apply aiterm context
- `git-safety` - Protect main/master branches

**Benefits:**
- Easy hook discovery
- Production-ready templates
- Validation and testing built-in
- Reduces barrier to using Claude Code hooks

---

### 📚 Command Template Library

Browse and install reusable command templates.

**Commands:**
```bash
aiterm commands list                 # List installed commands
aiterm commands browse               # Browse templates by category
aiterm commands install <category>:<name>  # Install command
aiterm commands validate             # Validate configurations
aiterm commands uninstall <name>     # Remove command
```

**Included Templates:**
- **git/sync** - Smart git sync with safety checks
- **git/pr** - Create GitHub PR with template
- **git/clean** - Clean merged branches safely
- **testing/watch** - Run tests in watch mode
- **docs/check** - Validate documentation quality

**Benefits:**
- Reusable workflow automation
- Category-based organization
- Beautiful tree view browsing
- Easy installation and validation

---

### 📡 MCP Server Management

Manage Model Context Protocol servers for Claude Code.

**Commands:**
```bash
aiterm mcp list                      # List all configured servers
aiterm mcp test <server>             # Test specific server
aiterm mcp test-all                  # Health check all servers
aiterm mcp validate                  # Validate configuration
aiterm mcp info <server>             # Show server details
```

**Features:**
- Automatic server discovery from settings.json
- Reachability testing
- Configuration validation
- Detailed server information
- Sensitive data masking (API keys, tokens)

**Benefits:**
- Easy server discovery and testing
- Configuration troubleshooting
- Health monitoring
- Security (masked sensitive data)

---

### 📝 Documentation Validation System

Validate documentation quality with comprehensive checks.

**Commands:**
```bash
aiterm docs stats                    # Show documentation statistics
aiterm docs validate-links           # Check all markdown links
aiterm docs test-examples            # Validate code examples
aiterm docs validate-all             # Run all checks
```

**Features:**
- Link validation (internal + external)
- Anchor reference checking
- Code example syntax validation (Python, Bash)
- Documentation statistics
- CI/CD friendly exit codes

**Real-World Testing:**
- Found 35 real issues in aiterm docs
- 6 broken links discovered
- 29 invalid code examples found
- Validates tool's practical value

**Benefits:**
- Automated documentation quality checks
- CI/CD pipeline integration
- Prevents broken links
- Ensures code examples work

---

## Installation

### Homebrew (macOS - Recommended)

```bash
brew install data-wise/tap/aiterm
```

### UV (All Platforms - Fastest)

```bash
uv tool install git+https://github.com/Data-Wise/aiterm
```

### pipx (All Platforms)

```bash
pipx install git+https://github.com/Data-Wise/aiterm
```

---

## Upgrade from v0.1.0

All existing v0.1.0 features continue to work:

```bash
# Existing commands still work
aiterm doctor
aiterm detect
aiterm switch
aiterm claude settings
```

**New in v0.2.0-dev:**
```bash
# New command groups
aiterm hooks <command>
aiterm commands <command>
aiterm mcp <command>
aiterm docs <command>
```

No breaking changes - all v0.1.0 features are preserved.

---

## Documentation

### New Documentation

- **MCP-INTEGRATION.md** (597 lines)
  - Complete MCP management guide
  - 13 code examples
  - Troubleshooting section

- **DOCS-HELPERS.md** (647 lines)
  - Documentation validation guide
  - 11 comprehensive sections
  - Python API examples

- **PHASE-3A-COMPLETE.md**
  - Complete Phase 3A summary
  - Code statistics
  - Lessons learned

### Updated Documentation

- **CLAUDE.md** - Updated with Phase 3A features
- **.STATUS** - Current progress tracking
- **CHANGELOG.md** - All Phase 3A commits documented

---

## Testing

### Integration Tests

- **29 integration tests** (100% passing)
- Tests all Phase 3A features
- CLI workflow validation
- Error handling verification
- Performance testing

### Manual Testing

- All commands tested with real data
- MCP integration tested with 5 servers
- Documentation validation found 35 real issues
- Hook templates tested for execution
- Command templates validated

---

## Performance

### Benchmarks

**Documentation Validation:**
- Internal links: ~3 seconds for 200+ links
- Code examples: ~2 seconds for 500+ examples
- Total validation: ~5 seconds

**MCP Server Testing:**
- Single server: <1 second
- All servers: ~3-5 seconds

**Hook/Command Operations:**
- List: <1 second
- Install: <1 second
- Validate: <1 second

All operations complete in under 10 seconds.

---

## Code Statistics

### Production Code

- Hook Management: 580 lines
- Command Library: 600 lines
- MCP Integration: 513 lines
- Documentation Helpers: 715 lines
- Integration Tests: 265 lines
- **Total: 2,673 lines**

### Documentation

- User guides: 1,244 lines
- Templates: 542 lines
- Completion summaries: 799 lines
- **Total: 2,585 lines**

### Tests

- Integration tests: 29 (100% passing)
- Test coverage: Comprehensive
- All features validated

---

## Breaking Changes

**None** - This is a feature-additive release.

All v0.1.0 functionality is preserved and working.

---

## Known Issues

### Documentation Validation

- Some intentionally incomplete code examples will fail validation
  - **Workaround:** Use `text` language for non-executable snippets
  - See DOCS-HELPERS.md troubleshooting section

### MCP Testing

- External link checking is slow (10-30 seconds)
  - **Expected:** Network requests for each URL
  - **Recommendation:** Use `--external` flag sparingly

### Hook Templates

- Templates assume bash/zsh shell
  - **Limitation:** Windows compatibility not yet tested
  - **Future:** Cross-platform templates planned

---

## Migration Guide

### From v0.1.0

No migration needed - v0.2.0-dev is fully backward compatible.

**Optional:** Start using new features:

```bash
# Explore new commands
aiterm hooks list
aiterm commands browse
aiterm mcp list
aiterm docs stats
```

---

## Contributing

We welcome contributions! Phase 3A establishes patterns for:

- Hook templates (`templates/hooks/`)
- Command templates (`templates/commands/`)
- Documentation validation
- Integration testing

See `CONTRIBUTING.md` for guidelines.

---

## Acknowledgments

Built with:
- **Typer** - Modern CLI framework
- **Rich** - Beautiful terminal output
- **pytest** - Comprehensive testing

Special thanks to:
- Claude Code team for hooks and MCP infrastructure
- Open source community for tool inspiration

---

## What's Next

### v0.2.0 (Stable Release)

- Additional hook templates
- More command templates
- Performance optimizations
- Windows compatibility testing

### v0.3.0 (Future)

- StatusLine builder (interactive)
- Terminal backend expansion (Wezterm, Alacritty)
- Advanced MCP features
- Command marketplace
- Plugin system

---

## Support

- **Documentation:** https://Data-Wise.github.io/aiterm/
- **Issues:** https://github.com/Data-Wise/aiterm/issues
- **Repository:** https://github.com/Data-Wise/aiterm

---

## Changelog

See `CHANGELOG.md` for detailed commit history.

**Highlights:**
- 14 commits for Phase 3A
- 4 complete feature systems
- 2,673 lines of production code
- 29 integration tests
- 100% feature completeness

---

**Version:** v0.2.0-dev
**Release Date:** 2025-12-24
**Status:** Development Release - Ready for Testing
