# Craft Plugin Enhancement Proposals (FINAL)

**Generated:** 2025-12-26
**Status:** APPROVED - Ready for Implementation
**Context:** aiterm v0.4.0 + craft v1.3.0 integration

---

## Executive Summary

**Decision:** Implement craft v1.3.0 with comprehensive documentation system and CLI testing.

### Approved Components

| Component | Type | Status |
|-----------|------|--------|
| Port documentation-generation | 5 agents + 3 skills | APPROVED |
| Shell test commands | `cli-gen` + `cli-run` | APPROVED |
| Streamline docs system | Option A (Merge & Enhance) | APPROVED |

---

## craft v1.3.0 Specification

### Final Stats

| Metric | v1.2.0 | v1.3.0 | Change |
|--------|--------|--------|--------|
| Commands | 46 | 50 | +4 |
| Agents | 1 | 6 | +5 |
| Skills | 8 | 11 | +3 |

### New Commands (4)

| Command | Description | Uses |
|---------|-------------|------|
| `/craft:docs:generate` | Full documentation generation | All 5 agents |
| `/craft:docs:api` | OpenAPI/Swagger generation | api-documenter + openapi-spec skill |
| `/craft:test:cli-gen` | Generate CLI test suites | cli-test-strategist skill |
| `/craft:test:cli-run` | Run CLI test suites | - |

### New Agents (5)

| Agent | Purpose |
|-------|---------|
| `docs-architect` | Long-form technical docs (10-100+ pages) |
| `tutorial-engineer` | Step-by-step tutorials |
| `api-documenter` | OpenAPI/Swagger documentation |
| `reference-builder` | Complete technical references |
| `mermaid-expert` | Diagrams (flow, sequence, ERD) |

### New Skills (3)

| Skill | Enhances |
|-------|----------|
| `changelog-automation` | `/craft:docs:changelog` |
| `architecture-decision-records` | ADR generation |
| `openapi-spec-generation` | `/craft:docs:api` |

---

## Implementation Plan

### Directory Structure

```
/Users/dt/projects/dev-tools/claude-plugins/craft/
├── commands/
│   ├── docs/
│   │   ├── sync.md           # Existing
│   │   ├── changelog.md      # Existing (enhanced)
│   │   ├── claude-md.md      # Existing (enhanced)
│   │   ├── validate.md       # Existing
│   │   ├── nav-update.md     # Existing
│   │   ├── generate.md       # NEW
│   │   └── api.md            # NEW
│   └── test/
│       ├── run.md            # Existing
│       ├── coverage.md       # Existing
│       ├── debug.md          # Existing
│       ├── watch.md          # Existing
│       ├── cli-gen.md        # NEW
│       └── cli-run.md        # NEW
├── agents/
│   ├── orchestrator.md       # Existing
│   └── docs/                  # NEW directory
│       ├── docs-architect.md
│       ├── tutorial-engineer.md
│       ├── api-documenter.md
│       ├── reference-builder.md
│       └── mermaid-expert.md
├── skills/
│   ├── design/               # Existing
│   ├── testing/
│   │   ├── test-strategist.md     # Existing
│   │   └── cli-test-strategist.md # NEW
│   └── docs/                  # NEW directory
│       ├── changelog-automation.md
│       ├── architecture-decision-records.md
│       └── openapi-spec-generation.md
└── README.md                  # Update for v1.3.0
```

### Implementation Timeline

| Day | Tasks | Files |
|-----|-------|-------|
| 1 | Port 5 documentation agents | `agents/docs/*.md` |
| 2 | Port 3 documentation skills | `skills/docs/*.md` |
| 3 | Create docs:generate + docs:api | `commands/docs/generate.md`, `api.md` |
| 4 | Create cli-gen + cli-run | `commands/test/cli-gen.md`, `cli-run.md` |
| 5 | Update README + testing | `README.md`, validation |

---

## Command Specifications

### /craft:docs:generate

```bash
# Usage
/craft:docs:generate                    # Full documentation
/craft:docs:generate tutorial           # Create tutorial
/craft:docs:generate architecture       # Create arch docs
/craft:docs:generate reference          # Create reference docs
/craft:docs:generate diagram            # Create Mermaid diagrams
/craft:docs:generate adr                # Create ADR

# Options
--output <dir>      # Output directory (default: docs/)
--format <fmt>      # Output format: markdown|html
```

### /craft:docs:api

```bash
# Usage
/craft:docs:api                         # Generate OpenAPI spec
/craft:docs:api --interactive           # With Swagger UI setup
/craft:docs:api --output openapi.yaml   # Custom output path

# Options
--version <ver>     # API version (default: from package)
--title <title>     # API title
--format yaml|json  # Output format
```

### /craft:test:cli-gen

```bash
# Usage
/craft:test:cli-gen interactive "app-name"  # Interactive test suite
/craft:test:cli-gen automated "app-name"    # Automated test suite

# Options
--output <dir>      # Output directory (default: tests/)
--framework zsh|bash  # Shell framework
```

### /craft:test:cli-run

```bash
# Usage
/craft:test:cli-run                     # Auto-detect and run
/craft:test:cli-run interactive         # Run interactive mode
/craft:test:cli-run automated           # Run CI mode (exit 0/1)

# Options
--verbose           # Detailed output
--log <file>        # Log file path
```

---

## Source Files for Porting

### From documentation-generation@1.2.1

```
~/.claude/plugins/cache/claude-code-workflows/documentation-generation/1.2.1/
├── agents/
│   ├── docs-architect.md          → craft/agents/docs/
│   ├── tutorial-engineer.md       → craft/agents/docs/
│   ├── api-documenter.md          → craft/agents/docs/
│   ├── reference-builder.md       → craft/agents/docs/
│   └── mermaid-expert.md          → craft/agents/docs/
├── skills/
│   ├── changelog-automation/SKILL.md    → craft/skills/docs/
│   ├── architecture-decision-records/   → craft/skills/docs/
│   └── openapi-spec-generation/         → craft/skills/docs/
└── commands/
    └── doc-generate.md            → craft/commands/docs/generate.md
```

---

## Relationship with aiterm v0.4.0

craft v1.3.0 enables aiterm workflow recipes:

```yaml
# Example recipe using craft v1.3.0
name: release
steps:
  - name: docs
    type: craft
    command: /craft:docs:generate

  - name: api
    type: craft
    command: /craft:docs:api

  - name: validate
    type: craft
    command: /craft:docs:validate

  - name: changelog
    type: craft
    command: /craft:docs:changelog
```

---

## Success Criteria

- [ ] All 5 agents ported and functional
- [ ] All 3 skills ported and auto-activating
- [ ] `docs:generate` routes to correct agents
- [ ] `docs:api` generates valid OpenAPI specs
- [ ] `cli-gen` produces working test suites
- [ ] `cli-run` executes tests correctly
- [ ] README updated with v1.3.0 commands
- [ ] No regressions in existing commands

---

**Ready for Implementation**
