# IDE Integration

Configure VS Code, Cursor, Zed, and other IDEs for optimal AI-assisted development.

## Overview

aiterm provides IDE integration to:

- **Configure terminals** with aiterm-optimized profiles
- **Install AI extensions** recommended for each IDE
- **Sync themes** across your development environment
- **Manage settings** programmatically

## Supported IDEs

| IDE | Terminal | Extensions | AI Features |
|-----|----------|------------|-------------|
| **VS Code** | Full | Full | Copilot, Continue, Claude Dev |
| **Cursor** | Full | Full | Built-in AI |
| **Zed** | Full | Limited | Built-in Assistant |
| **Positron** | Full | Full | R/Python focused |
| **Windsurf** | Full | Full | Built-in AI |

## Quick Start

```bash
# Check which IDEs are installed
ait ide list

# Get detailed status
ait ide status vscode

# Add aiterm terminal profile
ait ide terminal-profile vscode

# See recommended extensions
ait ide extensions vscode
```

## Commands

### `ait ide list`

Show all supported IDEs and their installation status.

```bash
$ ait ide list

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ IDE             ┃ Installed ┃ Config Exists ┃ Features              ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Visual Studio   │    ✓      │      ✓        │ terminal, extensions, │
│ Code            │           │               │ keybindings           │
│ Cursor          │    ✓      │      ✓        │ terminal, ai-features │
│ Zed             │    ✓      │      ✗        │ terminal, themes      │
│ Positron        │    ✗      │      ✗        │ terminal, r-support   │
│ Windsurf        │    ✗      │      ✗        │ terminal, ai-features │
└─────────────────┴───────────┴───────────────┴───────────────────────┘
```

### `ait ide status <ide>`

Show detailed configuration for a specific IDE.

```bash
$ ait ide status vscode

╭─────────────── Visual Studio Code Status ────────────────╮
│ Name: Visual Studio Code                                  │
│ Installed: Yes                                            │
│ Config Path: ~/.vscode/settings.json                      │
│ Config Exists: Yes                                        │
│ Features: terminal, extensions, keybindings, tasks        │
│ Settings Keys: 42                                         │
╰──────────────────────────────────────────────────────────╯
```

### `ait ide extensions <ide>`

List recommended AI development extensions.

```bash
$ ait ide extensions vscode

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Extension       ┃ ID                       ┃ Description           ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Continue        │ continue.continue        │ AI code assistant     │
│ Claude Dev      │ saoudrizwan.claude-dev   │ Claude Code in VS     │
│ GitHub Copilot  │ github.copilot           │ AI pair programmer    │
└─────────────────┴─────────────────────────┴───────────────────────┘
```

### `ait ide configure <ide>`

Configure IDE settings for AI development.

```bash
# Set terminal font and size
ait ide configure vscode --font "JetBrains Mono" --size 14

# Enable AI features
ait ide configure vscode --ai

# Disable AI inline suggestions
ait ide configure cursor --no-ai
```

**Options:**

| Option | Description |
|--------|-------------|
| `--font` | Terminal font family |
| `--size` | Terminal font size |
| `--ai / --no-ai` | Enable/disable AI features |

### `ait ide terminal-profile <ide>`

Add an aiterm-optimized terminal profile.

```bash
# Add default profile
ait ide terminal-profile vscode

# Custom profile name
ait ide terminal-profile vscode --name "aiterm-dev"
```

This adds a terminal profile with:

- `/bin/zsh` with login shell
- `AITERM=1` environment variable
- Proper `TERM_PROGRAM` setting

### `ait ide sync-theme <ide>`

Sync terminal theme with aiterm profiles.

```bash
# Dark theme (default)
ait ide sync-theme vscode

# Light theme
ait ide sync-theme vscode --theme light

# Solarized
ait ide sync-theme zed --theme solarized
```

**Available themes:**

