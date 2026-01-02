# Standards Sync Proposal: aiterm ↔ zsh-configuration

**Generated:** 2025-12-19
**Purpose:** Brainstorm strategies for keeping aiterm standards synchronized with zsh-configuration

---

## 🎯 Goal

Keep aiterm's standards folder synchronized with the **source of truth** in zsh-configuration while allowing project-specific customizations.

---

## 📋 Current State Analysis

### Source of Truth: zsh-configuration/standards/

```
~/projects/dev-tools/zsh-configuration/standards/
├── README.md                    # Standards hub overview
├── adhd/
│   ├── QUICK-START-TEMPLATE.md  # 30-second onboarding
│   ├── GETTING-STARTED-TEMPLATE.md  # 10-minute training
│   ├── TUTORIAL-TEMPLATE.md     # Step-by-step guides
│   └── REFCARD-TEMPLATE.md      # One-page quick reference
├── code/
│   ├── COMMIT-MESSAGES.md       # Git commit format
│   ├── R-STYLE-GUIDE.md         # R coding conventions
│   └── ZSH-COMMANDS-HELP.md     # ZSH help output standard
├── project/
│   └── PROJECT-STRUCTURE.md     # Directory conventions
└── workflow/
    └── (future: GIT-WORKFLOW.md, RELEASE-PROCESS.md)
```

**Total:** 8 standard documents

### Target: aiterm/standards/

```
~/projects/dev-tools/aiterm/standards/
├── README.md                    # aiterm-specific overview
├── adhd/                        # Synced from zsh-config
├── code/                        # Synced from zsh-config
├── documentation/               # NEW: aiterm-specific docs standards
├── project/                     # Synced from zsh-config
└── workflow/                    # Synced from zsh-config
```

---

## 🔄 Sync Strategy Options

### Option 1: Git Submodule ⭐ (Recommended)

**Approach:** Use git submodule to reference zsh-configuration/standards/

**Pros:**
- ✅ Single source of truth enforced by git
- ✅ Version-pinned (know exactly which version)
- ✅ Updates require explicit `git submodule update`
- ✅ Standard git workflow (commit hash tracks version)
- ✅ No duplication, no drift

**Cons:**
- ❌ Submodules are complex for newcomers
- ❌ Requires initialization (`git submodule init`)
- ❌ Extra step to update (`git submodule update --remote`)

**Implementation:**

```bash
# In aiterm repo
git submodule add ../../zsh-configuration standards/zsh-config-standards
git submodule update --init --recursive

# Create symlinks to specific folders
ln -s zsh-config-standards/standards/adhd standards/adhd
ln -s zsh-config-standards/standards/code standards/code
ln -s zsh-config-standards/standards/project standards/project
ln -s zsh-config-standards/standards/workflow standards/workflow

# Update to latest
git submodule update --remote standards/zsh-config-standards
git add standards/zsh-config-standards
git commit -m "chore(standards): update to latest zsh-configuration standards"
```

**Workflow:**
1. zsh-configuration updates standards → commit
2. aiterm runs `git submodule update --remote`
3. aiterm commits the submodule pointer update
4. Standards automatically in sync

---

### Option 2: Symbolic Links ⭐⭐

**Approach:** Symlink aiterm/standards/ → zsh-configuration/standards/

**Pros:**
- ✅ Real-time sync (changes immediately visible)
- ✅ Simple to set up
- ✅ Works locally without git complexity
- ✅ Single source of truth on filesystem

**Cons:**
- ❌ Breaks if zsh-configuration moves
- ❌ Doesn't work for external users (cloning aiterm only)
- ❌ Not tracked in git (symlinks are local)
- ❌ Only works for DT's machine

**Implementation:**

```bash
# In aiterm repo
cd ~/projects/dev-tools/aiterm/standards

# Remove created directories
rm -rf adhd code project workflow

# Create symlinks
ln -s ../../zsh-configuration/standards/adhd adhd
ln -s ../../zsh-configuration/standards/code code
ln -s ../../zsh-configuration/standards/project project
ln -s ../../zsh-configuration/standards/workflow workflow

# Add to .gitignore
echo "standards/adhd" >> .gitignore
echo "standards/code" >> .gitignore
echo "standards/project" >> .gitignore
echo "standards/workflow" >> .gitignore
```

**Workflow:**
1. Edit files in zsh-configuration/standards/
2. Changes immediately visible in aiterm/standards/
3. No sync step needed

**Best for:** DT's local development only

---

### Option 3: Copy + Sync Script ⭐⭐⭐ (Best for External Users)

**Approach:** Copy standards files, provide sync script to update

