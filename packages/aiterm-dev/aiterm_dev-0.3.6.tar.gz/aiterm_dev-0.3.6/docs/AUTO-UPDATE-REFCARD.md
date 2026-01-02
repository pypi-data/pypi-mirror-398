# Documentation Auto-Update Quick Reference

**One-page reference for the auto-update system**

---

## Quick Commands

```bash
# Run all updaters (interactive)
~/.claude/commands/workflow/lib/run-all-updaters.sh

# Auto mode (no prompts)
~/.claude/commands/workflow/lib/run-all-updaters.sh --auto

# Preview only (no changes)
~/.claude/commands/workflow/lib/run-all-updaters.sh --dry-run

# Individual updaters
~/.claude/commands/workflow/lib/update-changelog.sh [--apply]
~/.claude/commands/workflow/lib/update-mkdocs-nav.sh [--apply]
~/.claude/commands/workflow/lib/update-claude-md.sh [--apply]
```

---

## What Gets Updated

| File | What Changes | Safe? | Confirmation? |
|------|--------------|-------|---------------|
| `CHANGELOG.md` | Appends entries from commits | ✓ | No |
| `mkdocs.yml` | Adds new docs to navigation | ✓ | No |
| `.STATUS` / `CLAUDE.md` | Prepends session summary | ✓ | Yes |

---

## Conventional Commit Format

```
type(scope): subject

Examples:
feat(hooks): add wizard
fix(bug): resolve crash
docs: update guide
```

### Type Mapping

| Type | CHANGELOG Section |
|------|-------------------|
| `feat` | Added |
| `fix` | Fixed |
| `refactor`, `perf` | Changed |
| `docs` | Documentation |
| `test` | Tests |
| `build` | Build System |
| `ci` | CI/CD |

---

## mkdocs Section Detection

| Filename Pattern | Nav Section |
|------------------|-------------|
| `*API*`, `*ARCHITECTURE*` | Reference |
| `*GUIDE*`, `*INTEGRATION*` | User Guide |
| `*TUTORIAL*` | Tutorials |
| `*QUICKSTART*` | Getting Started |
| `*PHASE*`, `*DESIGN*`, `*PROGRESS*` | Development |

---

## Safety Features

- **Automatic backups:** `.backup-YYYYMMDD-HHMMSS`
- **Dry-run default:** Individual updaters preview by default
- **Validation:** `mkdocs build --strict` before saving
- **Auto-rollback:** Reverts on validation failure
- **Show diffs:** Always see changes before committing

---

## Rollback

```bash
# CHANGELOG
mv CHANGELOG.md.backup-YYYYMMDD-HHMMSS CHANGELOG.md

# mkdocs.yml
mv mkdocs.yml.backup-YYYYMMDD-HHMMSS mkdocs.yml

# .STATUS
mv .STATUS.backup-YYYYMMDD-HHMMSS .STATUS
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No new commits" | CHANGELOG is current, or make commits |
| "Missing [Unreleased] section" | Add `## [Unreleased]` to CHANGELOG.md |
| Wrong mkdocs section | Move manually, or rename file |
| Duplicate .STATUS sections | Use `## ✅ Just Completed (YYYY-MM-DD)` format |
| Build fails | Auto-rollback happens, check `mkdocs build --strict` |

---

## Integration with /workflow:done

The auto-updater runs as **Step 1.6** automatically:

```
/workflow:done
  ↓
Step 1.5: Detect issues
Step 1.6: Auto-update ← Here!
  ↓
Step 2: Session summary
```

**No extra commands needed** - just use `/workflow:done`

---

## Best Practices

1. **Use conventional commits** for better CHANGELOG entries
2. **Run after every session** to keep docs current
3. **Preview big changes** with `--dry-run` first
4. **Create docs in `docs/`** for automatic detection
5. **Review auto-summaries** before committing

---

## Time Savings

- **Manual:** 10-15 min/session
- **Automatic:** 30 seconds/session
- **Saved:** ~15 min/session = ~6 hours/month

---

## Configuration (Optional)

Create `.changelog-config.json`:

```json
{
  "skip_types": ["chore", "build", "ci"],
  "group_by": "type",
  "include_scope": true,
  "link_commits": true,
  "repo_url": "https://github.com/username/repo"
}
```

---

## Help

```bash
# Individual updater help
~/.claude/commands/workflow/lib/update-changelog.sh --help
~/.claude/commands/workflow/lib/update-mkdocs-nav.sh --help
~/.claude/commands/workflow/lib/update-claude-md.sh --help
~/.claude/commands/workflow/lib/run-all-updaters.sh --help
```

---

**Full Tutorial:** `docs/AUTO-UPDATE-TUTORIAL.md`

**Design Docs:** `PHASE-2-DESIGN.md`, `PHASE-2-COMPLETE.md`
