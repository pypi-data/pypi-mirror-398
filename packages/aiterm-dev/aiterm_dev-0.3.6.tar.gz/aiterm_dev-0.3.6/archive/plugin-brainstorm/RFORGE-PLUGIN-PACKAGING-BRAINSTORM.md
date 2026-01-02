# RForge Orchestrator Plugin - Packaging & Distribution Brainstorm

**Date:** 2025-12-21
**Context:** Claude Code plugin packaging and distribution strategies
**Goal:** Make RForge Orchestrator plugin easy to install, update, and distribute

---

## 🎯 Core Questions

1. **How should users install the plugin?**
2. **How do we handle dependencies (rforge-mcp server)?**
3. **How do we manage updates?**
4. **Can we automate the installation process?**
5. **How do we distribute to other users?**

---

## 💡 Packaging Approaches (10+ Ideas)

## CATEGORY 1: Installation Methods ⭐⭐⭐

### Idea 1.1: Git Clone Install
**What:** Users clone a GitHub repo

```bash
# Installation
git clone https://github.com/data-wise/rforge-orchestrator.git \
  ~/.claude/plugins/rforge-orchestrator

# Updates
cd ~/.claude/plugins/rforge-orchestrator
git pull
```

**Pros:**
- ✅ Simple for developers
- ✅ Easy to update (git pull)
- ✅ Version control built-in
- ✅ Can track issues on GitHub

**Cons:**
- ❌ Requires git knowledge
- ❌ Manual dependency management
- ❌ No automatic rforge-mcp setup

**ADHD-Friendly:** ⭐⭐ (too many steps)
**Complexity:** ⭐ (simple)
**Best for:** Developers, early adopters

---

### Idea 1.2: Install Script (One-Command) ⭐⭐⭐⭐⭐
**What:** Single command installs everything

```bash
# One command to rule them all
curl -fsSL https://rforge.dev/install.sh | bash

# Or with wget
wget -qO- https://rforge.dev/install.sh | bash
```

**What the script does:**
```bash
#!/bin/bash
# install.sh

set -e

echo "📦 Installing RForge Orchestrator Plugin..."

# 1. Install rforge-mcp if not present
if ! command -v rforge-mcp &> /dev/null; then
  echo "Installing RForge MCP server..."
  npx rforge-mcp configure
fi

# 2. Download plugin
PLUGIN_DIR="$HOME/.claude/plugins/rforge-orchestrator"
mkdir -p "$PLUGIN_DIR"

echo "Downloading plugin files..."
curl -fsSL https://github.com/data-wise/rforge-orchestrator/archive/main.tar.gz | \
  tar -xz -C "$PLUGIN_DIR" --strip-components=1

# 3. Verify installation
if [ -f "$PLUGIN_DIR/plugin.json" ]; then
  echo "✅ Plugin installed successfully!"
  echo ""
  echo "Next steps:"
  echo "1. Restart Claude Code"
  echo "2. Try: /rforge:analyze --help"
else
  echo "❌ Installation failed"
  exit 1
fi

echo ""
echo "📚 Documentation: https://rforge.dev/docs"
echo "🐛 Issues: https://github.com/data-wise/rforge-orchestrator/issues"
```

**Pros:**
- ✅ One command installation
- ✅ Handles dependencies automatically
- ✅ Can verify installation
- ✅ ADHD-friendly (minimal steps)
- ✅ Works on macOS/Linux

**Cons:**
- ❌ Requires curl/wget
- ❌ Security concerns (running remote script)
- ❌ Needs hosted install script

**ADHD-Friendly:** ⭐⭐⭐⭐⭐ (one command!)
**Complexity:** ⭐⭐ (script maintenance)
**Best for:** All users, recommended approach

---

### Idea 1.3: NPM Package ⭐⭐⭐⭐
**What:** Publish plugin as npm package

```bash
# Installation
npm install -g @rforge/orchestrator-plugin

# Or with npx (no install)
npx @rforge/orchestrator-plugin install
```

**Package structure:**
```json
{
  "name": "@rforge/orchestrator-plugin",
  "version": "0.1.0",
  "bin": {
    "rforge-plugin": "./bin/cli.js"
  },
  "scripts": {
    "postinstall": "node scripts/install-plugin.js"
  }
}
```

