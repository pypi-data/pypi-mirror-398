# aiterm Documentation Index

**Version:** 0.1.0-dev
**Last Updated:** 2025-12-21

---

## 📚 Complete Documentation Suite

This index provides access to all aiterm documentation.

---

## Quick Start

**New to aiterm?** Start here:

1. **[User Guide](guides/AITERM-USER-GUIDE.md)** - Learn how to use aiterm (15 min read)
2. **[Installation](guides/AITERM-USER-GUIDE.md#installation)** - Get aiterm installed (< 5 min)
3. **[First-Time Setup](guides/AITERM-USER-GUIDE.md#first-time-setup)** - Configure aiterm (4 steps)

---

## Documentation by Audience

### For Users

**Goal:** Use aiterm effectively

📖 **Start Here:**
- [User Guide](guides/AITERM-USER-GUIDE.md) - Complete walkthrough with examples
- [Implementation Summary](AITERM-IMPLEMENTATION-SUMMARY.md) - What aiterm does

🛠️ **When You Need Help:**
- [Troubleshooting Guide](troubleshooting/AITERM-TROUBLESHOOTING.md) - Solve common issues
- [FAQ](guides/AITERM-USER-GUIDE.md#faq) - Quick answers

---

### For Developers

**Goal:** Integrate aiterm or extend functionality

🏗️ **Architecture:**
- [Architecture Documentation](architecture/AITERM-ARCHITECTURE.md) - System design & diagrams
- [API Documentation](api/AITERM-API.md) - Complete API reference

💻 **Integration:**
- [Integration Guide](guides/AITERM-INTEGRATION.md) - Code examples & patterns
- [Python API](api/AITERM-API.md#python-api) - Library usage

🧪 **Testing:**
- [Testing Your Integration](guides/AITERM-INTEGRATION.md#testing-your-integration) - Test patterns
- [Implementation Summary](AITERM-IMPLEMENTATION-SUMMARY.md#test-coverage) - Coverage details

---

### For Contributors

**Goal:** Contribute to aiterm

📋 **Planning:**
- [Implementation Summary](AITERM-IMPLEMENTATION-SUMMARY.md) - What was built & why
- [Architecture Documentation](architecture/AITERM-ARCHITECTURE.md) - Design patterns
- [Roadmap](AITERM-IMPLEMENTATION-SUMMARY.md#roadmap) - Future plans

🔧 **Development:**
- [Integration Guide](guides/AITERM-INTEGRATION.md) - Best practices
- [API Documentation](api/AITERM-API.md) - API reference

✅ **Standards:**
- [Performance Metrics](AITERM-IMPLEMENTATION-SUMMARY.md#performance-metrics) - Targets
- [Design Patterns](architecture/AITERM-ARCHITECTURE.md#design-patterns) - Patterns used

---

## Documentation by Type

### Reference Documentation

**Complete technical references**

| Document | Purpose | Audience |
|----------|---------|----------|
| [API Documentation](api/AITERM-API.md) | CLI commands & Python API | Developers |
| [Architecture](architecture/AITERM-ARCHITECTURE.md) | System design & diagrams | Developers/Contributors |

---

### Guides

**Step-by-step walkthroughs**

| Document | Purpose | Audience |
|----------|---------|----------|
| [User Guide](guides/AITERM-USER-GUIDE.md) | How to use aiterm | Users |
| [Integration Guide](guides/AITERM-INTEGRATION.md) | How to integrate/extend | Developers |

---

### Reports

**Implementation & analysis**

| Document | Purpose | Audience |
|----------|---------|----------|
| [Implementation Summary](AITERM-IMPLEMENTATION-SUMMARY.md) | What was built | All |
| [Troubleshooting](troubleshooting/AITERM-TROUBLESHOOTING.md) | Problem solving | All |

---

## Documentation by Feature

### Core Features

**Automatic Context Detection**

- **Overview:** [User Guide - Context Types](guides/AITERM-USER-GUIDE.md#context-types)
- **API:** [detect_context()](api/AITERM-API.md#detect_context)
- **Architecture:** [Context Detection Architecture](architecture/AITERM-ARCHITECTURE.md#2-context-detection-architecture)
- **Integration:** [Creating Custom Detectors](guides/AITERM-INTEGRATION.md#creating-custom-context-detectors)

---

**Profile Management**

- **Overview:** [User Guide - Profile Switching](guides/AITERM-USER-GUIDE.md#workflow-5-switching-between-projects)
- **API:** [profile commands](api/AITERM-API.md#profile-management)
- **Architecture:** [Profile Switching Flow](architecture/AITERM-ARCHITECTURE.md#3-profile-switching-flow)
- **Troubleshooting:** [Profile Issues](troubleshooting/AITERM-TROUBLESHOOTING.md#profile-switching-issues)

---

**Claude Code Integration**

- **Overview:** [User Guide - Auto-Approvals](guides/AITERM-USER-GUIDE.md#claude-code-auto-approval-presets)
- **API:** [claude commands](api/AITERM-API.md#claude-code-integration)
- **Architecture:** [Auto-Approval Flow](architecture/AITERM-ARCHITECTURE.md#2-auto-approval-application-flow)
- **Troubleshooting:** [Claude Issues](troubleshooting/AITERM-TROUBLESHOOTING.md#claude-code-integration-issues)

---

**Terminal Backends**

- **Overview:** [User Guide - Terminal Compatibility](guides/AITERM-USER-GUIDE.md#faq)
- **API:** [Terminal API](api/AITERM-API.md#terminal-backends)
- **Architecture:** [Terminal Backend Architecture](architecture/AITERM-ARCHITECTURE.md#1-terminal-backend-architecture)
- **Integration:** [Adding New Backends](guides/AITERM-INTEGRATION.md#adding-new-terminal-backends)

---

## Documentation by Task

### I want to...

#### ...install aiterm

→ [Installation Guide](guides/AITERM-USER-GUIDE.md#installation)

**Quick:** `uv pip install git+https://github.com/Data-Wise/aiterm.git`

---

#### ...understand how aiterm works

→ [Architecture Documentation](architecture/AITERM-ARCHITECTURE.md)

**Quick:** [System Overview](architecture/AITERM-ARCHITECTURE.md#system-overview)

---

#### ...use aiterm daily

→ [User Guide - Daily Workflows](guides/AITERM-USER-GUIDE.md#daily-workflows)

**Quick:** Just `cd` to your project - aiterm handles the rest!

---

#### ...create a custom context detector

→ [Integration Guide - Custom Detectors](guides/AITERM-INTEGRATION.md#creating-custom-context-detectors)

**Quick:** Inherit from `ContextDetector`, implement `detect()`

---

#### ...add a new terminal backend

→ [Integration Guide - Terminal Backends](guides/AITERM-INTEGRATION.md#adding-new-terminal-backends)

**Quick:** Inherit from `TerminalBackend`, implement abstract methods

---

#### ...fix a problem

→ [Troubleshooting Guide](troubleshooting/AITERM-TROUBLESHOOTING.md)

**Quick:** [Quick Diagnosis](troubleshooting/AITERM-TROUBLESHOOTING.md#quick-diagnosis)

---

#### ...see performance metrics

→ [Implementation Summary - Performance](AITERM-IMPLEMENTATION-SUMMARY.md#performance-metrics)

**Quick:** All operations < 200ms, most < 100ms

---

#### ...understand design decisions

→ [Implementation Summary - Architecture Decisions](AITERM-IMPLEMENTATION-SUMMARY.md#architecture-decisions)

**Quick:** Python, UV, iTerm2-first, Documentation-first

---

#### ...contribute to aiterm

→ [Implementation Summary - Roadmap](AITERM-IMPLEMENTATION-SUMMARY.md#roadmap)

**Quick:** Check Phase 2 planned features

---

## Quick Reference

### Key Commands

```bash
# Installation
uv pip install git+https://github.com/Data-Wise/aiterm.git

# Verification
aiterm doctor

# Context detection
aiterm detect

# Profile management
aiterm profile list
aiterm profile switch PROFILE

# Claude Code integration
aiterm claude approvals list
aiterm claude approvals set PRESET
aiterm claude settings show
```

---

### Key Files

| File/Directory | Description |
|----------------|-------------|
| `~/.aiterm/config.json` | aiterm configuration |
| `~/.claude/settings.json` | Claude Code settings |
| `~/.claude/settings.json.backup.*` | Automatic backups |
| `src/aiterm/` | Main package source |
| `docs/` | Documentation |

---

### Key Concepts

| Concept | Description | Document |
|---------|-------------|----------|
| Context | Project type detection | [API - Context](api/AITERM-API.md#context-detection) |
| Profile | Terminal visual theme | [User Guide - Profiles](guides/AITERM-USER-GUIDE.md#step-3-explore-available-profiles) |
| Detector | Context detection strategy | [Integration - Detectors](guides/AITERM-INTEGRATION.md#creating-custom-context-detectors) |
| Backend | Terminal integration | [Integration - Backends](guides/AITERM-INTEGRATION.md#adding-new-terminal-backends) |
| Preset | Auto-approval collection | [User Guide - Presets](guides/AITERM-USER-GUIDE.md#claude-code-auto-approval-presets) |
| Priority | Detector precedence | [Architecture - Chain](architecture/AITERM-ARCHITECTURE.md#4-chain-of-responsibility) |

---

### Performance Targets

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Context detection | < 50ms | ~30ms | ✅ |
| Profile switching | < 150ms | ~100ms | ✅ |
| Settings read | < 10ms | ~5ms | ✅ |
| Settings write | < 50ms | ~40ms | ✅ |
| Total overhead | < 200ms | ~130ms | ✅ |

See [Implementation Summary - Performance](AITERM-IMPLEMENTATION-SUMMARY.md#performance-metrics)

---

### Context Types (Priority Order)

| Priority | Type | Detection | Profile |
|----------|------|-----------|---------|
| 1 | Production | `*/production/*` or `*/prod/*` | Production |
| 2 | AI Session | `*/claude-sessions/*` or `*/gemini-sessions/*` | AI-Session |
| 3 | R Package | `DESCRIPTION` + `R/` | R-Dev |
| 4 | Python | `pyproject.toml` or `setup.py` | Python-Dev |
| 5 | Node.js | `package.json` | Node-Dev |
| 6 | Quarto | `_quarto.yml` | R-Dev |
| 7 | MCP Server | `mcp-server/` directory | AI-Session |
| 8 | Dev Tools | `.git/` + `scripts/` | Dev-Tools |
| 9 | Default | (no match) | Default |

See [User Guide - Context Types](guides/AITERM-USER-GUIDE.md#context-types)

---

### Auto-Approval Presets

| Preset | Tools | Use Case |
|--------|-------|----------|
| `minimal` | 15 | Essential operations only |
| `development` | 45 | Full development workflow |
| `production` | 20 | Production-safe (read-only) |
| `r-package` | 35 | R package development |
| `python-dev` | 40 | Python development |
| `teaching` | 30 | Teaching/course development |
| `research` | 35 | Research/manuscript writing |
| `ai-session` | 50 | AI coding sessions (broadest) |

See [User Guide - Presets](guides/AITERM-USER-GUIDE.md#claude-code-auto-approval-presets)

---

## Documentation Statistics

### Coverage

- **Total Documents:** 7
- **Total Lines:** 3,600+
- **Code Examples:** 80+
- **Mermaid Diagrams:** 16
- **Audience Coverage:** Users, Developers, Contributors

### By Type

| Type | Count | Lines |
|------|-------|-------|
| API Reference | 1 | ~520 |
| Architecture | 1 | ~680 |
| User Guides | 2 | ~1,400 |
| Integration | 1 | ~600 |
| Troubleshooting | 1 | ~550 |
| Reports | 1 | ~450 |
| Index | 1 | ~200 |

### By Feature

| Feature | Docs | Examples | Diagrams |
|---------|------|----------|----------|
| Context Detection | All | 15+ | 5 |
| Profile Management | All | 10+ | 4 |
| Claude Integration | 5 | 8+ | 2 |
| Terminal Backends | 4 | 20+ | 3 |
| Custom Extensions | 2 | 25+ | 2 |

---

## Documentation Standards

All documentation follows these standards:

✅ **Clarity:** Written for target audience
✅ **Completeness:** Covers all features
✅ **Examples:** Real code examples
✅ **Diagrams:** Visual aids (Mermaid)
✅ **Navigation:** Clear table of contents
✅ **Cross-linking:** Links between docs
✅ **Up-to-date:** Reflects current implementation
✅ **ADHD-friendly:** Clear hierarchies, progressive disclosure

---

## Contributing to Documentation

### How to Update Documentation

1. **Identify document** to update (see index above)
2. **Edit markdown file** in appropriate directory
3. **Update last modified date**
4. **Test code examples** (if applicable)
5. **Update cross-links** (if structure changed)
6. **Update this index** (if new document added)

### Documentation Structure

```
docs/
├── api/
│   └── AITERM-API.md                    # API reference
├── architecture/
│   └── AITERM-ARCHITECTURE.md           # System design
├── guides/
│   ├── AITERM-USER-GUIDE.md             # User guide
│   └── AITERM-INTEGRATION.md            # Developer guide
├── troubleshooting/
│   └── AITERM-TROUBLESHOOTING.md        # Troubleshooting
├── AITERM-IMPLEMENTATION-SUMMARY.md     # Implementation summary
└── AITERM-DOCS-INDEX.md                 # This file
```

### Adding New Documentation

**When adding a new document:**

1. Create file in appropriate directory
2. Follow existing format (see templates)
3. Add to this index:
   - Table of contents
   - By audience section
   - By type section
   - By feature section (if applicable)
4. Add cross-links from related docs
5. Update statistics

---

## Version History

### v0.1.0-dev (2025-12-21) - Phase 0 Documentation

**Documentation Created:**
- ✅ API Documentation (520+ lines)
- ✅ Architecture Documentation (680+ lines)
- ✅ User Guide (800+ lines)
- ✅ Integration Guide (600+ lines)
- ✅ Troubleshooting Guide (550+ lines)
- ✅ Implementation Summary (450+ lines)
- ✅ Documentation Index (200+ lines)

**Statistics:**
- 7 documents
- 3,800+ lines
- 80+ code examples
- 16 diagrams

**Milestone:** Comprehensive documentation BEFORE Phase 1 implementation

---

### v0.1.0 (2024-12-18) - Initial Release

**Documentation Created:**
- ✅ Basic README
- ✅ CLI help text
- ✅ Initial MkDocs site (deployed)

**Statistics:**
- ~2,600 lines
- Basic coverage

---

## External Resources

### Official Links

- **GitHub Repository:** https://github.com/Data-Wise/aiterm
- **Documentation Site:** https://Data-Wise.github.io/aiterm/
- **Issue Tracker:** https://github.com/Data-Wise/aiterm/issues
- **Discussions:** https://github.com/Data-Wise/aiterm/discussions

### Related Projects

- **Claude Code:** https://code.claude.com
- **iTerm2:** https://iterm2.com
- **UV Package Manager:** https://github.com/astral-sh/uv
- **Typer:** https://typer.tiangolo.com
- **Rich:** https://rich.readthedocs.io

### Community

- **PyPI:** (pending publication)
- **Awesome Lists:** (pending submission)

---

## Feedback

Found an issue with documentation? Have a suggestion?

- **Documentation Issues:** https://github.com/Data-Wise/aiterm/issues (label: documentation)
- **General Feedback:** https://github.com/Data-Wise/aiterm/discussions
- **Feature Requests:** https://github.com/Data-Wise/aiterm/issues (label: enhancement)

---

## License

Documentation licensed under MIT License - See LICENSE file for details.

Code licensed under MIT License - See LICENSE file for details.

---

## Search Tips

**Finding information:**

1. **Use browser search (Cmd+F / Ctrl+F):**
   - Search for command names (e.g., "aiterm detect")
   - Search for concepts (e.g., "context detection")
   - Search for error messages

2. **Use this index:**
   - Browse by audience (User, Developer, Contributor)
   - Browse by feature (Context, Profiles, Claude, etc.)
   - Browse by task ("I want to...")

3. **GitHub search:**
   - Search across all docs
   - Filter by file type (.md)
   - Search code examples

---

## Next Steps

### For New Users

1. Read [User Guide](guides/AITERM-USER-GUIDE.md)
2. Follow [Installation](guides/AITERM-USER-GUIDE.md#installation)
3. Complete [First-Time Setup](guides/AITERM-USER-GUIDE.md#first-time-setup)
4. Try [Daily Workflows](guides/AITERM-USER-GUIDE.md#daily-workflows)

### For Developers

1. Read [Architecture](architecture/AITERM-ARCHITECTURE.md)
2. Review [API Documentation](api/AITERM-API.md)
3. Explore [Integration Guide](guides/AITERM-INTEGRATION.md)
4. Check [Roadmap](AITERM-IMPLEMENTATION-SUMMARY.md#roadmap)

### For Contributors

1. Read [Implementation Summary](AITERM-IMPLEMENTATION-SUMMARY.md)
2. Review [Architecture](architecture/AITERM-ARCHITECTURE.md)
3. Check [Roadmap](AITERM-IMPLEMENTATION-SUMMARY.md#roadmap)
4. Browse [GitHub Issues](https://github.com/Data-Wise/aiterm/issues)

---

**Last Updated:** 2025-12-21
**Maintained By:** aiterm Development Team
**Documentation Version:** Phase 0 Complete

**Total Documentation:** 3,800+ lines | 80+ examples | 16 diagrams | 7 documents