**Pros:**
- ✅ Works for external users (files in repo)
- ✅ No git complexity (submodules)
- ✅ No broken symlinks
- ✅ Can customize per-project if needed
- ✅ Clear sync process (run script)

**Cons:**
- ❌ Files can drift if sync not run
- ❌ Manual sync step required
- ❌ Duplication (storage)

**Implementation:**

```bash
# Create sync script
cat > scripts/sync-standards.sh <<'EOF'
#!/bin/bash
# Sync standards from zsh-configuration

SOURCE="$HOME/projects/dev-tools/zsh-configuration/standards"
TARGET="$(dirname "$0")/../standards"

echo "Syncing standards from zsh-configuration..."

# Sync each directory
rsync -av --delete "$SOURCE/adhd/" "$TARGET/adhd/"
rsync -av --delete "$SOURCE/code/" "$TARGET/code/"
rsync -av --delete "$SOURCE/project/" "$TARGET/project/"
rsync -av --delete "$SOURCE/workflow/" "$TARGET/workflow/"

# Update README with sync timestamp
echo "Last synced: $(date)" >> "$TARGET/README.md"

echo "✅ Standards synced successfully"
EOF

chmod +x scripts/sync-standards.sh
```

**Workflow:**
1. zsh-configuration updates standards → commit
2. aiterm runs `./scripts/sync-standards.sh`
3. aiterm commits updated files
4. External users get files in repo (no sync needed)

---

### Option 4: Git Subtree

**Approach:** Use git subtree to merge zsh-configuration/standards/ into aiterm

**Pros:**
- ✅ Standards files in aiterm repo (works for external users)
- ✅ No submodule complexity
- ✅ Can pull updates with `git subtree pull`
- ✅ Can push aiterm-specific changes back to zsh-config

**Cons:**
- ❌ More complex than copy
- ❌ Subtree history can be confusing
- ❌ Harder to understand what changed

**Implementation:**

```bash
# Initial setup
git subtree add --prefix standards/upstream \
  ../zsh-configuration main --squash

# Pull updates
git subtree pull --prefix standards/upstream \
  ../zsh-configuration main --squash

# Create symlinks
ln -s upstream/standards/adhd standards/adhd
ln -s upstream/standards/code standards/code
# ...
```

---

### Option 5: npm-style "install" + Lock File

**Approach:** Copy standards, track version in lock file

**Pros:**
- ✅ Version-pinned (like package.json)
- ✅ Works for external users
- ✅ Clear upgrade path
- ✅ Can have multiple versions in monorepo

**Cons:**
- ❌ Custom tooling needed
- ❌ Over-engineered for this use case

**Implementation:**

```yaml
# standards.lock.yaml
version: "1.0.0"
source: "zsh-configuration/standards"
commit: "abc123def"
synced: "2025-12-19"
```

---

## 🎯 Recommended Hybrid Approach

**For DT (Local Development):** Option 2 (Symlinks)

```bash
# Quick, real-time sync, works great for you
cd ~/projects/dev-tools/aiterm/standards
ln -s ../../zsh-configuration/standards/adhd adhd
ln -s ../../zsh-configuration/standards/code code
ln -s ../../zsh-configuration/standards/project project
ln -s ../../zsh-configuration/standards/workflow workflow
```

**For External Users:** Option 3 (Copy + Sync Script)

```bash
# Initial sync (run once when cloning)
./scripts/sync-standards.sh

# Standards files committed to repo
# Users get them automatically on clone
```

**For Both:** Keep documentation/ as aiterm-specific

```
standards/
├── README.md              # aiterm-specific overview
├── adhd/                  # → symlink (DT) / copied files (external)
├── code/                  # → symlink (DT) / copied files (external)
├── project/               # → symlink (DT) / copied files (external)
├── workflow/              # → symlink (DT) / copied files (external)
└── documentation/         # aiterm-specific (not synced)
    ├── MKDOCS-GUIDE.md
    ├── API-DOCS-GUIDE.md
    └── INTERACTIVE-TUTORIAL-GUIDE.md
```

---

## 📁 aiterm-Specific Standards (documentation/)

**Not synced from zsh-configuration** - these are unique to aiterm:

### documentation/MKDOCS-GUIDE.md

**Purpose:** Guidelines for writing MkDocs documentation

**Contents:**
- MkDocs structure conventions
- Navigation organization
- Markdown extensions to use
- Code block styling
- Admonition usage

### documentation/API-DOCS-GUIDE.md

**Purpose:** Python API documentation standards

**Contents:**
- Docstring format (Google/NumPy style)
- Type hint conventions
- Example code in docstrings
- Sphinx/pdoc3 integration

### documentation/INTERACTIVE-TUTORIAL-GUIDE.md

