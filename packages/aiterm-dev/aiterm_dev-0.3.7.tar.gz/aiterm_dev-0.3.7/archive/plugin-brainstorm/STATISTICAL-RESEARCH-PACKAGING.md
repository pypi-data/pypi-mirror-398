# Statistical Research Plugin - Packaging Strategy

**Generated:** 2025-12-23
**Context:** Converting statistical-research MCP → Plugin with proper packaging

---

## 🎯 The Packaging Question

**Current situation:**
- MCP servers live in `~/projects/dev-tools/mcp-servers/`
- Plugins get installed to `~/.claude/plugins/`
- Want to package statistical-research plugin for distribution

**Key insight:** Plugins need their own **source project** separate from installation location!

---

## 📁 Proposed Directory Structure

### Option 1: New Top-Level Project (RECOMMENDED) ⭐⭐⭐⭐⭐

```
~/projects/dev-tools/
├── mcp-servers/                    # MCP servers (existing)
│   ├── rforge/                     # RForge MCP
│   ├── statistical-research/       # OLD - will deprecate
│   ├── project-refactor/
│   ├── docling/
│   └── shell/
├── claude-plugins/                 # NEW - Plugin source projects
│   ├── statistical-research/       # NEW - Plugin project
│   │   ├── package.json           # npm package config
│   │   ├── README.md              # Plugin documentation
│   │   ├── LICENSE                # MIT license
│   │   ├── .gitignore
│   │   ├── commands/              # Slash commands
│   │   │   ├── literature/
│   │   │   ├── manuscript/
│   │   │   ├── simulation/
│   │   │   └── research/
│   │   ├── skills/                # 17 A-grade skills
│   │   │   ├── mathematical/
│   │   │   ├── implementation/
│   │   │   ├── writing/
│   │   │   └── research/
│   │   ├── lib/                   # Shell utilities
│   │   │   ├── arxiv-api.sh
│   │   │   ├── crossref-api.sh
│   │   │   └── bibtex-utils.sh
│   │   ├── .claude-plugin/        # Plugin metadata
│   │   │   └── plugin.json
│   │   ├── scripts/               # Installation scripts
│   │   │   ├── install.sh
│   │   │   └── uninstall.sh
│   │   └── tests/                 # Plugin tests
│   └── rforge-orchestrator/       # Could move here too (optional)
├── aiterm/                         # aiterm CLI project
└── ...other projects
```

**Installation flow:**
```bash
# Development
cd ~/projects/dev-tools/claude-plugins/statistical-research
./scripts/install.sh  # Symlinks to ~/.claude/plugins/statistical-research

# Publishing
npm publish statistical-research-plugin

# Users install
npm install -g statistical-research-plugin
# OR
claude plugin install statistical-research
```

**Pros:**
- ✅ Clean separation (source vs installed)
- ✅ Standard npm package structure
- ✅ Easy to publish (npm, GitHub)
- ✅ Version control separate from MCP servers
- ✅ Can have own git repo
- ✅ Follows standard plugin development pattern

**Cons:**
- ⚠️ New directory to manage
- ⚠️ Need to decide: monorepo vs separate repos

---

### Option 2: Under Existing Project (aiterm) ⭐⭐⭐

```
~/projects/dev-tools/aiterm/
├── src/aiterm/                     # aiterm Python package
├── docs/                           # aiterm docs
├── plugins/                        # NEW - Bundled plugins
│   └── statistical-research/       # Plugin source
│       ├── package.json
│       ├── commands/
│       ├── skills/
│       └── ...
└── ...
```

**Installation flow:**
```bash
# Bundled with aiterm
aiterm plugin install statistical-research

# Or standalone
cd ~/projects/dev-tools/aiterm/plugins/statistical-research
./scripts/install.sh
```

**Pros:**
- ✅ Bundled with aiterm ecosystem
- ✅ Single repo for aiterm + plugins
- ✅ Easier to keep in sync

**Cons:**
- ❌ Mixes Python (aiterm) with Claude plugins
- ❌ Different technologies in same repo
- ❌ Harder to publish plugin separately
- ❌ Plugin doesn't make sense without aiterm

---

### Option 3: Standalone GitHub Repo ⭐⭐⭐⭐

```
~/projects/dev-tools/statistical-research-plugin/
├── package.json
├── README.md
├── LICENSE
├── commands/
├── skills/
├── lib/
├── .claude-plugin/
├── scripts/
└── tests/

# Separate repo
https://github.com/Data-Wise/statistical-research-plugin
```

