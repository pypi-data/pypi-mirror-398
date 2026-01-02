---
description: Create GitHub pull request with template
category: git
---

# Create Pull Request

This command helps create a well-formatted GitHub pull request.

## Usage

Run `/git:pr` and I'll:
1. Check current branch and commits
2. Generate PR title from commits
3. Create PR summary
4. Use `gh pr create` to submit

## What I need from you

- Current branch should have commits to merge
- GitHub CLI (`gh`) should be authenticated
- Target branch (I'll ask if not main)

## PR Template

I'll create a PR with:

**Title**: Based on your commits or branch name

**Body**:
```markdown
## Summary
- [Bullet points of changes]

## Changes
- [List of key changes]

## Testing
- [ ] Tested locally
- [ ] Tests pass
- [ ] No breaking changes

## Screenshots
[If applicable]
```

Please confirm you want to create a PR!
