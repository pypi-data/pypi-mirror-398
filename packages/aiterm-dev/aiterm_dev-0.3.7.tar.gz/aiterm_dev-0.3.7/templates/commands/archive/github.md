# GitHub (ARCHIVED)

**Status:** DEPRECATED - Merged into `/git`
**Migration:** Use `/git` hub commands instead

---

This command has been archived as part of Phase 3 optimization.
GitHub functionality is now part of the `/git` hub:
- `/git pr` - Pull request management
- `/git status` - Repository status
- `/git history` - Commit history

## Migration Guide

| Old Command | New Command |
|-------------|-------------|
| `/github pr` | `/git pr` |
| `/github issues` | `/git` (use gh CLI directly) |
| `/github actions` | `/git` (use gh CLI directly) |
| `/github release` | `/git` (use gh CLI directly) |

## Note

For advanced GitHub operations not covered by `/git`, use the `gh` CLI directly.
The `/git` hub focuses on common git workflows including PR creation.