**Purpose:** Creating web-based interactive tutorials

**Contents:**
- HTML/CSS structure
- Live code preview setup
- Download generated code feature
- Hosting on GitHub Pages

---

## 🔄 Sync Workflow Comparison

### DT's Workflow (Symlink Approach)

```bash
# Day 1: Set up symlinks (one-time)
cd ~/projects/dev-tools/aiterm/standards
ln -s ../../zsh-configuration/standards/adhd adhd
ln -s ../../zsh-configuration/standards/code code
ln -s ../../zsh-configuration/standards/project project
ln -s ../../zsh-configuration/standards/workflow workflow

# Day 2+: Edit standards in zsh-configuration
cd ~/projects/dev-tools/zsh-configuration/standards
vim adhd/QUICK-START-TEMPLATE.md  # Edit

# Changes automatically visible in aiterm
cd ~/projects/dev-tools/aiterm
cat standards/adhd/QUICK-START-TEMPLATE.md  # ✅ Updated!

# Commit in zsh-configuration
cd ~/projects/dev-tools/zsh-configuration
git add standards/adhd/QUICK-START-TEMPLATE.md
git commit -m "docs(standards): update quick-start template"

# No action needed in aiterm (symlinks track changes)
```

**Pros:** Zero sync overhead, real-time updates
**Cons:** Only works on DT's machine

---

### External User Workflow (Copy + Sync Script)

```bash
# Day 1: Clone aiterm
git clone https://github.com/Data-Wise/aiterm
cd aiterm

# Standards already in repo (committed files)
ls standards/adhd/  # ✅ Files present

# Day 30: DT updates standards in zsh-configuration
# DT runs sync script
cd ~/projects/dev-tools/aiterm
./scripts/sync-standards.sh  # ✅ Synced

# DT commits
git add standards/
git commit -m "chore(standards): sync from zsh-configuration"
git push

# External user updates
git pull  # ✅ Gets updated standards
```

**Pros:** Works for everyone, standards tracked in git
**Cons:** Manual sync step (but DT does it)

---

## 📊 Decision Matrix

| Approach | DT's Ease | External Users | Git Tracked | Real-time | Complexity |
|----------|-----------|----------------|-------------|-----------|------------|
| **Submodule** | ⭐⭐ | ⭐⭐ | ✅ | ❌ | 🔴 High |
| **Symlinks** | ⭐⭐⭐ | ❌ | ❌ | ✅ | 🟢 Low |
| **Copy + Sync** | ⭐⭐⭐ | ⭐⭐⭐ | ✅ | ❌ | 🟢 Low |
| **Subtree** | ⭐⭐ | ⭐⭐⭐ | ✅ | ❌ | 🔴 High |
| **Lock File** | ⭐ | ⭐⭐ | ✅ | ❌ | 🔴 High |

**Winner:** Copy + Sync Script (best balance)

---

## 🎯 Implementation Plan

### Phase 1: Initial Setup (Today)

```bash
# 1. Create sync script
./scripts/sync-standards.sh

# 2. Run initial sync
./scripts/sync-standards.sh

# 3. Create aiterm-specific docs
mkdir -p standards/documentation
touch standards/documentation/MKDOCS-GUIDE.md
touch standards/documentation/API-DOCS-GUIDE.md
touch standards/documentation/INTERACTIVE-TUTORIAL-GUIDE.md

# 4. Create standards README
cat > standards/README.md <<'EOF'
# aiterm Standards

Standards for the aiterm project.

**Source:** Most standards synced from `zsh-configuration/standards/`
**Sync:** Run `./scripts/sync-standards.sh` to update

## Directories

- `adhd/` - ADHD-friendly templates (synced)
- `code/` - Coding standards (synced)
- `project/` - Project structure (synced)
- `workflow/` - Git workflow (synced)
- `documentation/` - Documentation guides (aiterm-specific)
EOF

# 5. Commit
git add standards/ scripts/sync-standards.sh
git commit -m "chore(standards): set up sync from zsh-configuration"
```

### Phase 2: DT's Local Optimization (Optional)

```bash
# Convert to symlinks for real-time sync (DT's machine only)
cd ~/projects/dev-tools/aiterm
rm -rf standards/adhd standards/code standards/project standards/workflow
ln -s ../../zsh-configuration/standards/adhd standards/adhd
ln -s ../../zsh-configuration/standards/code standards/code
ln -s ../../zsh-configuration/standards/project standards/project
ln -s ../../zsh-configuration/standards/workflow standards/workflow

# Add to .gitignore (so symlinks aren't committed)
echo "standards/adhd" >> .gitignore
echo "standards/code" >> .gitignore
echo "standards/project" >> .gitignore
echo "standards/workflow" >> .gitignore

# Before pushing, run sync to update committed files
./scripts/sync-standards.sh
```