**Install script (postinstall):**
```javascript
// scripts/install-plugin.js
const fs = require('fs');
const path = require('path');
const os = require('os');

const pluginDir = path.join(os.homedir(), '.claude', 'plugins', 'rforge-orchestrator');
const sourceDir = path.join(__dirname, '..', 'plugin');

// Copy plugin files
fs.cpSync(sourceDir, pluginDir, { recursive: true });

console.log('✅ RForge Orchestrator plugin installed!');
console.log('Restart Claude Code to activate.');
```

**Pros:**
- ✅ Familiar to developers (npm)
- ✅ Automatic updates (npm update)
- ✅ Version management built-in
- ✅ Can bundle dependencies
- ✅ Works cross-platform

**Cons:**
- ❌ Requires Node.js/npm
- ❌ More complex packaging
- ❌ Still need rforge-mcp separately

**ADHD-Friendly:** ⭐⭐⭐⭐ (familiar if you use npm)
**Complexity:** ⭐⭐⭐ (packaging overhead)
**Best for:** Node.js developers

---

### Idea 1.4: Claude Code Plugin Manager ⭐⭐⭐⭐⭐
**What:** Built-in plugin manager in Claude Code

```bash
# If Claude Code had a plugin manager
claude plugin install rforge-orchestrator

# Or in Claude interface
/plugin:install rforge-orchestrator
```

**How it would work:**
1. Plugin registry (like npm, but for Claude plugins)
2. Claude Code has built-in `plugin` command
3. Plugins have metadata (dependencies, version)
4. Auto-installs dependencies (like rforge-mcp)
5. Auto-updates available

**Pros:**
- ✅ Best user experience
- ✅ Integrated with Claude Code
- ✅ Dependency management automatic
- ✅ Updates managed centrally
- ✅ Discovery (browse plugins)

**Cons:**
- ❌ Doesn't exist yet!
- ❌ Would need Anthropic to build
- ❌ Not under our control

**ADHD-Friendly:** ⭐⭐⭐⭐⭐ (ideal!)
**Complexity:** ⭐⭐⭐⭐⭐ (requires Anthropic)
**Best for:** Future (if Claude builds it)
**Status:** 🔮 Aspirational

---

### Idea 1.5: Homebrew Formula (macOS) ⭐⭐⭐⭐
**What:** Install via Homebrew (like aiterm!)

```bash
# Add tap
brew tap data-wise/rforge

# Install plugin
brew install rforge-orchestrator-plugin

# Updates
brew upgrade rforge-orchestrator-plugin
```

**Formula:**
```ruby
# Formula/rforge-orchestrator-plugin.rb
class RforgeOrchestratorPlugin < Formula
  desc "Auto-delegation orchestrator for RForge MCP tools"
  homepage "https://github.com/data-wise/rforge-orchestrator"
  url "https://github.com/data-wise/rforge-orchestrator/archive/v0.1.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "rforge-mcp"  # Dependency!

  def install
    plugin_dir = "#{Dir.home}/.claude/plugins/rforge-orchestrator"
    mkdir_p plugin_dir
    cp_r Dir["*"], plugin_dir
  end

  def caveats
    <<~EOS
      Plugin installed to ~/.claude/plugins/rforge-orchestrator

      Next steps:
      1. Restart Claude Code
      2. Try: /rforge:analyze --help

      Documentation: https://rforge.dev/docs
    EOS
  end

  test do
    assert_predicate "#{Dir.home}/.claude/plugins/rforge-orchestrator/plugin.json", :exist?
  end
end
```

**Pros:**
- ✅ macOS standard (familiar)
- ✅ Handles dependencies (rforge-mcp)
- ✅ Auto-updates (brew upgrade)
- ✅ Uninstall easy (brew uninstall)
- ✅ Matches aiterm distribution!

**Cons:**
- ❌ macOS only
- ❌ Requires Homebrew tap maintenance
- ❌ Learning curve for non-Homebrew users

**ADHD-Friendly:** ⭐⭐⭐⭐⭐ (macOS users love Homebrew)
**Complexity:** ⭐⭐ (formula maintenance)
**Best for:** macOS users (which you are!)

