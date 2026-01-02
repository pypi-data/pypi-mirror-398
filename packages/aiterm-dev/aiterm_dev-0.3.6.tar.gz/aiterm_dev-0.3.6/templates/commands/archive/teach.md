# Teach (ARCHIVED)

**Status:** DEPRECATED - Merged into `/research`
**Migration:** Use `/research` hub or create custom skill

---

This command has been archived as part of Phase 3 optimization.
Teaching functionality is now part of:
- `/research` hub for academic content
- Custom skills for grading workflows (see `templates/skills/`)

## Migration Guide

| Old Command | New Command |
|-------------|-------------|
| `/teach grade` | Custom grading skill |
| `/teach feedback` | Custom feedback skill |
| `/teach rubric` | Custom rubric skill |
| `/teach explain` | `/code explain` or `/research` |

## Recommendation

For teaching workflows, create a custom skill:
```
~/.claude/skills/teaching/SKILL.md
```

See IDEAS.md for teaching skill templates.
