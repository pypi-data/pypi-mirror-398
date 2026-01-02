# IDE Commands Reference

Quick reference for aiterm IDE integration commands.

## Commands

| Command | Description |
|---------|-------------|
| `ait ide list` | List supported IDEs and status |
| `ait ide status <ide>` | Show detailed IDE status |
| `ait ide extensions <ide>` | List AI extension recommendations |
| `ait ide configure <ide>` | Configure IDE settings |
| `ait ide terminal-profile <ide>` | Add aiterm terminal profile |
| `ait ide sync-theme <ide>` | Sync theme settings |
| `ait ide open <ide> [path]` | Open path in IDE |
| `ait ide compare` | Compare configs across IDEs |

## Supported IDEs

| IDE | Command | Config Path |
|-----|---------|-------------|
| VS Code | `code` | `~/.vscode/settings.json` |
| Cursor | `cursor` | `~/.cursor/settings.json` |
| Zed | `zed` | `~/.config/zed/settings.json` |
| Positron | `positron` | `~/.positron/settings.json` |
| Windsurf | `windsurf` | `~/.windsurf/settings.json` |

## Quick Setup

```bash
# Full IDE setup in 3 commands
ait ide terminal-profile vscode
ait ide configure vscode --font "JetBrains Mono" --size 13
ait ide sync-theme vscode --theme dark
```

## Configure Options

| Option | Description | Example |
|--------|-------------|---------|
| `--font` | Terminal font family | `--font "Fira Code"` |
| `--size` | Terminal font size | `--size 14` |
| `--ai` | Enable AI features | `--ai` |
| `--no-ai` | Disable AI features | `--no-ai` |

## Terminal Profile

Adds to VS Code/Cursor:
```json
"terminal.integrated.profiles.osx": {
  "aiterm": {
    "path": "/bin/zsh",
    "args": ["-l"],
    "env": {"AITERM": "1"}
  }
}
```

Adds to Zed:
```json
"terminal": {
  "shell": {"program": "/bin/zsh"},
  "env": {"AITERM": "1"}
}
```

## Theme Options

| Theme | Description |
|-------|-------------|
| `dark` | Dark color scheme (default) |
| `light` | Light color scheme |
| `solarized` | Solarized Dark |

```bash
ait ide sync-theme vscode --theme dark
ait ide sync-theme zed --theme solarized
```

## Recommended Extensions

### VS Code / Cursor
| Extension | ID | Purpose |
|-----------|---|---------|
| Continue | `continue.continue` | AI code assistant |
| Claude Dev | `saoudrizwan.claude-dev` | Claude in VS Code |
| GitHub Copilot | `github.copilot` | AI pair programmer |

### Zed
| Extension | Purpose |
|-----------|---------|
| Zed Assistant | Built-in AI assistant |

## Examples

```bash
# Check what's installed
ait ide list

# Setup VS Code for AI development
ait ide terminal-profile vscode
ait ide extensions vscode

# Configure Zed terminal
ait ide terminal-profile zed
ait ide configure zed --font "SF Mono" --size 12

# Open project in Cursor
ait ide open cursor ~/projects/myapp

# Compare all installed IDEs
ait ide compare
```

## Environment Variables

When using aiterm terminal profile:

| Variable | Value | Purpose |
|----------|-------|---------|
| `AITERM` | `1` | Signals aiterm integration |
| `TERM_PROGRAM` | IDE name | IDE identification |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| IDE not detected | Add CLI to PATH |
| Settings not saved | Check file permissions |
| Theme not applied | Restart IDE |
| Profile not visible | Restart IDE terminal |