---

## CATEGORY 2: Dependency Management ⭐⭐⭐

### Idea 2.1: Bundled Dependencies
**What:** Include rforge-mcp with plugin

**Approaches:**

**A) Bundle MCP server in plugin:**
```
rforge-orchestrator/
├── plugin.json
├── agents/
├── skills/
└── vendor/
    └── rforge-mcp/          # Bundled!
        └── dist/index.js
```

**B) Download on first use:**
```typescript
// On first skill invocation
if (!mcpServerAvailable()) {
  console.log('Installing RForge MCP server...');
  await installMCPServer();  // npx rforge-mcp configure
}
```

**Pros:**
- ✅ No separate install needed
- ✅ Version compatibility guaranteed
- ✅ Works offline (if bundled)

**Cons:**
- ❌ Larger package size
- ❌ Duplicate if user has rforge-mcp globally
- ❌ Update complexity (need to update both)

**ADHD-Friendly:** ⭐⭐⭐⭐ (no extra steps)
**Complexity:** ⭐⭐⭐ (bundling overhead)

---

### Idea 2.2: Dependency Checker + Auto-Install ⭐⭐⭐⭐⭐
**What:** Check for dependencies, offer to install

```typescript
// In orchestrator agent startup
async function checkDependencies() {
  // Check if rforge-mcp available
  const mcpAvailable = await isMCPServerConfigured();

  if (!mcpAvailable) {
    console.log('⚠️  RForge MCP server not found');
    console.log('');
    console.log('The orchestrator plugin requires RForge MCP server.');
    console.log('');
    console.log('Install now? [Y/n]');

    const answer = await getUserConfirmation();

    if (answer) {
      console.log('Installing RForge MCP server...');
      await exec('npx rforge-mcp configure');
      console.log('✅ Installation complete!');
      console.log('Please restart Claude Code.');
    } else {
      console.log('Installation skipped.');
      console.log('Install manually: npx rforge-mcp configure');
    }
  }
}
```

**Pros:**
- ✅ Automatic dependency resolution
- ✅ User stays in control (asks permission)
- ✅ Clear error messages
- ✅ ADHD-friendly (does the work for you)

**Cons:**
- ❌ Requires user interaction
- ❌ Needs restart after install

**ADHD-Friendly:** ⭐⭐⭐⭐⭐ (helpful automation)
**Complexity:** ⭐⭐ (simple check + exec)
**Best for:** First-time users

---

### Idea 2.3: Monorepo Package ⭐⭐⭐
**What:** Combine plugin + MCP server in one repo

```
rforge/
├── packages/
│   ├── mcp-server/          # RForge MCP
│   │   ├── src/
│   │   └── package.json
│   └── orchestrator-plugin/ # Claude plugin
│       ├── plugin.json
│       └── agents/
└── package.json             # Root
```

**Installation:**
```bash
# Clone monorepo
git clone https://github.com/data-wise/rforge

# Install everything
cd rforge
npm install

# Setup both
npm run setup:all
```

**Pros:**
- ✅ Single source of truth
- ✅ Version sync automatic
- ✅ Shared code possible
- ✅ Easier development

**Cons:**
- ❌ Larger clone size
- ❌ More complex for users
- ❌ Couples plugin to MCP server

**ADHD-Friendly:** ⭐⭐⭐ (one repo, but bigger)
**Complexity:** ⭐⭐⭐⭐ (monorepo overhead)
**Best for:** Development, not distribution

---

## CATEGORY 3: Update Mechanisms ⭐⭐⭐

### Idea 3.1: Manual Git Pull
**What:** Users update via git

```bash
cd ~/.claude/plugins/rforge-orchestrator
git pull
```

**Pros:**
- ✅ Simple
- ✅ User controls timing

**Cons:**
- ❌ Easy to forget
- ❌ No update notifications

**ADHD-Friendly:** ⭐⭐ (will forget to update)

---

### Idea 3.2: Auto-Update Checker ⭐⭐⭐⭐
**What:** Plugin checks for updates on startup

