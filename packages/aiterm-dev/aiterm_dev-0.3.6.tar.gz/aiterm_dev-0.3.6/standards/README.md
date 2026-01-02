# aiterm Standards

> **TL;DR:** Standard templates and conventions for the aiterm project.

## Overview

This directory contains standards for aiterm project development, documentation, and workflows.

**Source:** Most standards are synced from `zsh-configuration/standards/` (single source of truth for DT's dev standards)

**Sync:** Run `../scripts/sync-standards.sh` to update from zsh-configuration

---

## Directory Structure

```
standards/
├── README.md              # This file
├── adhd/                  # ADHD-friendly templates (synced)
│   ├── QUICK-START-TEMPLATE.md
│   ├── GETTING-STARTED-TEMPLATE.md
│   ├── TUTORIAL-TEMPLATE.md
│   └── REFCARD-TEMPLATE.md
├── code/                  # Coding standards (synced)
│   ├── COMMIT-MESSAGES.md
│   ├── R-STYLE-GUIDE.md (reference)
│   └── ZSH-COMMANDS-HELP.md (reference)
├── project/               # Project structure (synced)
│   └── PROJECT-STRUCTURE.md
├── workflow/              # Git workflow (synced)
└── documentation/         # Documentation guides (aiterm-specific)
    ├── MKDOCS-GUIDE.md
    ├── API-DOCS-GUIDE.md
    └── INTERACTIVE-TUTORIAL-GUIDE.md
```

---

## Synced vs. aiterm-Specific

### Synced from zsh-configuration (Universal Standards)

**Directories:** `adhd/`, `code/`, `project/`, `workflow/`

These standards apply to ALL of DT's dev projects:
- ADHD-friendly documentation templates
- Git commit message format
- Project structure conventions
- Development workflow

**To update:** Run `../scripts/sync-standards.sh`

### aiterm-Specific Standards

**Directory:** `documentation/`

These standards are unique to aiterm:
- MkDocs documentation structure
- Python API documentation (docstrings)
- Interactive tutorial creation
- Web-based documentation hosting

**To update:** Edit files directly in this repo

---

## Quick Reference

### Creating Documentation

```bash
# Use ADHD-friendly templates
cat standards/adhd/QUICK-START-TEMPLATE.md
cat standards/adhd/REFCARD-TEMPLATE.md
cat standards/adhd/TUTORIAL-TEMPLATE.md

# For MkDocs-specific docs
cat standards/documentation/MKDOCS-GUIDE.md

# For Python API docs
cat standards/documentation/API-DOCS-GUIDE.md
```

### Commit Messages

```bash
# Follow conventional commits
cat standards/code/COMMIT-MESSAGES.md

# Examples for aiterm
feat(mcp): add server creation wizard
fix(terminal): handle iTerm2 profile switch
docs: update installation guide
test(cli): add MCP creation tests
```

### Project Structure

```bash
# Check expected structure
cat standards/project/PROJECT-STRUCTURE.md
```

---

## Syncing Standards

### For DT (Maintainer)

When zsh-configuration standards are updated:

```bash
# Update aiterm standards
cd ~/projects/dev-tools/aiterm
./scripts/sync-standards.sh

# Commit updated files
git add standards/
git commit -m "chore(standards): sync from zsh-configuration"
git push
```

### For External Users

Standards are already synced in the repo. Just `git pull` to get updates.

---

## Creating New Documentation

### Tutorial

1. Copy template: `cp standards/adhd/TUTORIAL-TEMPLATE.md docs/tutorials/my-tutorial.md`
2. Fill in the sections
3. Add to `mkdocs.yml`

### Reference Card

1. Copy template: `cp standards/adhd/REFCARD-TEMPLATE.md docs/ref-cards/my-refcard.md`
2. Use table format (scannable, one-page)
3. Keep to printable size

### Quick Start

1. Copy template: `cp standards/adhd/QUICK-START-TEMPLATE.md docs/quickstart.md`
2. Focus on 30-second setup
3. TL;DR at top, commands copy-paste ready

---

## Philosophy

From zsh-configuration standards:

1. **Copy-paste ready** — Every guide has commands you can run
2. **TL;DR first** — Summary at the top, details below
3. **Decision trees** — "If X, do Y" not essays
4. **One source of truth** — Standards live here, nowhere else
5. **Visual hierarchy** — Headers, tables, bullets
6. **Quick wins first** — Easy tasks before hard ones
7. **Concrete next steps** — Numbered, actionable

---

## See Also

- **Full Summary:** `../STANDARDS-SUMMARY.md` - Consolidated overview of all standards
- **Sync Proposal:** `../STANDARDS-SYNC-PROPOSAL.md` - Detailed sync strategy brainstorm
- **Source:** `~/projects/dev-tools/zsh-configuration/standards/` - Original source of truth

---

Last synced: 2025-12-19 22:53:57
