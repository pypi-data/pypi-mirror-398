# Common Workflows

Real-world workflows using **aiterm** with Claude Code.

---

## Daily Development Workflow

### Morning Setup

```bash
# 1. Check aiterm health
ait doctor

# 2. Navigate to project
cd ~/projects/myapp

# 3. Apply context
ait switch
# → iTerm2 profile changes to match project type
# → Tab title shows: "📦 node: myapp [main]"

# 4. Start Claude Code
claude

# Context is already set!
```

**Benefits:**
- Visual confirmation you're in the right project
- Git branch visible in tab title
- Profile colors prevent production mistakes

---

## Multi-Project Context Switching

### Scenario: Working on 3 projects simultaneously

```bash
# Terminal Tab 1: Web Frontend
cd ~/projects/webapp
ait switch
# → Node-Dev profile (green theme)
# → Tab: "📦 node: webapp [feature/new-ui]"

# Terminal Tab 2: API Backend
cd ~/projects/api
ait switch
# → Python-Dev profile (blue theme)
# → Tab: "🐍 python: api [develop]"

# Terminal Tab 3: Database Scripts
cd ~/production/migrations
ait switch
# → Production profile (RED theme) 🚨
# → Tab: "🚨 production: migrations [main]"
```

**Visual Safety:**
- Red terminal = production (be extra careful!)
- Different colors = quick visual identification
- Tab titles show branch (no mistakes!)

---

## Claude Code Setup (First Time)

### Safe Progressive Approach

```bash
# Day 1: Read-only exploration
ait claude backup
ait claude approvals add safe-reads
ait claude approvals add minimal

# Day 2-3: Add git operations
ait claude backup
ait claude approvals add git-ops

# Week 2: Add dev tools
ait claude backup
ait claude approvals add python-dev  # or node-dev, r-dev

# Week 3: Add GitHub integration
ait claude backup
ait claude approvals add github-cli

# Optional: Web research
ait claude approvals add web-tools
```

**Philosophy:**
- Start conservative
- Add permissions as needed
- Always backup before changes
- Build trust gradually

---

## R Package Development

### Complete R Package Workflow

```bash
# 1. Navigate to package
cd ~/r-packages/mypackage

# 2. Check context
ait detect
# Shows: 📦 r-package → R-Dev profile

# 3. Set up Claude approvals for R
ait claude backup
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add r-dev

# 4. Apply context
ait switch

# 5. Start Claude
claude
```

**Claude can now:**
- Run `Rscript` and `R CMD check`
- Build documentation with `roxygen2`
- Run `quarto render` for vignettes
- Execute `devtools::test()`
- Git operations for version control

**Example session:**
```
User: Run the package tests and check for errors

Claude: [Runs R CMD check automatically]
Claude: [Shows test results]
Claude: Found 2 failing tests in test-models.R
```

---

## Python Package Development

### pytest + uv Workflow

```bash
# Setup
cd ~/projects/mypkg
ait switch
ait claude approvals add python-dev

# Claude can now:
# - Run pytest automatically
# - Install deps with uv
# - Format code with black/ruff
# - Run type checks with mypy
```

**Example session:**
```
User: Add tests for the new UserAuth class

Claude: [Writes tests in tests/test_auth.py]
Claude: [Runs pytest automatically]
Test Results: 15 passed, 0 failed
```

---

## Production Deployment Safety

### Scenario: Deploying to production

```bash
# 1. Navigate to production directory
cd ~/production/live-site

# 2. Context shows RED warning
ait switch
# → Production profile (RED) 🚨
# → Tab: "🚨 production: live-site [main]"

# 3. Visual cues everywhere
# - Terminal background: red tint
# - Tab title: red warning emoji
# - Status bar: production indicator

# 4. Extra careful mode activated
# - Double-check all commands
# - Review changes before committing
# - Slow down, think first
```

**Safety features:**
- Impossible to miss you're in production
- Different muscle memory (red = danger!)
- Prevents "wrong terminal tab" disasters

---

## Multi-Language Monorepo

### Scenario: Monorepo with Python + Node + R