```typescript
// On orchestrator startup
async function checkForUpdates() {
  const currentVersion = '0.1.0';  // From plugin.json

  const latestVersion = await fetch('https://api.github.com/repos/data-wise/rforge-orchestrator/releases/latest')
    .then(r => r.json())
    .then(data => data.tag_name.replace('v', ''));

  if (latestVersion > currentVersion) {
    console.log(`🆕 New version available: ${latestVersion} (you have ${currentVersion})`);
    console.log('Update with: cd ~/.claude/plugins/rforge-orchestrator && git pull');
    console.log('Or: brew upgrade rforge-orchestrator-plugin');
  }
}
```

**Pros:**
- ✅ Users know updates exist
- ✅ Non-intrusive (just notifies)
- ✅ Can include changelog

**Cons:**
- ❌ Still manual update process
- ❌ Requires network call

**ADHD-Friendly:** ⭐⭐⭐⭐ (helpful reminder)
**Complexity:** ⭐⭐ (simple check)

---

### Idea 3.3: Skill-Based Update ⭐⭐⭐⭐⭐
**What:** Add update skill to plugin

```bash
# Check for updates
/rforge:update check

# Apply updates
/rforge:update apply

# Or combined
/rforge:update
```

**Implementation:**
```markdown
<!-- skills/update.md -->
# /rforge:update - Update Plugin

Check for and apply plugin updates.

## Usage

\`\`\`bash
# Check only
/rforge:update check

# Check and apply
/rforge:update
\`\`\`

## What it does

1. Checks GitHub for latest release
2. Shows changelog
3. Asks permission to update
4. Downloads and installs update
5. Verifies installation
6. Reminds to restart Claude Code
```

**Pros:**
- ✅ Integrated with plugin
- ✅ User-friendly (skill command)
- ✅ Can show changelog
- ✅ ADHD-friendly (easy to remember)

**Cons:**
- ❌ Needs permissions to modify files
- ❌ Requires restart after update

**ADHD-Friendly:** ⭐⭐⭐⭐⭐ (super easy)
**Complexity:** ⭐⭐⭐ (needs download + install logic)
**Best for:** All users

---

### Idea 3.4: Auto-Update (Opt-in) ⭐⭐⭐
**What:** Automatic updates in background

```json
// plugin.json
{
  "settings": {
    "auto_update": {
      "enabled": false,        // Default: off
      "check_interval": 86400, // Daily
      "notify_before_update": true
    }
  }
}
```

**Pros:**
- ✅ Always up to date
- ✅ No user action needed

**Cons:**
- ❌ Unexpected changes
- ❌ Breaking changes risk
- ❌ Might update mid-session

**ADHD-Friendly:** ⭐⭐⭐⭐ (no maintenance burden)
**Complexity:** ⭐⭐⭐⭐ (background service needed)
**Best for:** Stable plugins with good versioning

---

## CATEGORY 4: Distribution Channels ⭐⭐⭐

### Idea 4.1: GitHub Releases ⭐⭐⭐⭐⭐
**What:** Official releases on GitHub

```bash
# Download release
wget https://github.com/data-wise/rforge-orchestrator/releases/download/v0.1.0/rforge-orchestrator.tar.gz

# Extract
tar -xzf rforge-orchestrator.tar.gz -C ~/.claude/plugins/
```

**Release process:**
```bash
# Create release
git tag v0.1.0
git push origin v0.1.0

# GitHub Actions builds package
# Attaches tar.gz to release
```

**Pros:**
- ✅ Official source
- ✅ Version history
- ✅ Changelog included
- ✅ Free hosting

**Cons:**
- ❌ Manual download/extract
- ❌ Requires GitHub account (for issues)

**ADHD-Friendly:** ⭐⭐⭐ (standard but manual)
**Complexity:** ⭐⭐ (GitHub releases are easy)

---

### Idea 4.2: NPM Registry ⭐⭐⭐⭐
**What:** Publish to npm

```bash
npm install -g @rforge/orchestrator-plugin
```

**Pros:**
- ✅ Familiar to developers
- ✅ Easy updates (npm update)
- ✅ Version management built-in

**Cons:**
- ❌ Requires npm
- ❌ Not discoverable to non-developers

**ADHD-Friendly:** ⭐⭐⭐⭐ (if you use npm)
**Complexity:** ⭐⭐⭐ (publishing overhead)