**Installation flow:**
```bash
# Install from GitHub
claude plugin install Data-Wise/statistical-research-plugin

# Or npm
npm install -g @data-wise/statistical-research-plugin

# Or git clone
git clone https://github.com/Data-Wise/statistical-research-plugin.git
cd statistical-research-plugin
./scripts/install.sh
```

**Pros:**
- ✅ Fully independent project
- ✅ Own repo, issues, releases
- ✅ Easy to share/publish
- ✅ Clear ownership

**Cons:**
- ❌ Separate from other dev-tools projects
- ❌ More repos to manage
- ❌ Loses connection to MCP history

---

### Option 4: claude-plugins/ Subdirectory (Hybrid) ⭐⭐⭐⭐⭐ RECOMMENDED

```
~/projects/dev-tools/
├── mcp-servers/                    # MCP source projects
│   ├── rforge/
│   ├── statistical-research/       # OLD MCP (deprecated)
│   └── ...
├── claude-plugins/                 # Plugin source projects
│   ├── statistical-research/       # NEW - Plugin version
│   │   ├── .git/                  # Own git repo
│   │   ├── package.json
│   │   ├── README.md
│   │   └── ...
│   └── README.md                  # Index of plugins
└── aiterm/

# Each plugin is its own git repo
cd ~/projects/dev-tools/claude-plugins/statistical-research
git remote -v
  origin  https://github.com/Data-Wise/statistical-research-plugin.git
```

**This is like mcp-servers/ but for plugins!**

**Pros:**
- ✅ Organized with other plugins
- ✅ Each plugin can be own git repo
- ✅ Easy to find (`ls ~/projects/dev-tools/claude-plugins/`)
- ✅ Consistent with mcp-servers/ pattern
- ✅ Publishable independently
- ✅ Can have shared utilities in parent

**Cons:**
- ⚠️ Need to manage multiple repos
- ⚠️ Need parent README to index plugins

---

## 🏗️ Recommended: Option 4 (claude-plugins/ directory)

### Why This Works Best

**1. Mirrors MCP Servers Pattern**
```
mcp-servers/        → Source for MCP servers
claude-plugins/     → Source for Claude plugins
```

**2. Each Plugin is Independent**
- Own git repo
- Own package.json
- Own releases
- Own issues/PRs

**3. Easy to Organize**
```bash
cd ~/projects/dev-tools/claude-plugins
ls -la
  statistical-research/     # Plugin 1
  rforge-orchestrator/      # Plugin 2 (could move here)
  aiterm-helpers/           # Future plugin 3
  README.md                 # Index
```

**4. Publishing Workflow**
```bash
# Develop
cd ~/projects/dev-tools/claude-plugins/statistical-research

# Install locally (symlink)
./scripts/install.sh
  → Creates symlink: ~/.claude/plugins/statistical-research → source

# Publish to npm
npm publish

# Users install
npm install -g @data-wise/statistical-research-plugin
# Installs to: ~/.claude/plugins/statistical-research
```

---

## 📦 Package Structure (Detailed)

### File: package.json
```json
{
  "name": "@data-wise/statistical-research-plugin",
  "version": "1.0.0",
  "description": "Statistical research workflows - literature, manuscripts, and 17 A-grade skills",
  "type": "module",
  "main": "index.js",
  "bin": {
    "statistical-research-plugin": "./scripts/install.sh"
  },
  "files": [
    "commands/",
    "skills/",
    "lib/",
    ".claude-plugin/",
    "scripts/",
    "README.md",
    "LICENSE"
  ],
  "scripts": {
    "install": "./scripts/install.sh",
    "uninstall": "./scripts/uninstall.sh",
    "test": "./scripts/test.sh"
  },
  "keywords": [
    "claude",
    "claude-code",
    "plugin",
    "statistics",
    "research",
    "literature",
    "arxiv",
    "bibtex",
    "manuscript"
  ],
  "author": "Stat-Wise",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/Data-Wise/statistical-research-plugin.git"
  },
  "bugs": {
    "url": "https://github.com/Data-Wise/statistical-research-plugin/issues"
  },
  "homepage": "https://github.com/Data-Wise/statistical-research-plugin#readme"
}
```

