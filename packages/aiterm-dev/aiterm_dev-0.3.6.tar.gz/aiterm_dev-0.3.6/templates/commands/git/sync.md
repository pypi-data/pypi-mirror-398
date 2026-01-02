---
description: Smart git sync with safety checks
category: git
---

# Git Sync - Smart pull/push with safety

This command performs a safe git sync operation:
1. Checks for uncommitted changes
2. Stashes if needed
3. Pulls latest changes
4. Pushes local commits
5. Pops stash if applicable

## Usage

Just run `/git:sync` and I'll handle the rest!

## What I'll do

1. **Check status** - Are there uncommitted changes?
2. **Stash if needed** - Save work in progress
3. **Pull** - Get latest from remote
4. **Push** - Send your commits
5. **Restore stash** - Return to your work

## Safety checks

- Won't pull if you have conflicts
- Won't push if remote has new commits
- Stashes changes safely
- Shows clear status at each step

## Example

```bash
# Check current status
git status

# Stash changes if any
git stash push -m "Auto-stash before sync"

# Pull latest
git pull --rebase

# Push local commits
git push

# Restore stash if we created one
git stash pop
```

Please proceed with the sync!