---

### Idea 4.3: Claude Plugin Marketplace ⭐⭐⭐⭐⭐
**What:** Official Claude Code plugin marketplace (future)

**If it existed:**
- Browse plugins in Claude interface
- One-click install
- Auto-updates
- Reviews & ratings
- Dependency management

**Status:** 🔮 Doesn't exist yet, but would be ideal!

---

### Idea 4.4: Self-Hosted Install Server ⭐⭐
**What:** Host installation on your own server

```bash
curl https://rforge.dev/install | bash
```

**Pros:**
- ✅ Full control
- ✅ Can track analytics
- ✅ Custom domain

**Cons:**
- ❌ Server costs
- ❌ Maintenance burden
- ❌ Uptime responsibility

**ADHD-Friendly:** ⭐⭐⭐ (user doesn't care where it's hosted)
**Complexity:** ⭐⭐⭐⭐ (infrastructure)

---

## CATEGORY 5: Packaging Formats ⭐⭐⭐

### Idea 5.1: Tarball (tar.gz) ⭐⭐⭐⭐
**What:** Compressed archive

```bash
# Create package
tar -czf rforge-orchestrator-v0.1.0.tar.gz \
  -C ~/.claude/plugins/rforge-orchestrator .

# Install
tar -xzf rforge-orchestrator-v0.1.0.tar.gz \
  -C ~/.claude/plugins/rforge-orchestrator
```

**Pros:**
- ✅ Simple
- ✅ Cross-platform
- ✅ Small size

**Cons:**
- ❌ Manual extraction
- ❌ No dependency handling

---

### Idea 5.2: Zip Archive ⭐⭐⭐⭐
**What:** Zip file (Windows-friendly)

```bash
# Create
zip -r rforge-orchestrator-v0.1.0.zip ~/.claude/plugins/rforge-orchestrator

# Install
unzip rforge-orchestrator-v0.1.0.zip -d ~/.claude/plugins/
```

**Pros:**
- ✅ Windows-friendly
- ✅ Familiar to all users
- ✅ Built-in to macOS/Windows

**Cons:**
- ❌ Manual extraction
- ❌ No dependency handling

---

### Idea 5.3: Self-Extracting Installer ⭐⭐⭐
**What:** Single executable that installs

```bash
# Download installer
wget https://rforge.dev/install/rforge-orchestrator-installer.sh

# Run (self-extracting)
chmod +x rforge-orchestrator-installer.sh
./rforge-orchestrator-installer.sh
```

**What it does:**
1. Extracts plugin files
2. Checks dependencies
3. Installs rforge-mcp if needed
4. Verifies installation
5. Shows next steps

**Pros:**
- ✅ Single file
- ✅ Handles everything
- ✅ ADHD-friendly (one command)

**Cons:**
- ❌ Platform-specific
- ❌ Larger file size

---

## CATEGORY 6: Advanced Ideas ⭐⭐

### Idea 6.1: Plugin CLI Tool
**What:** Dedicated CLI for plugin management

```bash
# Install CLI
npm install -g rforge-cli

# Use CLI to manage plugin
rforge install orchestrator
rforge update orchestrator
rforge uninstall orchestrator
rforge list
```

**Pros:**
- ✅ Centralized management
- ✅ Can manage multiple RForge components

**Cons:**
- ❌ Extra tool to install
- ❌ More complexity

---

### Idea 6.2: Docker Container
**What:** Run plugin in container (extreme!)

**Probably overkill**, but mentioned for completeness.

---

### Idea 6.3: VS Code Marketplace Pattern
**What:** Mimic VS Code extension distribution

**Features to copy:**
- Search/browse plugins
- One-click install
- Auto-updates
- Dependency management
- User reviews

**Pros:**
- ✅ Proven model
- ✅ Great UX

**Cons:**
- ❌ Requires infrastructure
- ❌ Claude Code doesn't have this yet

---

## 🎯 Recommended Packaging Strategy

### Phase 1: MVP (Week 1) ⭐⭐⭐⭐⭐

**Primary: Install Script**
```bash
curl -fsSL https://rforge.dev/install.sh | bash
```