### File: scripts/install.sh
```bash
#!/bin/bash
# Install plugin to ~/.claude/plugins/

PLUGIN_NAME="statistical-research"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$HOME/.claude/plugins/$PLUGIN_NAME"

echo "Installing $PLUGIN_NAME plugin..."

# Create plugins directory if needed
mkdir -p "$HOME/.claude/plugins"

# Remove existing installation
if [ -e "$TARGET_DIR" ]; then
  echo "Removing existing installation..."
  rm -rf "$TARGET_DIR"
fi

# Create symlink (development mode)
if [ "$1" == "--dev" ]; then
  echo "Creating symlink for development..."
  ln -s "$SOURCE_DIR" "$TARGET_DIR"
  echo "✓ Symlinked: $TARGET_DIR → $SOURCE_DIR"

# Copy files (production mode)
else
  echo "Copying plugin files..."
  cp -r "$SOURCE_DIR" "$TARGET_DIR"
  echo "✓ Installed to: $TARGET_DIR"
fi

echo "✓ $PLUGIN_NAME plugin installed successfully!"
echo ""
echo "Available commands:"
echo "  /research:arxiv <query>          - Search arXiv"
echo "  /research:manuscript:methods     - Write methods section"
echo "  /research:lit-gap <topic>        - Find research gaps"
echo ""
echo "17 A-grade skills available automatically"
```

### File: README.md
```markdown
# Statistical Research Plugin

Statistical research workflows for Claude Code - literature management, manuscript writing, and 17 A-grade research skills.

## Features

### 13 Slash Commands
- **Literature:** arXiv search, DOI lookup, BibTeX management
- **Manuscript:** Methods writing, reviewer responses, proof review
- **Simulation:** Monte Carlo design, analysis
- **Research:** Gap finding, hypothesis generation, analysis planning

### 17 A-Grade Skills
- **Mathematical:** proof-architect, mathematical-foundations, identification-theory, asymptotic-theory
- **Implementation:** simulation-architect, algorithm-designer, numerical-methods, computational-inference, statistical-software-qa
- **Writing:** methods-paper-writer, publication-strategist, methods-communicator
- **Research:** literature-gap-finder, cross-disciplinary-ideation, method-transfer-engine, mediation-meta-analyst, sensitivity-analyst

## Installation

### From npm
```bash
npm install -g @data-wise/statistical-research-plugin
```

### From source
```bash
git clone https://github.com/Data-Wise/statistical-research-plugin.git
cd statistical-research-plugin
./scripts/install.sh
```

### Development mode
```bash
cd ~/projects/dev-tools/claude-plugins/statistical-research
./scripts/install.sh --dev  # Creates symlink
```

## Usage

### Literature Management
```
/research:arxiv "bootstrap mediation"
/research:doi 10.1037/met0000310
/research:bib:search "mediation"
```

### Manuscript Writing
```
/research:manuscript:methods <topic>
/research:manuscript:reviewer <review-file>
```

### Research Planning
```
/research:lit-gap "causal mediation"
/research:analysis-plan <research-question>
```

## Documentation

See [full documentation](https://github.com/Data-Wise/statistical-research-plugin/wiki) for:
- Complete command reference
- Skill descriptions and activation
- API integration guides
- Examples and workflows

## License

MIT
```

---

## 🚀 Migration Path

### Step 1: Create Directory Structure
```bash
# Create claude-plugins directory
mkdir -p ~/projects/dev-tools/claude-plugins
cd ~/projects/dev-tools/claude-plugins

# Create plugin project
mkdir statistical-research
cd statistical-research

# Initialize git repo
git init
git remote add origin https://github.com/Data-Wise/statistical-research-plugin.git
```

### Step 2: Copy/Move Skills from MCP
```bash
# Copy skills from old MCP
cp -r ~/projects/dev-tools/mcp-servers/statistical-research/skills/ \
      ~/projects/dev-tools/claude-plugins/statistical-research/

# Or move if deprecating MCP immediately
mv ~/projects/dev-tools/mcp-servers/statistical-research/skills/ \
   ~/projects/dev-tools/claude-plugins/statistical-research/
```

### Step 3: Create Package Files
```bash
# Create package.json
npm init -y
# Edit with proper details

# Create scripts
mkdir scripts
# Write install.sh, uninstall.sh, test.sh

# Create .claude-plugin metadata
mkdir .claude-plugin
# Write plugin.json
```

### Step 4: Develop Commands
```bash
# Create command structure
mkdir -p commands/{literature,manuscript,simulation,research}
mkdir lib

# Write commands and scripts
# (Follow brainstorm document)
```

