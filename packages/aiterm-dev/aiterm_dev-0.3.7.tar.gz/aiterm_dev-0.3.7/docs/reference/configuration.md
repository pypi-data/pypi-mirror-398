# Configuration Reference

## Shell Configuration

### Required in .zshrc

```zsh
# Must be before Oh My Zsh / Antidote loads
DISABLE_AUTO_TITLE="true"

# At end of .zshrc
source ~/path/to/aiterm/zsh/iterm2-integration.zsh
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TERM_PROGRAM` | Must be "iTerm.app" | Set by iTerm2 |
| `DISABLE_AUTO_TITLE` | Prevent OMZ title override | Not set |

## Integration Variables

These are set by the integration (read-only):

| Variable | Purpose |
|----------|---------|
| `_ITERM_CURRENT_PROFILE` | Currently active profile |
| `_ITERM_CURRENT_TITLE` | Current tab title |
| `_ITERM_HOOK_REGISTERED` | Prevents duplicate hooks |

## iTerm2 Configuration

### Title Settings

Path: Settings → Profiles → General → Title

| Setting | Recommended |
|---------|-------------|
| Title | Session Name |
| Alternative | Session Name + Job |

### For Triggers

Path: Settings → Profiles → Default → Advanced → Triggers

See [Triggers Guide](../guide/triggers.md) for setup.

## File Locations

| File | Location |
|------|----------|
| Integration script | `zsh/iterm2-integration.zsh` |
| Dynamic Profiles | `profiles/context-switcher-profiles.json` |
| iTerm2 Dynamic Profiles | `~/Library/Application Support/iTerm2/DynamicProfiles/` |
| iTerm2 Preferences | `~/Library/Preferences/com.googlecode.iterm2.plist` |

## Escape Sequences Used

| Sequence | Purpose |
|----------|---------|
| `\033]1337;SetProfile=NAME\007` | Switch profile |
| `\033]2;TITLE\007` | Set window title |