**What it does:**
1. Install rforge-mcp (if not present)
2. Download plugin from GitHub
3. Extract to ~/.claude/plugins/
4. Verify installation
5. Show next steps

**Backup: Manual Git Clone**
```bash
git clone https://github.com/data-wise/rforge-orchestrator.git \
  ~/.claude/plugins/rforge-orchestrator
npx rforge-mcp configure
```

**Why this approach:**
- ✅ One-command install
- ✅ Handles dependencies
- ✅ Works on macOS/Linux
- ✅ Easy to maintain
- ✅ ADHD-friendly

---

### Phase 2: Polish (Week 2) ⭐⭐⭐⭐⭐

**Add: Homebrew Formula**
```bash
brew tap data-wise/rforge
brew install rforge-orchestrator-plugin
```

**Why add Homebrew:**
- ✅ macOS standard (you use it!)
- ✅ Matches aiterm distribution
- ✅ Handles updates elegantly
- ✅ Familiar to macOS developers

---

### Phase 3: Scale (Month 2) ⭐⭐⭐⭐

**Add: NPM Package**
```bash
npm install -g @rforge/orchestrator-plugin
```

**Add: Update Skill**
```bash
/rforge:update
```

**Why add these:**
- NPM: Reaches Node.js developers
- Update skill: Better UX for all users

---

## 📊 Comparison Matrix

| Method | Install Ease | Update Ease | Deps | ADHD | Platform | Priority |
|--------|--------------|-------------|------|------|----------|----------|
| **Install Script** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | Mac/Linux | **🔥 P0** |
| **Homebrew** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | macOS | **🔥 P1** |
| **Git Clone** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ⭐⭐ | All | P2 |
| **NPM** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ | All | P3 |
| **Update Skill** | N/A | ⭐⭐⭐⭐⭐ | N/A | ⭐⭐⭐⭐⭐ | All | P3 |

---

## 🛠️ Implementation Plan

### Week 1: Install Script

**Create install.sh:**
```bash
#!/bin/bash
set -e

echo "📦 Installing RForge Orchestrator Plugin..."

# 1. Check/install rforge-mcp
if ! command -v rforge-mcp &> /dev/null && ! npx rforge-mcp --version &> /dev/null; then
  echo "Installing RForge MCP server..."
  npx rforge-mcp configure
fi

# 2. Download plugin
PLUGIN_DIR="$HOME/.claude/plugins/rforge-orchestrator"
TEMP_DIR=$(mktemp -d)

echo "Downloading plugin..."
curl -fsSL https://github.com/data-wise/rforge-orchestrator/archive/main.tar.gz | \
  tar -xz -C "$TEMP_DIR" --strip-components=1

# 3. Install
mkdir -p "$PLUGIN_DIR"
cp -r "$TEMP_DIR"/* "$PLUGIN_DIR"/

# 4. Cleanup
rm -rf "$TEMP_DIR"

# 5. Verify
if [ -f "$PLUGIN_DIR/plugin.json" ]; then
  VERSION=$(grep '"version"' "$PLUGIN_DIR/plugin.json" | cut -d'"' -f4)
  echo "✅ Plugin v$VERSION installed successfully!"
  echo ""
  echo "Next steps:"
  echo "1. Restart Claude Code"
  echo "2. Try: /rforge:analyze --help"
  echo ""
  echo "📚 Docs: https://github.com/data-wise/rforge-orchestrator"
else
  echo "❌ Installation failed"
  exit 1
fi
```

**Host it:**
```bash
# Add to GitHub repo
.github/
└── install.sh

# Enable GitHub Pages with redirect
echo "curl -fsSL https://raw.githubusercontent.com/data-wise/rforge-orchestrator/main/.github/install.sh | bash" > index.html
```

**Test:**
```bash
curl -fsSL https://rforge.dev/install.sh | bash
```

---

### Week 2: Homebrew Formula