### Step 5: Local Testing
```bash
# Install in dev mode
./scripts/install.sh --dev

# Test commands in Claude Code
# Verify skills activate
# Test shell scripts
```

### Step 6: Publish
```bash
# Commit to git
git add .
git commit -m "Initial release"
git tag v1.0.0
git push origin main --tags

# Publish to npm
npm publish

# Create GitHub release
gh release create v1.0.0 --notes "Initial release"
```

---

## 🎯 Benefits of This Approach

### Development Benefits
1. **Source control** - Own git repo for plugin
2. **Version management** - npm semver, releases
3. **Easy testing** - Symlink for development
4. **Clean separation** - Source vs installed

### Distribution Benefits
1. **npm publishing** - Standard package manager
2. **GitHub releases** - Downloadable archives
3. **Easy installation** - `npm install -g`
4. **Auto-updates** - `npm update -g`

### Organization Benefits
1. **Consistent structure** - Like mcp-servers/
2. **Discoverable** - All plugins in one place
3. **Independent repos** - Each plugin separate
4. **Shared utilities** - Can add common lib/

---

## 📊 Comparison: Where Things Live

| Component | Source Location | Installed Location | Distribution |
|-----------|----------------|-------------------|--------------|
| **MCP Servers** | `~/projects/dev-tools/mcp-servers/rforge/` | N/A (runs via node) | npm package |
| **Plugins (OLD)** | N/A | `~/.claude/plugins/rforge-orchestrator/` | Built-in |
| **Plugins (NEW)** | `~/projects/dev-tools/claude-plugins/statistical-research/` | `~/.claude/plugins/statistical-research/` | npm package |
| **Skills** | Bundled in plugin source | Bundled in plugin install | Part of plugin |

---

## 💡 Recommended Workflow

### For Development
```bash
# Clone/create in claude-plugins/
cd ~/projects/dev-tools/claude-plugins
git clone <your-plugin-repo>
cd <plugin-name>

# Install in dev mode (symlink)
./scripts/install.sh --dev

# Edit source, changes reflect immediately
# Test in Claude Code

# Commit when ready
git add .
git commit -m "Add feature"
git push
```

### For Users
```bash
# Install published plugin
npm install -g @data-wise/statistical-research-plugin

# Or from GitHub
git clone https://github.com/Data-Wise/statistical-research-plugin.git
cd statistical-research-plugin
./scripts/install.sh

# Use in Claude Code
/research:arxiv "my query"
```

---

## 🗂️ Index File for claude-plugins/

### File: ~/projects/dev-tools/claude-plugins/README.md
```markdown
# Claude Code Plugins

Source projects for Claude Code plugins developed by Data-Wise.

## Plugins

### statistical-research
**Status:** In Development
**Description:** Statistical research workflows - literature, manuscripts, 17 A-grade skills
**Repo:** https://github.com/Data-Wise/statistical-research-plugin
**Location:** `./statistical-research/`

### rforge-orchestrator (Optional move)
**Status:** Stable
**Description:** Auto-delegation for RForge MCP tools
**Location:** Currently in `~/.claude/plugins/` (could move here)

## Structure

Each plugin:
- Is its own git repository
- Has own package.json for npm publishing
- Installs to `~/.claude/plugins/<name>`
- Can be developed with `./scripts/install.sh --dev`

## Publishing

Plugins are published to npm:
```bash
cd <plugin-dir>
npm publish
```

Users install:
```bash
npm install -g @data-wise/<plugin-name>
```
```

---

## ✅ Final Recommendation

### Create: ~/projects/dev-tools/claude-plugins/

**Structure:**
```
~/projects/dev-tools/
├── mcp-servers/           # MCP source projects (existing)
├── claude-plugins/        # Plugin source projects (NEW)
│   ├── statistical-research/  # New plugin
│   └── README.md          # Index
└── aiterm/                # aiterm CLI
```

**Each plugin:**
- Own git repo (can be submodule or independent)
- Own package.json (npm publishable)
- Installs to `~/.claude/plugins/<name>`
- Development mode: `./scripts/install.sh --dev` (symlink)
- Production: `npm install -g @data-wise/<name>`

**Benefits:**
- ✅ Mirrors mcp-servers/ pattern
- ✅ Each plugin independent
- ✅ Easy to publish/share
- ✅ Clean development workflow
- ✅ Professional packaging

---

**Status:** ✅ Packaging strategy defined
**Next:** Create claude-plugins/ directory and begin statistical-research plugin
