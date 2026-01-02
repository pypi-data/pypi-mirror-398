# Claude Code Integration

Complete guide to using **aiterm** with Claude Code CLI.

---

## Overview

**aiterm** helps you manage Claude Code configuration:

- ✅ View and backup `~/.claude/settings.json`
- ✅ Manage auto-approval permissions with curated presets
- ✅ Quick setup with safe, production-tested configurations
- 🚧 Hook management (coming v0.2.0)
- 🚧 MCP server integration (coming v0.2.0)

---

## Quick Setup (5 Minutes)

### 1. Check Current Configuration

```bash
# View current settings
ait claude settings

# List current auto-approvals
ait claude approvals list
```

### 2. Backup Before Changes

```bash
# Create timestamped backup
ait claude backup
# → Creates: ~/.claude/settings.backup-20241218-153045.json
```

### 3. Add Safe Permissions

```bash
# Start with safe read-only operations
ait claude approvals add safe-reads

# Add git operations (no destructive commands)
ait claude approvals add git-ops

# Add your primary dev tools
ait claude approvals add python-dev  # or node-dev, r-dev
```

### 4. Verify

```bash
# Check what was added
ait claude approvals list
```

**Done!** Claude Code can now execute approved commands without prompting.

---

## Auto-Approval Presets

### safe-reads (5 permissions)

**Purpose:** Read-only file and directory operations

**Permissions:**
```bash
Read(/Users/youruser/**)     # Read any file
Glob(**/*.py)                 # Search for files
Grep(*)                       # Search file contents
Bash(ls:*)                    # List directories
Bash(cat:*)                   # View file contents
```

**Use when:**
- Starting with Claude Code
- Maximum safety
- Exploration and learning

**Add:**
```bash
ait claude approvals add safe-reads
```

---

### git-ops (12 permissions)

**Purpose:** Git workflow commands (no destructive operations)

**Permissions:**
```bash
Bash(git status:*)
Bash(git diff:*)
Bash(git log:*)
Bash(git show:*)
Bash(git branch:*)
Bash(git fetch:*)
Bash(git add:*)
Bash(git commit:*)
Bash(git push:*)
Bash(git checkout:*)
Bash(git pull:*)
Bash(git stash:*)
```

**Excluded:** `git reset --hard`, `git push --force`, destructive operations

**Use when:**
- Daily development workflow
- Code reviews
- Branch management

**Add:**
```bash
ait claude approvals add git-ops
```

---

### github-cli (8 permissions)

**Purpose:** GitHub CLI operations

**Permissions:**
```bash
Bash(gh pr list:*)
Bash(gh pr view:*)
Bash(gh pr create:*)
Bash(gh pr checkout:*)
Bash(gh issue list:*)
Bash(gh issue view:*)
Bash(gh repo:*)
Bash(gh api:*)               # Read-only API calls
```

**Excluded:** `gh pr merge`, destructive repo operations

**Use when:**
- Working with pull requests
- Managing issues
- Reviewing code on GitHub

**Add:**
```bash
ait claude approvals add github-cli
```

---

### python-dev (6 permissions)

**Purpose:** Python development tools

**Permissions:**
```bash
Bash(python3:*)
Bash(pip3 install:*)
Bash(pytest:*)
Bash(python -m pytest:*)
Bash(uv:*)                   # UV package manager
Bash(uv pip install:*)
```

**Use when:**
- Python package development
- Running tests
- Installing dependencies

**Add:**
```bash
ait claude approvals add python-dev
```

---

### node-dev (7 permissions)

**Purpose:** Node.js and JavaScript development

**Permissions:**
```bash
Bash(npm install:*)
Bash(npm run:*)
Bash(npx:*)
Bash(bun:*)                  # Bun runtime
Bash(node:*)
Bash(yarn:*)
Bash(pnpm:*)
```

**Use when:**
- JavaScript/TypeScript development
- React/Vue/Angular projects
- npm package development

**Add:**
```bash
ait claude approvals add node-dev
```

---

### r-dev (5 permissions)

**Purpose:** R package development and Quarto

**Permissions:**
```bash
Bash(Rscript:*)
Bash(R CMD:*)
Bash(R:*)
Bash(quarto:*)
Bash(which:*)                # Check R installation
```

**Use when:**
- R package development
- Statistical analysis
- Quarto document rendering

**Add:**
```bash
ait claude approvals add r-dev
```

---

### web-tools (2 permissions)

**Purpose:** Web search and content fetching

**Permissions:**
```bash
WebSearch
WebFetch(domain:*)
```