```bash
# Project structure:
# ~/projects/datascience/
#   ├── api/           (Python)
#   ├── frontend/      (Node.js)
#   ├── analysis/      (R)

# Root level
cd ~/projects/datascience
ait detect
# → Shows: Dev-Tools (has .git + scripts/)

# Work on API
cd ~/projects/datascience/api
ait detect
# → Shows: 🐍 python (has pyproject.toml)
ait switch

# Work on frontend
cd ~/projects/datascience/frontend
ait detect
# → Shows: 📦 node (has package.json)
ait switch

# Work on analysis
cd ~/projects/datascience/analysis
ait detect
# → Shows: 📦 r-package (has DESCRIPTION)
ait switch
```

**Setup once:**
```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev
ait claude approvals add node-dev
ait claude approvals add r-dev
```

**Benefits:**
- Auto-detects sub-project type
- Correct profile for each directory
- Claude uses right tools automatically

---

## GitHub PR Review Workflow

### Complete PR Review with aiterm

```bash
# 1. Setup GitHub CLI permissions
ait claude approvals add github-cli
ait claude approvals add git-ops

# 2. List open PRs
# (Claude can run automatically)
gh pr list

# 3. Checkout PR
gh pr checkout 123

# 4. Context updates automatically
ait switch
# → Shows new branch in tab title

# 5. Review with Claude
claude
```

**Example session:**
```
User: Review this PR for bugs and suggest improvements

Claude: [Reads changed files automatically]
Claude: [Runs tests]
Claude: [Provides review comments]

User: Looks good, approve and merge

Claude: I can approve but you should merge manually
        (gh pr merge requires explicit permission)
```

---

## Quarto Document Workflow

### Academic Paper with Quarto

```bash
# 1. Setup
cd ~/quarto/manuscripts/paper-2024
ait detect
# → Shows: 📊 quarto → R-Dev profile

# 2. Add R dev tools
ait claude approvals add r-dev

# 3. Switch context
ait switch

# 4. Work with Claude
claude
```

**Claude can:**
- Render Quarto documents
- Run R code chunks
- Generate plots
- Format tables
- Manage citations

**Example:**
```
User: Render the manuscript and show any errors

Claude: [Runs quarto render]
Claude: Found error in analysis.qmd line 45
        ggplot requires 'aes' argument
```

---

## Testing Workflow

### Automated Testing Across Projects

**Python:**
```bash
cd ~/projects/myapp
ait switch
# Claude can run: pytest -v
```

**Node.js:**
```bash
cd ~/projects/webapp
ait switch
# Claude can run: npm test, npm run test:unit
```

**R:**
```bash
cd ~/r-packages/mypkg
ait switch
# Claude can run: R CMD check, devtools::test()
```

**Key benefit:** Context detection + auto-approvals = Claude runs tests without asking!

---

## Research Literature Workflow

### With MCP + Web Tools

```bash
# Setup web search permissions
ait claude approvals add web-tools

# Research session
claude
```

**Example:**
```
User: Find recent papers on causal mediation analysis

Claude: [Searches automatically with WebSearch]
Claude: [Fetches paper abstracts with WebFetch]
Claude: [Summarizes findings]
```

**Coming in v0.2.0:**
- MCP server integration
- Zotero library access
- PDF reading and analysis

---

## Emergency "Wrong Directory" Detection

### Scenario: About to deploy to wrong environment

```bash
# Think you're in staging
cd ~/staging/myapp  # Actually: ~/production/myapp
# Terminal turns RED 🚨
# Tab shows: "🚨 production: myapp"

# VISUAL ALARM!
# Red background = STOP
# Check directory
pwd
# /Users/me/production/myapp

# Phew! Caught by context detection.
cd ~/staging/myapp
ait switch
# Back to safe colors
```

**This has saved production countless times!**

---

## Tips & Tricks

### Alias for Quick Navigation

```bash
# Add to ~/.zshrc
alias cdw='cd ~/projects/webapp && ait switch'
alias cdapi='cd ~/projects/api && ait switch'
alias cdprod='cd ~/production && ait switch'
```

### Check Before Switching

```bash
# Detect before applying (safer)
ait detect ~/production/site  # Check first
ait switch ~/production/site  # Apply if correct
```

### Combine with Shell Hooks

```bash
# Auto-switch on cd (add to ~/.zshrc)
chpwd() {
  if [[ -d ".git" ]] || [[ -f "pyproject.toml" ]]; then
    ait switch &>/dev/null
  fi
}
```

---

## Next Steps

- **CLI Reference:** [All commands](../reference/commands.md)
- **Claude Integration:** [Detailed setup](claude-integration.md)
- **Context Detection:** [How detection works](context-detection.md)
