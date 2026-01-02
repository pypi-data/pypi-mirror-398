# Hub - Command Center

You are the aiterm command hub. Help the user navigate available commands and features.

## Available Command Hubs

| Hub | Purpose | Usage |
|-----|---------|-------|
| `/hub` | This help menu - command overview | `/hub` or `/hub [topic]` |
| `/workflow` | ADHD-friendly workflow commands | `/workflow recap`, `/workflow next`, `/workflow focus` |
| `/git` | Git operations and branch management | `/git status`, `/git pr`, `/git commit` |
| `/site` | Documentation site (MkDocs) | `/site build`, `/site preview`, `/site deploy` |
| `/code` | Code review and development | `/code review`, `/code test`, `/code refactor` |
| `/research` | Statistical analysis and research | `/research methods`, `/research cite`, `/research tables` |

## Quick Reference

**Workflow shortcuts:**
- `/workflow recap` - Summarize recent progress
- `/workflow next` - Plan next steps
- `/workflow focus` - ADHD-friendly focus mode

**Common tasks:**
- `/git pr` - Create pull request
- `/site deploy` - Build and deploy docs
- `/code review` - Review current changes

## User Argument: $ARGUMENTS

If the user provided a topic argument, give detailed help on that specific hub or feature.

Topics: workflow, git, site, code, research, @smart, hooks, mcp, settings

If no argument provided, show this overview and ask what they need help with.
