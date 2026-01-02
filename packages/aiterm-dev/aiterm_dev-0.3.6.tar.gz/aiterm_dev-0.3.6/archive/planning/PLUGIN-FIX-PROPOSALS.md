# Plugin Loading Bug - Engineering Proposals

**Date:** 2025-12-26
**Issue:** Local plugins not loading due to version/path mismatch

---

## Root Cause

Claude Code's local marketplace handler has a bug:
1. Creates cache directory with name `unknown/` (fallback)
2. Updates registry with semver from `plugin.json` (e.g., `1.1.0`)
3. **Result:** Looks for `/rforge/1.1.0/` but only `/rforge/unknown/` exists

---

## Option A: Bandaid Fix (Not Recommended)

```bash
cd ~/.claude/plugins/cache/local-plugins
mv rforge/unknown rforge/1.1.0
mv workflow/unknown workflow/2.1.0
mv statistical-research/unknown statistical-research/1.1.0
find . -name ".orphaned_at" -delete
```

**Pros:** Quick, immediate fix
**Cons:** Breaks on next sync, doesn't address root cause
**Verdict:** ❌ Technical debt

---

## Option B: Git Submodules (Moderate)

Convert to proper git structure so Claude Code uses SHA versioning.

```bash
# In claude-plugins repo, make each plugin a submodule
cd ~/projects/dev-tools/claude-plugins
rm -rf rforge workflow statistical-research  # backup first!
git submodule add git@github.com:Data-Wise/rforge-plugin.git rforge
git submodule add git@github.com:Data-Wise/workflow-plugin.git workflow
git submodule add git@github.com:Data-Wise/statistical-research-plugin.git statistical-research
```

**Pros:** Claude Code would detect git SHA properly
**Cons:** Requires separate repos per plugin, more complex workflow
**Verdict:** ⚠️ Good for mature plugins, overkill for development

---

## Option C: Direct Plugin Installation (Recommended for Production)

Skip local-marketplace entirely. Install directly from git.

```bash
# Remove local-marketplace approach
rm -rf ~/.claude/local-marketplace
rm ~/.claude/plugins/rforge ~/.claude/plugins/workflow ~/.claude/plugins/statistical-research

# Install from git directly (if plugins have own repos)
claude plugin add https://github.com/Data-Wise/rforge-plugin
claude plugin add https://github.com/Data-Wise/workflow-plugin

# Or publish to cc-marketplace and install normally
```

**Pros:** Works with Claude Code's expected flow, auto-updates work
**Cons:** Requires publishing plugins, less convenient for dev
**Verdict:** ✅ Best for production/stable plugins

---

## Option D: Symlink to Cache (Development Workaround)

Create symlinks in cache that point to dev directories.

```bash
# Clear broken cache
rm -rf ~/.claude/plugins/cache/local-plugins

# Create cache structure that points to dev
mkdir -p ~/.claude/plugins/cache/local-plugins/rforge
mkdir -p ~/.claude/plugins/cache/local-plugins/workflow
mkdir -p ~/.claude/plugins/cache/local-plugins/statistical-research

# Symlink version dirs to source
ln -s /Users/dt/projects/dev-tools/claude-plugins/rforge \
      ~/.claude/plugins/cache/local-plugins/rforge/1.1.0
ln -s /Users/dt/projects/dev-tools/claude-plugins/workflow \
      ~/.claude/plugins/cache/local-plugins/workflow/2.1.0
ln -s /Users/dt/projects/dev-tools/claude-plugins/statistical-research \
      ~/.claude/plugins/cache/local-plugins/statistical-research/1.1.0

# Remove orphan markers if they get recreated
find ~/.claude/plugins/cache/local-plugins -name ".orphaned_at" -delete
```

**Pros:**
- Development changes immediately reflected (no copy)
- Paths match what registry expects
- Easy to update version: just rename symlink

**Cons:**
- Manual version management
- Claude Code sync might overwrite
- Need to update symlink name when version changes

**Verdict:** ✅ Best for active development

---

## Option E: Self-Healing Script (Most Robust for Dev)

Create a script that fixes the mismatch automatically.

```bash
#!/bin/bash
# ~/.claude/scripts/fix-local-plugins.sh

CACHE_DIR="$HOME/.claude/plugins/cache/local-plugins"
REGISTRY="$HOME/.claude/plugins/installed_plugins.json"

for plugin in rforge workflow statistical-research; do
  # Get expected version from registry
  expected_version=$(jq -r ".plugins[\"${plugin}@local-plugins\"][0].version" "$REGISTRY")

  # Check if cache has 'unknown' dir
  if [ -d "$CACHE_DIR/$plugin/unknown" ] && [ ! -d "$CACHE_DIR/$plugin/$expected_version" ]; then
    echo "Fixing $plugin: unknown → $expected_version"
    mv "$CACHE_DIR/$plugin/unknown" "$CACHE_DIR/$plugin/$expected_version"
  fi

  # Remove orphan marker
  find "$CACHE_DIR/$plugin" -name ".orphaned_at" -delete 2>/dev/null
done

echo "Local plugins fixed!"
```

**Run as:** Claude Code hook on SessionStart, or cron, or alias.

**Pros:**
- Automatic self-healing
- Works with Claude Code's sync
- No manual intervention needed

**Cons:**
- Adds another moving part
- Might mask underlying issues

**Verdict:** ✅ Best balance of robustness and convenience

---

## Recommendation

**For immediate fix:** Option D (symlink to cache) - gets you working now

**For long-term:** Option E (self-healing script) as SessionStart hook

**For production plugins:** Option C (direct git installation)

---

## Implementation: Combined D + E

### Step 1: Fix now with symlinks

```bash
# Backup and clear
mv ~/.claude/plugins/cache/local-plugins ~/.claude/plugins/cache/local-plugins.bak

# Create clean structure with symlinks
mkdir -p ~/.claude/plugins/cache/local-plugins/rforge
mkdir -p ~/.claude/plugins/cache/local-plugins/workflow
mkdir -p ~/.claude/plugins/cache/local-plugins/statistical-research

ln -s /Users/dt/projects/dev-tools/claude-plugins/rforge \
      ~/.claude/plugins/cache/local-plugins/rforge/1.1.0
ln -s /Users/dt/projects/dev-tools/claude-plugins/workflow \
      ~/.claude/plugins/cache/local-plugins/workflow/2.1.0
ln -s /Users/dt/projects/dev-tools/claude-plugins/statistical-research \
      ~/.claude/plugins/cache/local-plugins/statistical-research/1.1.0
```

### Step 2: Add self-healing hook

```json
// In ~/.claude/settings.json, add to hooks:
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "/bin/bash ~/.claude/scripts/fix-local-plugins.sh"
      }
    ]
  }
}
```

### Step 3: Update version script

When you bump plugin version:
```bash
# Example: rforge 1.1.0 → 1.2.0
cd ~/.claude/plugins/cache/local-plugins/rforge
mv 1.1.0 1.2.0  # Just rename the symlink

# Update plugin.json in source
# Registry will update on next Claude Code sync
```

---

## Future Enhancement: aiterm Integration

Add to aiterm CLI:
```bash
ait plugins fix      # Run self-healing
ait plugins status   # Show local plugin health
ait plugins link     # Create dev symlinks
ait plugins unlink   # Remove and let Claude Code manage
```

This makes local plugin development a first-class workflow.