**Create formula:**
```ruby
# data-wise/homebrew-tap/Formula/rforge-orchestrator-plugin.rb
class RforgeOrchestratorPlugin < Formula
  desc "Auto-delegation orchestrator for RForge MCP tools"
  homepage "https://github.com/data-wise/rforge-orchestrator"
  url "https://github.com/data-wise/rforge-orchestrator/archive/v0.1.0.tar.gz"
  sha256 "..."  # Calculate with: shasum -a 256 rforge-orchestrator-v0.1.0.tar.gz
  license "MIT"

  depends_on "node"  # For rforge-mcp

  def install
    # Copy plugin files to Claude plugins directory
    plugin_dir = "#{Dir.home}/.claude/plugins/rforge-orchestrator"
    mkdir_p plugin_dir
    cp_r Dir["*"], plugin_dir

    # Ensure rforge-mcp is configured
    system "npx", "rforge-mcp", "configure" unless File.exist?("#{Dir.home}/.claude/settings.json")
  end

  def caveats
    <<~EOS
      RForge Orchestrator plugin installed!

      Next steps:
      1. Restart Claude Code
      2. Try: /rforge:analyze --help

      Documentation: https://github.com/data-wise/rforge-orchestrator
      Issues: https://github.com/data-wise/rforge-orchestrator/issues
    EOS
  end

  test do
    assert_predicate "#{Dir.home}/.claude/plugins/rforge-orchestrator/plugin.json", :exist?
  end
end
```

**Publish:**
```bash
# In homebrew-tap repo
git add Formula/rforge-orchestrator-plugin.rb
git commit -m "Add rforge-orchestrator-plugin formula"
git push

# Users can now install:
brew tap data-wise/tap
brew install rforge-orchestrator-plugin
```

---

### Week 3: Update Skill

**Add skill:**
```markdown
<!-- skills/update.md -->
# /rforge:update - Update Plugin

Update the RForge Orchestrator plugin to the latest version.

## Usage

\`\`\`bash
/rforge:update
\`\`\`

## What it does

1. Checks GitHub for latest release
2. Shows changelog
3. Downloads update
4. Installs to ~/.claude/plugins/rforge-orchestrator
5. Verifies installation
```

**Implementation:**
```typescript
// In orchestrator agent
async function handleUpdate() {
  // 1. Check for updates
  const current = '0.1.0';  // From plugin.json
  const latest = await fetchLatestVersion();

  if (latest === current) {
    return 'Already up to date!';
  }

  // 2. Show changelog
  const changelog = await fetchChangelog(latest);
  console.log(`New version: ${latest}`);
  console.log(changelog);

  // 3. Confirm
  const confirm = await askUser('Update now?');
  if (!confirm) return 'Update cancelled.';

  // 4. Download & install
  await downloadAndInstall(latest);

  // 5. Success
  return `Updated to v${latest}! Please restart Claude Code.`;
}
```

---

## 🎉 Final Recommendation

### **Use Multi-Channel Distribution:**

**Primary (Week 1):**
```bash
# Install script (one command)
curl -fsSL https://rforge.dev/install.sh | bash
```

**Secondary (Week 2):**
```bash
# Homebrew (macOS standard)
brew install data-wise/tap/rforge-orchestrator-plugin
```

**Tertiary (Week 3+):**
```bash
# NPM (for Node.js users)
npm install -g @rforge/orchestrator-plugin

# Update skill (for all users)
/rforge:update
```

**Manual (always available):**
```bash
# Git clone (for developers)
git clone https://github.com/data-wise/rforge-orchestrator.git \
  ~/.claude/plugins/rforge-orchestrator
```

---

## ✅ Action Items

### Immediate (This Week):
1. [ ] Create install.sh script
2. [ ] Test install script locally
3. [ ] Add install.sh to GitHub repo
4. [ ] Update README with installation instructions
5. [ ] Test from clean environment

### Week 2:
1. [ ] Create Homebrew formula
2. [ ] Add to data-wise/homebrew-tap
3. [ ] Test Homebrew installation
4. [ ] Document Homebrew method

### Week 3+:
1. [ ] Create NPM package
2. [ ] Publish to NPM registry
3. [ ] Add /rforge:update skill
4. [ ] Create update mechanism

---

**Generated:** 2025-12-21
**Status:** Comprehensive packaging strategy ready
**Priority:** Install script (P0), Homebrew (P1), NPM + Update skill (P3)

**Next:** Implement install.sh and test it! 🚀