### Phase 3: Maintenance (Ongoing)

**When zsh-configuration standards change:**

```bash
# DT's workflow
cd ~/projects/dev-tools/zsh-configuration
# Edit standards/...
git commit -m "docs(standards): update template"

cd ~/projects/dev-tools/aiterm
./scripts/sync-standards.sh  # Update committed files
git add standards/
git commit -m "chore(standards): sync from zsh-configuration"
git push
```

**External users:** Automatic on `git pull`

---

## 🚀 Benefits of This Approach

### For DT

✅ **Real-time edits** (if using symlinks locally)
✅ **Single source of truth** (zsh-configuration)
✅ **Simple sync** (one script)
✅ **No submodule complexity**

### For External Users

✅ **Just works** (standards in repo)
✅ **No setup** (files already there)
✅ **Updates via git pull** (standard workflow)
✅ **No broken symlinks**

### For aiterm Project

✅ **Consistent with other projects** (same standards)
✅ **Automatic updates** (when DT syncs)
✅ **Project-specific additions** (documentation/)
✅ **Clear version history** (git commits)

---

## 📝 Sync Script Features

### Basic Version

```bash
#!/bin/bash
# Sync standards from zsh-configuration

SOURCE="$HOME/projects/dev-tools/zsh-configuration/standards"
TARGET="$(dirname "$0")/../standards"

rsync -av --delete "$SOURCE/adhd/" "$TARGET/adhd/"
rsync -av --delete "$SOURCE/code/" "$TARGET/code/"
rsync -av --delete "$SOURCE/project/" "$TARGET/project/"
rsync -av --delete "$SOURCE/workflow/" "$TARGET/workflow/"

echo "✅ Standards synced"
```

### Advanced Version (with checks)

```bash
#!/bin/bash
# Sync standards from zsh-configuration (enhanced)

set -e  # Exit on error

SOURCE="$HOME/projects/dev-tools/zsh-configuration/standards"
TARGET="$(dirname "$0")/../standards"

# Check source exists
if [[ ! -d "$SOURCE" ]]; then
    echo "❌ Source not found: $SOURCE"
    echo "Clone zsh-configuration first:"
    echo "  git clone <url> ~/projects/dev-tools/zsh-configuration"
    exit 1
fi

# Confirm sync
echo "📦 Syncing standards from zsh-configuration..."
echo "   Source: $SOURCE"
echo "   Target: $TARGET"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Sync each directory
for dir in adhd code project workflow; do
    echo "  📁 Syncing $dir/..."
    rsync -av --delete "$SOURCE/$dir/" "$TARGET/$dir/"
done

# Update README timestamp
echo "" >> "$TARGET/README.md"
echo "Last synced: $(date '+%Y-%m-%d %H:%M:%S')" >> "$TARGET/README.md"

echo "✅ Standards synced successfully"
echo ""
echo "Next steps:"
echo "  git add standards/"
echo "  git commit -m 'chore(standards): sync from zsh-configuration'"
```

---

## 🎓 Alternative: Monorepo Approach (Future)

**If DT moves to monorepo structure:**

```
dev-tools/
├── packages/
│   ├── aiterm/
│   ├── zsh-configuration/
│   └── other-tools/
└── standards/           # Shared standards (symlinked by all)
    ├── adhd/
    ├── code/
    ├── project/
    └── workflow/
```

**Benefits:**
- Single source of truth at monorepo root
- All packages symlink to shared standards
- No sync needed (all packages share filesystem)

**Requires:** Restructuring all dev-tools into monorepo

---

## 📋 Summary & Recommendation

### Recommended Approach: Copy + Sync Script

**Why:**
- ✅ Simple for DT (one script to run)
- ✅ Works for external users (files in repo)
- ✅ No git complexity (no submodules)
- ✅ Clear version control (git history)
- ✅ Can optimize locally with symlinks if desired

**Implementation:**
1. Create `scripts/sync-standards.sh` script
2. Run initial sync to populate standards/
3. Commit synced files to repo
4. Add instructions to README
5. Run sync script when zsh-configuration changes

**Ongoing Workflow:**
```bash
# When zsh-configuration standards update
./scripts/sync-standards.sh
git add standards/
git commit -m "chore(standards): sync from zsh-configuration"
```

**Time Investment:** 15 minutes setup, 1 minute per sync

---

**Generated:** 2025-12-19
**Status:** 🟢 Ready to implement
**Recommended:** Copy + Sync Script (Option 3)
**Next Action:** Create sync script and run initial sync