**Use when:**
- Research tasks
- Documentation lookups
- Finding examples online

**Add:**
```bash
ait claude approvals add web-tools
```

---

### minimal (10 permissions)

**Purpose:** Bare minimum shell commands

**Permissions:**
```bash
Bash(ls:*)
Bash(cat:*)
Bash(echo:*)
Bash(pwd:*)
Bash(cd:*)
Bash(find:*)
Bash(grep:*)
Bash(wc:*)
Bash(head:*)
Bash(tail:*)
```

**Use when:**
- Ultra-conservative approach
- Learning Claude Code
- Shared environments

**Add:**
```bash
ait claude approvals add minimal
```

---

## Recommended Combinations

### For Web Developers

```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add node-dev
ait claude approvals add github-cli
ait claude approvals add web-tools
```

### For Python Developers

```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev
ait claude approvals add github-cli
```

### For R Package Developers

```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add r-dev
ait claude approvals add github-cli
```

### Conservative Starter

```bash
ait claude approvals add safe-reads
ait claude approvals add minimal
```

---

## Managing Permissions

### View Current Approvals

```bash
# List all approved permissions
ait claude approvals list

# View in Claude Code settings file
ait claude settings
```

### Backup Strategy

```bash
# Before adding new permissions
ait claude backup

# Creates timestamped backup:
# ~/.claude/settings.backup-20241218-153045.json
```

**Restore from backup:**
```bash
cp ~/.claude/settings.backup-TIMESTAMP.json ~/.claude/settings.json
```

### Remove Permissions

Currently, you must manually edit `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Remove this line",
      "Bash(pytest:*)"
    ]
  }
}
```

**Coming in v0.2.0:** `ait claude approvals remove <preset>`

---

## Safety Guidelines

### What Presets DON'T Include

**No destructive operations:**
- ❌ `rm -rf` commands
- ❌ `git reset --hard`
- ❌ `git push --force` to main/master
- ❌ System file modifications
- ❌ Credential/secret exposure

**Always requires confirmation:**
- Permanent deletions
- Force pushes
- Production deployments
- Publishing packages
- Account modifications

### When to Be Cautious

**Don't auto-approve:**
- Commands you don't understand
- Operations on production systems
- Financial transactions
- Credential management
- Package publishing

**Always review:**
- PRs before merging
- Commits before pushing
- Deployments to production

---

## Troubleshooting

### Permissions Not Working

```bash
# 1. Verify permissions are in settings
ait claude approvals list

# 2. Check settings file directly
cat ~/.claude/settings.json | grep -A 20 '"allow"'

# 3. Restart Claude Code CLI
# (close terminal, open new session)
```

### Accidentally Added Wrong Preset

```bash
# Restore from backup
ait claude backup  # First, backup current state
cp ~/.claude/settings.backup-PREVIOUS.json ~/.claude/settings.json

# Verify restoration
ait claude approvals list
```

### Finding the Right Preset

```bash
# List all available presets with descriptions
ait claude approvals presets

# Check what permissions a preset includes
# (view source: src/aiterm/claude/settings.py)
```

---

## Advanced Usage

### Custom Permission Patterns

Edit `~/.claude/settings.json` to add custom patterns:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(mycommand:*)",          // Custom command
      "Read(/specific/path/**)",    // Specific directory
      "Bash(npm run test:unit:*)"   // Specific npm script
    ]
  }
}
```

**Pattern syntax:**
- `*` = wildcard (matches any characters)
- `:*` = matches any arguments after command
- `**` = recursive directory match

### Project-Specific Approvals

Use `.claude/settings.local.json` in project root:

```json
{
  "permissions": {
    "allow": [
      "Bash(make:*)",
      "Bash(docker-compose:*)"
    ]
  }
}
```

Claude Code merges local settings with global settings.

---

## Coming in v0.2.0

### Hook Management

```bash
# Install Claude Code hooks
ait hooks install session-start
ait hooks install pre-commit
ait hooks install cost-tracker

# List installed hooks
ait hooks list

# Configure hooks
ait hooks config session-start
```

### MCP Server Integration

```bash
# Discover MCP servers
ait mcp list

# Configure server
ait mcp config statistical-research

# Test server
ait mcp test statistical-research
```

---

## Resources

- **Claude Code Docs:** [https://code.claude.com/docs](https://code.claude.com/docs)
- **Settings Reference:** `~/.claude/settings.json`
- **Command Reference:** [CLI Commands](../reference/commands.md)
- **Workflows:** [Common Workflows](workflows.md)