- `dark` - Dark color scheme
- `light` - Light color scheme
- `solarized` - Solarized Dark

### `ait ide open <ide>`

Open a path in the specified IDE.

```bash
# Open current directory
ait ide open vscode

# Open specific path
ait ide open zed ~/projects/myapp
```

### `ait ide compare`

Compare configurations across installed IDEs.

```bash
$ ait ide compare

IDE Configuration Comparison

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Setting         ┃ VS Code       ┃ Cursor  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Config exists   │ Yes           │ Yes     │
│ Terminal font   │ JetBrains Mono│ default │
│ AI enabled      │ Yes           │ Yes     │
└─────────────────┴───────────────┴─────────┘
```

## IDE-Specific Setup

### VS Code / Cursor

VS Code and Cursor share similar settings formats.

**Recommended Setup:**

```bash
# 1. Add terminal profile
ait ide terminal-profile vscode

# 2. Configure terminal
ait ide configure vscode --font "JetBrains Mono" --size 13

# 3. View extensions
ait ide extensions vscode
```

**Config Path:** `~/.vscode/settings.json` or `~/.cursor/settings.json`

**Key Settings Added:**

```json
{
  "terminal.integrated.profiles.osx": {
    "aiterm": {
      "path": "/bin/zsh",
      "args": ["-l"],
      "env": {
        "AITERM": "1",
        "TERM_PROGRAM": "vscode"
      }
    }
  },
  "terminal.integrated.fontFamily": "JetBrains Mono",
  "terminal.integrated.fontSize": 13
}
```

### Zed

Zed uses a different settings format (JSON with different keys).

**Recommended Setup:**

```bash
# 1. Configure terminal
ait ide terminal-profile zed

# 2. Set theme
ait ide sync-theme zed --theme dark
```

**Config Path:** `~/.config/zed/settings.json`

**Key Settings Added:**

```json
{
  "terminal": {
    "shell": {
      "program": "/bin/zsh",
      "args": ["-l"]
    },
    "env": {
      "AITERM": "1"
    },
    "font_family": "JetBrains Mono",
    "font_size": 13
  },
  "assistant": {
    "enabled": true
  },
  "theme": "One Dark"
}
```

### Positron

Positron is an IDE for data science with R and Python support.

**Recommended Setup:**

```bash
# 1. Check status
ait ide status positron

# 2. Add terminal profile
ait ide terminal-profile positron
```

**Config Path:** `~/.positron/settings.json`

### Windsurf

Windsurf is an AI-native IDE similar to Cursor.

**Recommended Setup:**

```bash
ait ide terminal-profile windsurf
ait ide configure windsurf --ai
```

**Config Path:** `~/.windsurf/settings.json`

## Integration with Claude Code

When using Claude Code from within an IDE terminal:

1. The `AITERM=1` env var signals aiterm integration
2. Context detection works the same as regular terminal
3. Session coordination tracks IDE-based sessions

**Workflow:**

```bash
# Open project in IDE
ait ide open vscode ~/projects/myapp

# Start Claude Code in IDE terminal
claude

# aiterm hooks detect the session automatically
ait sessions live
```

## Troubleshooting

### IDE Not Detected

If `ait ide list` shows an IDE as not installed:

1. Ensure the IDE's CLI command is in PATH
2. For VS Code: Run "Install 'code' command in PATH" from command palette
3. For Zed: Add `/Applications/Zed.app/Contents/MacOS` to PATH

### Settings Not Applied

If changes don't appear after running configure commands:

1. Restart the IDE
2. Check the config file directly
3. Verify no syntax errors in settings JSON

```bash
# Check if settings file is valid JSON
python -m json.tool ~/.vscode/settings.json
```

### Permission Errors

If settings can't be saved:

```bash
# Ensure directory exists
mkdir -p ~/.vscode
mkdir -p ~/.config/zed

# Check permissions
ls -la ~/.vscode/settings.json
```
