# StatusLine Alternative Color Themes

Replace the bright yellow colors in your Claude Code statusLine with ADHD-friendly, eye-strain-reducing alternatives.

## Quick Start

### 1. Preview Themes

```bash
# Preview each theme to see how it looks
bash preview-theme.sh cool-blues
bash preview-theme.sh forest-greens
bash preview-theme.sh purple-charcoal
```

### 2. Install Your Favorite

```bash
# Install Cool Blues & Grays (professional, calming)
bash install-theme.sh cool-blues

# Install Forest Greens & Dark (nature-inspired, warm)
bash install-theme.sh forest-greens

# Install Purple & Charcoal (minimal stimulation, sophisticated)
bash install-theme.sh purple-charcoal
```

### 3. Start Claude Code

```bash
claude
# Your new theme will appear in the status line!
```

## What's Fixed?

The current statusLine uses **bright yellow** (`38;5;214`) for the session duration timer, which can cause eye strain during long coding sessions. These themes replace all bright yellows with calmer, more subdued alternatives.

### Before (Current)
```
╰─ Sonnet 4.5 │ 14:30 │ ⏱ 12m │ +43/-12 │ ⚡84% W:11%
                           ^^^ Bright yellow (eye strain)
```

### After (Any Theme)
```
╰─ Sonnet 4.5 │ 14:30 │ ⏱ 12m │ +43/-12 │ ⚡84% W:11%
                           ^^^ Calm color (no eye strain)
```

## Theme Comparison

| Theme | Best For | Key Feature |
|-------|----------|-------------|
| **Cool Blues & Grays** | Professional work, all-day sessions | Monochromatic blue-gray, calming |
| **Forest Greens & Dark** | Reducing eye fatigue, nature lovers | Earth tones, warm but not bright |
| **Purple & Charcoal** | Late-night coding, ADHD optimization | Low contrast, minimal stimulation |

See `COMPARISON.md` for detailed comparison table and color specifications.

## Files

- `theme-cool-blues.sh` - Cool Blues & Grays color definitions
- `theme-forest-greens.sh` - Forest Greens & Dark color definitions
- `theme-purple-charcoal.sh` - Purple & Charcoal color definitions
- `preview-theme.sh` - Visual preview script
- `install-theme.sh` - Automatic installation script
- `COMPARISON.md` - Detailed comparison and documentation

## Switching Themes

You can easily switch between themes:

```bash
# Try Cool Blues for daytime
bash install-theme.sh cool-blues

# Switch to Purple & Charcoal for evening
bash install-theme.sh purple-charcoal
```

Each installation creates a timestamped backup of your current statusLine.

## Restore Original

Your original statusLine is backed up automatically. To restore:

```bash
# Find your backup
ls ~/.claude/statusline-p10k.sh.backup-*

# Restore the most recent backup
cp ~/.claude/statusline-p10k.sh.backup-YYYYMMDD-HHMMSS ~/.claude/statusline-p10k.sh
```

## Quick Fix (Without Full Theme)

If you just want to fix the bright yellow duration without changing the entire theme:

```bash
# Edit ~/.claude/statusline-p10k.sh and find line 485:
# Change: 38;5;214m⏱
# To:     38;5;109m⏱

# Or run this one-liner:
sed -i.bak 's/38;5;214m⏱/38;5;109m⏱/g' ~/.claude/statusline-p10k.sh
```

## Creating Your Own Theme

1. Copy one of the `theme-*.sh` files
2. Modify the color codes (ANSI 256 colors: 0-255)
3. Test with `preview-theme.sh`
4. Apply with `install-theme.sh`

**Color reference:** https://www.ditig.com/256-colors-cheat-sheet

## Support

- See `COMPARISON.md` for detailed documentation
- Check project CLAUDE.md for statusLine architecture
- ANSI 256 color chart: https://www.ditig.com/256-colors-cheat-sheet
- StatusLine docs: https://code.claude.com/docs/en/statusline.md
