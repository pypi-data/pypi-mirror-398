# Command Templates

Claude Code slash command templates for aiterm.

## Directory Structure

```
commands/
├── hubs/           # 6 core hub commands (active)
│   ├── hub.md      # Command center & help
│   ├── workflow.md # ADHD-friendly task management
│   ├── git.md      # Git operations
│   ├── site.md     # Documentation site (MkDocs)
│   ├── code.md     # Development operations
│   └── research.md # Statistical analysis & research
│
└── archive/        # Deprecated commands (for reference)
    ├── help.md     # → merged into /hub
    ├── math.md     # → merged into /research
    ├── write.md    # → distributed across hubs
    ├── github.md   # → merged into /git
    └── teach.md    # → merged into /research + skills
```

## Installation

Copy hub commands to your Claude Code commands directory:

```bash
# Copy all hubs
cp templates/commands/hubs/*.md ~/.claude/commands/

# Or install specific hubs
cp templates/commands/hubs/workflow.md ~/.claude/commands/
```

## Usage

After installation, use in Claude Code:

```
/hub                    # Show all available commands
/hub workflow           # Get help on workflow commands
/workflow recap         # Summarize recent progress
/workflow next          # Plan next steps
/git pr                 # Create pull request
/site deploy            # Deploy documentation
/code review            # Review current changes
/research methods       # Statistical methods guidance
```

## Phase 3 Optimization Summary

**Before:** 10+ scattered commands
**After:** 6 focused hub commands

| Kept (Hubs) | Archived | Reason |
|-------------|----------|--------|
| /hub | /help | Consolidated into /hub |
| /workflow | - | Core ADHD workflow |
| /git | /github | Git + GitHub merged |
| /site | - | Docs management |
| /code | - | Development ops |
| /research | /math, /teach | Academic work consolidated |

**Result:** 40% reduction, clearer command structure, better discoverability.

## Customization

These are templates. Feel free to:
- Modify prompts for your workflow
- Add project-specific commands
- Create additional hubs as needed

## Related

- `templates/skills/` - Reusable AI workflows
- `templates/hooks/` - Event-triggered scripts
- `IDEAS.md` - Full feature roadmap
