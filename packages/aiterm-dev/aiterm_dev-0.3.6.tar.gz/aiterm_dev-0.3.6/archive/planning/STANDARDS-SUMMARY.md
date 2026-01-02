# aiterm Project Standards Summary

**Generated:** 2025-12-19
**Based on:** zsh-configuration standards (~/projects/dev-tools/zsh-configuration/standards/)

> **Purpose:** This document consolidates all applicable standards from the zsh-configuration project for the aiterm project.

---

## 📋 Table of Contents

1. [Project Organization](#project-organization)
2. [Documentation Standards](#documentation-standards)
3. [Commit Message Standards](#commit-message-standards)
4. [ADHD-Friendly Practices](#adhd-friendly-practices)
5. [Testing Standards](#testing-standards)
6. [Development Workflow](#development-workflow)

---

## Project Organization

### Universal Files (Required)

Every project MUST have:

```
aiterm/
├── README.md          # Quick start (ADHD-friendly format)
├── .STATUS            # Machine-readable status
├── .gitignore         # Git ignores
└── CHANGELOG.md       # Version history
```

### .STATUS File Format

```yaml
status: active          # active | draft | stable | paused | archived
progress: 75            # 0-100 (optional)
next: Write discussion  # Next action item
target: v0.2.0          # Target version/milestone (optional)
updated: 2025-12-19     # Last update date
```

**Valid statuses:**

| Status | Meaning |
|--------|---------|
| `active` | Currently working on |
| `draft` | In development, not ready |
| `stable` | Production ready |
| `paused` | Temporarily stopped |
| `archived` | No longer maintained |
| `under-review` | Submitted, waiting feedback |
| `published` | Completed and released |

### Python Project Structure (aiterm-specific)

```
aiterm/
├── README.md              # Quick start
├── .STATUS                # Project status
├── CHANGELOG.md           # Version history
├── pyproject.toml         # Project metadata
├── .gitignore
│
├── src/aiterm/            # Source code
│   ├── __init__.py
│   ├── cli/               # CLI commands (Typer)
│   │   ├── main.py
│   │   ├── mcp.py         # MCP management
│   │   └── ...
│   ├── terminal/          # Terminal backends
│   ├── context/           # Context detection
│   └── utils/             # Utilities
│
├── tests/                 # Test suite (pytest)
│   ├── test_cli.py
│   └── ...
│
├── docs/                  # Documentation (MkDocs)
│   ├── tutorials/         # Step-by-step guides
│   │   ├── getting-started/
│   │   └── mcp-creation/
│   ├── ref-cards/         # Quick references (printable)
│   ├── interactive/       # Web-based tutorials
│   ├── examples/          # Real-world examples
│   └── api/               # API documentation
│
├── templates/             # User-facing templates
│   ├── mcp-servers/       # MCP server templates
│   ├── plugins/           # Plugin templates
│   └── hooks/             # Hook templates
│
└── .github/
    └── workflows/
        └── tests.yml
```

---

## Documentation Standards

### Documentation Types

| Type | Purpose | Format | Example |
|------|---------|--------|---------|
| **QUICK-START** | Get running in 30 seconds | Prose + commands | README.md |
| **GETTING-STARTED** | Learn basics in 10 minutes | Structured sections | docs/tutorials/ |
| **TUTORIAL** | Deep learning (step-by-step) | Numbered steps | docs/tutorials/ |
| **REFCARD** | Quick lookup | Tables + boxes | docs/ref-cards/ |

### QUICK-START Template (README.md)

```markdown
# [Project Name]

> **TL;DR:** [One sentence: what this does]

## 30-Second Setup

\`\`\`bash
# Clone and run
git clone [url]
cd [project]
[one command to get running]
\`\`\`

## What This Does

- [Bullet 1: Main feature]
- [Bullet 2: Secondary feature]
- [Bullet 3: Who it's for]

## Common Tasks

| I want to... | Run this |
|--------------|----------|
| Build | `pb` |
| Test | `pt` |
| Document | `pd` |

## Where Things Are

| Location | Contents |
|----------|----------|
| `src/` | Main code |
| `tests/` | Test files |
| `docs/` | Documentation |

## Current Status

See `.STATUS` file or run:
\`\`\`bash
aiterm --version
\`\`\`
```

### REFCARD Template

**Design Principles:**

1. **One page** — No scrolling (print-friendly)
2. **Scannable** — Tables and boxes, not paragraphs
3. **No explanations** — Just commands and syntax
4. **Grouped logically** — By task, not alphabetically
5. **Most-used first** — Common commands at top

**Example Structure:**

```markdown
# [Tool Name] Reference Card

> **Version:** X.X | **Last Updated:** YYYY-MM-DD

---

## Essential Commands

| Command | Description |
|---------|-------------|
| `[cmd]` | [2-4 word description] |
| `[cmd]` | [2-4 word description] |

## [Category 1]

| Command | Description |
|---------|-------------|
| `[cmd]` | [description] |

## Common Patterns

\`\`\`bash
# [Pattern name]
[command pattern]
\`\`\`

## Quick Tips

- [Tip 1]
- [Tip 2]
```

**Formatting Rules:**
- Descriptions: 2-4 words max
- Start with verb
- No articles (a, the)
- No ending punctuation
- Group by task, not alphabetically

### TUTORIAL Template

**Structure:**

```markdown
# [Tutorial Title]

> **TL;DR:** [What you'll build in one sentence]

**Prerequisites:**
- [Item 1]
- [Item 2]

**Time:** [X minutes]

---

## Step 1: [Action]

[Brief explanation]

\`\`\`bash
# Command
[command]
\`\`\`

**Expected output:**
\`\`\`
[output]
\`\`\`

## Step 2: [Action]

...

## What You Built

- [Summary point 1]
- [Summary point 2]

## Next Steps

- [Follow-up tutorial 1]
- [Follow-up tutorial 2]
```

---

## Commit Message Standards

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(mcp): add server creation wizard` |
| `fix` | Bug fix | `fix(cli): correct argument parsing` |
| `docs` | Documentation only | `docs(readme): add installation guide` |
| `style` | Formatting, no code change | `style: apply black formatting` |
| `refactor` | Code change, no new feature/fix | `refactor(utils): simplify helpers` |
| `test` | Adding/fixing tests | `test(mcp): add creation wizard tests` |
| `chore` | Build, tooling, deps | `chore(deps): update typer to 0.9` |
| `perf` | Performance improvement | `perf(detect): cache project type` |

### Scope (Optional)

For aiterm, common scopes:

| Scope | Use For |
|-------|---------|
| `mcp` | MCP server management/creation |
| `plugin` | Plugin management/creation |
| `hook` | Hook management/creation |
| `agent` | Agent management/creation |
| `terminal` | Terminal integration |
| `cli` | CLI commands |
| `docs` | Documentation |
| `tests` | Test suite |

### Subject Rules

1. **Imperative mood** — "add feature" not "added feature"
2. **No period** at the end
3. **Max 50 characters** (72 absolute max)
4. **Lowercase** first letter

```bash
# GOOD
feat(mcp): add server creation wizard
fix(terminal): handle iTerm2 profile switch
docs: update installation instructions

# BAD
feat(mcp): Added server creation wizard.   # Past tense, period
FIX: iTerm2 profile                       # Caps, unclear
updated docs                              # Past tense, no type
```

### Body (When Needed)

- Wrap at 72 characters
- Explain **why**, not what (code shows what)
- Reference issues: `Fixes #123`, `Closes #456`

```
fix(terminal): handle iTerm2 profile switch

The profile switch command failed when terminal was in fullscreen.
Now detects fullscreen mode and switches only when in windowed mode.

Fixes #42
```

### Breaking Changes

Use `!` after type or `BREAKING CHANGE:` in footer:

```
feat(mcp)!: change server config format

BREAKING CHANGE: MCP server configs now use YAML instead of JSON.
Run `aiterm mcp migrate` to convert existing configs.
```

### Claude Code Integration

When using Claude Code's `/commit` skill, the commit message should still follow these standards:

```bash
# The skill will add the Claude attribution automatically
feat(mcp): add marketplace server

Implements aiterm-mcp-marketplace server for discovering and installing
MCP servers conversationally via Claude.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## ADHD-Friendly Practices

### Core Principles

1. **Copy-paste ready** — Every guide has commands you can run
2. **TL;DR first** — Summary at the top, details below
3. **Decision trees** — "If X, do Y" not essays
4. **One source of truth** — Standards live here, nowhere else
5. **Visual hierarchy** — Headers, tables, bullets
6. **Quick wins first** — Easy tasks before hard ones
7. **Concrete next steps** — Numbered, actionable

### Writing Guidelines

**For Documentation:**
- Start with TL;DR (one sentence)
- Use tables over paragraphs
- Number sequential steps
- Include expected outputs
- Show common patterns
- Provide quick commands

**For Code:**
- Clear function names (verb + noun)
- Docstrings with examples
- Type hints everywhere
- Single responsibility per function
- Fail fast with clear errors

**For Planning:**
- Break tasks into <30 min chunks
- Use checkboxes for progress
- Include time estimates
- Show dependencies clearly
- Provide multiple paths when possible

### Documentation Structure Example

```markdown
# [Feature Name]

> **TL;DR:** [One sentence]

## Quick Wins (< 30 min each)

1. ⚡ [Action] - [One sentence benefit]
2. ⚡ [Action] - [One sentence benefit]

## Medium Effort (1-2 hours)

- [ ] [Task with clear outcome]

## Long-term (Future sessions)

- [ ] [Strategic item]

## Recommended Next Step

→ Start with #1 because [reason]
```

---

## Testing Standards

### Test Organization

```
tests/
├── test_cli.py           # CLI command tests
├── test_terminal.py      # Terminal integration tests
├── test_context.py       # Context detection tests
├── test_mcp.py           # MCP management tests
└── fixtures/             # Test data
    ├── sample_projects/
    └── sample_configs/
```

### Test Naming Convention

```python
def test_<what_youre_testing>_<scenario>_<expected_outcome>():
    """Test description."""
    pass

# Examples
def test_detect_context_r_package_returns_r_dev():
    """Detect R package returns R-Dev profile."""
    pass

def test_mcp_create_with_template_creates_server():
    """MCP create with template creates working server."""
    pass
```

### Test Structure (Arrange-Act-Assert)

```python
def test_example():
    """Test description."""
    # Arrange - Set up test data
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Act - Execute the functionality
    result = detect_context(project_path)

    # Assert - Verify the outcome
    assert result == "R-Dev"
```

### Coverage Goals

- **Minimum:** 70% overall
- **Target:** 80%+ overall
- **Critical paths:** 90%+ (MCP creation, context detection)

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aiterm --cov-report=html

# Run specific test
pytest tests/test_cli.py::test_init_command

# Run integration tests only
pytest -m integration

# Run quick tests only
pytest -m "not integration"
```

---

## Development Workflow

### Branch Strategy

```
main          Production-ready releases
  └─ dev      Active development
      └─ feature/X  Feature branches
```

**Workflow:**
1. Create feature branch from `dev`
2. Develop + test
3. PR to `dev`
4. Merge to `dev`
5. When ready: PR `dev` → `main` for release

### Development Cycle

```bash
# 1. Start new feature
git checkout dev
git pull
git checkout -b feature/mcp-creation

# 2. Develop
# ... make changes ...

# 3. Test
pytest
pytest --cov=aiterm

# 4. Format
black src/ tests/
isort src/ tests/

# 5. Commit
git add .
git commit -m "feat(mcp): add creation wizard"

# 6. Push
git push -u origin feature/mcp-creation

# 7. Create PR (via GitHub CLI)
gh pr create --base dev --title "feat(mcp): add creation wizard"
```

### Pre-commit Checklist

Before committing:

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`, `isort`)
- [ ] Type hints added (new code)
- [ ] Docstrings added (public functions)
- [ ] Commit message follows standards
- [ ] No debug code left behind

### Release Process

**For v0.X.0 releases:**

1. Update CHANGELOG.md
2. Update version in pyproject.toml
3. Update .STATUS file
4. Create PR: `dev` → `main`
5. Merge after review
6. Tag release: `git tag v0.X.0`
7. Push tag: `git push origin v0.X.0`
8. Publish to PyPI (when ready)

---

## Quick Reference Commands

### Documentation

```bash
# Create new quick-start guide
cp standards/adhd/QUICK-START-TEMPLATE.md docs/

# Create new ref-card
cp standards/adhd/REFCARD-TEMPLATE.md docs/ref-cards/

# Create new tutorial
cp standards/adhd/TUTORIAL-TEMPLATE.md docs/tutorials/
```

### Testing

```bash
# Run tests
pytest

# Coverage report
pytest --cov=aiterm --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

### Git Workflow

```bash
# Quick commit
git add .
git commit -m "type(scope): message"

# View status
cat .STATUS

# Check standards compliance
# (Future: proj check)
```

---

## References

**Source:** `~/projects/dev-tools/zsh-configuration/standards/`

- **Project Standards:** `project/PROJECT-STRUCTURE.md`
- **ADHD Templates:** `adhd/*.md`
- **Code Standards:** `code/COMMIT-MESSAGES.md`
- **Workflow Standards:** `workflow/GIT-WORKFLOW.md`

**Standards Hub README:** `~/projects/dev-tools/zsh-configuration/standards/README.md`

---

**Last Updated:** 2025-12-19
**Status:** ✅ Active standards for aiterm project
**Next Review:** After v0.2.0 release
