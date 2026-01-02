# Shell Completion

aiterm provides tab completion for all commands, subcommands, and options.

## Quick Setup

### Zsh (Recommended)

```bash
# Install completion
aiterm --install-completion zsh

# Or manually add to ~/.zshrc
eval "$(aiterm --show-completion zsh)"
```

### Bash

```bash
# Install completion
aiterm --install-completion bash

# Or manually add to ~/.bashrc
eval "$(aiterm --show-completion bash)"
```

### Fish

```bash
# Install completion
aiterm --install-completion fish
```

## What Gets Completed

| Type | Example |
|------|---------|
| Commands | `ait cl<TAB>` → `claude` |
| Subcommands | `ait claude ap<TAB>` → `approvals` |
| Options | `ait --<TAB>` → `--help`, `--version` |
| Arguments | `ait hooks install <TAB>` → template names |

## Usage Examples

```bash
# Complete commands
ait <TAB>
# → claude  context  detect  doctor  docs  hooks  init  mcp  profile  switch

# Complete subcommands
ait claude <TAB>
# → approvals  backup  settings

# Complete nested subcommands
ait claude approvals <TAB>
# → add  list  presets

# Complete options
ait doctor --<TAB>
# → --help
```

## Troubleshooting

### Completion Not Working

1. **Restart shell** after installing completion
2. **Check shell type**: `echo $SHELL`
3. **Verify installation**:
   ```bash
   # Zsh
   grep -l "aiterm" ~/.zfunc/* 2>/dev/null

   # Bash
   grep "aiterm" ~/.bash_completion 2>/dev/null
   ```

### Manual Installation (Zsh)

If `--install-completion` doesn't work:

```bash
# Create completion directory
mkdir -p ~/.zfunc

# Generate completion script
aiterm --show-completion zsh > ~/.zfunc/_aiterm

# Add to ~/.zshrc (before compinit)
fpath=(~/.zfunc $fpath)
autoload -Uz compinit && compinit
```

### Manual Installation (Bash)

```bash
# Generate completion script
aiterm --show-completion bash > ~/.aiterm-complete.bash

# Add to ~/.bashrc
source ~/.aiterm-complete.bash
```

## Alias Completion

If using the `ait` alias, completion works automatically because `ait` is a symlink to `aiterm`.

```bash
# Both work the same
aiterm <TAB>
ait <TAB>
```

## Related

- [Quick Start](../QUICK-START.md) - Get started with aiterm
- [Reference Card](../REFCARD.md) - Command quick reference
