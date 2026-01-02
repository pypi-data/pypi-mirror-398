# StatusLine Color Theme Comparison

**Problem:** The current Powerlevel10k-inspired statusLine uses bright yellow (`38;5;214`) for the session duration, which can cause eye strain during long coding sessions.

**Solution:** Three alternative color schemes that eliminate bright yellow while maintaining readability and visual hierarchy.

---

## 📊 Quick Comparison Table

| Feature | Current (Bright) | Cool Blues & Grays | Forest Greens & Dark | Purple & Charcoal |
|---------|------------------|--------------------|-----------------------|-------------------|
| **Primary Issue** | Bright yellow (214) | ✅ Resolved | ✅ Resolved | ✅ Resolved |
| **Directory BG** | Blue (4) | Steel blue (67) | Forest green (22) | Deep purple (54) |
| **Git Clean BG** | Green (2) | Slate blue (24) | Deep green (28) | Charcoal (236) |
| **Git Modified BG** | Yellow (3) ⚠️ | Blue-gray (60) | Olive green (58) | Slate purple (60) |
| **Time Color** | Cyan (75) | Soft cyan (116) | Sage green (108) | Lavender (183) |
| **Duration Color** | **Bright yellow (214)** ⚠️ | **Gray-blue (109)** ✅ | **Muted olive (143)** ✅ | **Muted mauve (139)** ✅ |
| **Quota 50-80%** | Yellow (220) ⚠️ | Medium cyan (74) | Khaki (143) | Mauve (139) |
| **ADHD-Friendly** | ❌ High contrast | ✅ Calming | ✅ Nature-inspired | ✅ Minimal stimulation |
| **Eye Strain** | ❌ High | ✅ Low | ✅ Very low | ✅ Minimal |
| **Best For** | Bright screens | Professional work | Long sessions | Late-night coding |

---

## 🎨 Theme Details

### Theme 1: Cool Blues & Grays
**Philosophy:** Professional, calming, monochromatic blue-gray palette

**Characteristics:**
- Reduces visual noise with monochromatic scheme
- Soft cyan and gray-blue tones replace all yellows
- Excellent for long coding sessions
- Best for: Professional work environments, ADHD-friendly focus

**Key Colors:**
- Directory: Steel blue background (`48;5;67`)
- Duration: Calm gray-blue (`38;5;109`) ← Replaces bright yellow
- Git status: Slate blue/blue-gray spectrum
- Quota warnings: Cool blue spectrum (no yellows)

**When to Use:**
- All-day coding sessions
- Bright screen environments
- When you need to minimize distractions
- Professional/corporate settings

---

### Theme 2: Forest Greens & Dark
**Philosophy:** Nature-inspired earth tones, warm but not bright

**Characteristics:**
- Green and olive tones inspired by forest canopy
- Muted, earthy colors reduce eye strain
- Warm palette without brightness
- Best for: Reducing eye fatigue, nature lovers

**Key Colors:**
- Directory: Forest green background (`48;5;22`)
- Duration: Muted olive (`38;5;143`) ← Replaces bright yellow
- Git status: Deep green/olive spectrum
- Quota warnings: Green to brown spectrum

**When to Use:**
- Long research/reading sessions
- Prefer warm over cool tones
- Working in dim lighting
- Nature-inspired workflow aesthetic

---

### Theme 3: Purple & Charcoal
**Philosophy:** Modern, sophisticated, minimal visual stimulation

**Characteristics:**
- Low-contrast purple and gray palette
- Sophisticated and elegant appearance
- Minimizes visual stimulation (ADHD-optimized)
- Best for: Late-night coding, minimal distraction

**Key Colors:**
- Directory: Deep purple background (`48;5;54`)
- Duration: Muted mauve (`38;5;139`) ← Replaces bright yellow
- Git status: Charcoal/purple spectrum
- Quota warnings: Purple spectrum (lavender to burgundy)

**When to Use:**
- Late-night coding sessions
- Need minimal visual stimulation
- ADHD/focus optimization
- Modern, sophisticated aesthetic preference

---

## 🚀 Installation Instructions

### Quick Install (Recommended)

Each theme has a standalone script in `statusline-alternatives/`:
1. `theme-cool-blues.sh`
2. `theme-forest-greens.sh`
3. `theme-purple-charcoal.sh`

**Steps:**

1. **Backup your current statusLine:**
   ```bash
   cp ~/.claude/statusline-p10k.sh ~/.claude/statusline-p10k.sh.backup
   ```

2. **Preview a theme** (see visual output without installing):
   ```bash
   # Preview Cool Blues
   bash ~/projects/dev-tools/aiterm/statusline-alternatives/preview-theme.sh cool-blues

   # Preview Forest Greens
   bash ~/projects/dev-tools/aiterm/statusline-alternatives/preview-theme.sh forest-greens

   # Preview Purple & Charcoal
   bash ~/projects/dev-tools/aiterm/statusline-alternatives/preview-theme.sh purple-charcoal
   ```

3. **Apply a theme** (automatic installation):
   ```bash
   # Install Cool Blues
   bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh cool-blues

   # Install Forest Greens
   bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh forest-greens

   # Install Purple & Charcoal
   bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh purple-charcoal
   ```

4. **Test the theme** (start new Claude Code session):
   ```bash
   claude
   ```

5. **Restore original if needed:**
   ```bash
   cp ~/.claude/statusline-p10k.sh.backup ~/.claude/statusline-p10k.sh
   ```

---

### Manual Installation

If you prefer to manually edit the file:

1. **Open the statusLine script:**
   ```bash
   nano ~/.claude/statusline-p10k.sh
   # or
   code ~/.claude/statusline-p10k.sh
   ```

2. **Apply changes from your chosen theme:**
   - Open the corresponding theme file: `theme-cool-blues.sh`, `theme-forest-greens.sh`, or `theme-purple-charcoal.sh`
   - Follow the installation comments in each script
   - Key sections to replace:
     - Lines 293-314: Color definitions
     - Lines 210-228: Quota color logic
     - Line 485: Line2 content (time and duration colors)
     - Lines 463-478: Model display colors
     - Lines 273-291: Lines display colors

3. **Save and test:**
   ```bash
   # Start new Claude Code session
   claude
   ```

---

## 🔄 Switching Between Themes

You can easily switch themes by running the install script:

```bash
# Try Cool Blues for daytime work
bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh cool-blues

# Switch to Purple & Charcoal for evening coding
bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh purple-charcoal
```

**Tip:** Create aliases in your `~/.zshrc`:
```bash
# Add to ~/.config/zsh/.zshrc
alias statusline-cool="bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh cool-blues"
alias statusline-forest="bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh forest-greens"
alias statusline-purple="bash ~/projects/dev-tools/aiterm/statusline-alternatives/install-theme.sh purple-charcoal"
alias statusline-original="cp ~/.claude/statusline-p10k.sh.backup ~/.claude/statusline-p10k.sh"
```

Then simply run: `statusline-cool`, `statusline-forest`, or `statusline-purple`

---

## 🎯 Recommendation

**For ADHD-friendly focus:** Start with **Purple & Charcoal** (lowest visual stimulation)

**For all-day professional work:** Try **Cool Blues & Grays** (calming and professional)

**For reducing eye strain:** Use **Forest Greens & Dark** (nature-inspired, warm tones)

**Quick fix without changing theme:** If you just want to fix the bright yellow duration without changing the entire theme, replace line 485 in `~/.claude/statusline-p10k.sh`:

```bash
# Find this line (485):
line2_content="${line2_content} \033[38;5;240m│\033[0m \033[38;5;75m${current_time}\033[0m \033[38;5;240m│\033[0m \033[38;5;214m⏱ ${session_duration}\033[0m"

# Replace with (just changes duration from 214 to 109):
line2_content="${line2_content} \033[38;5;240m│\033[0m \033[38;5;75m${current_time}\033[0m \033[38;5;240m│\033[0m \033[38;5;109m⏱ ${session_duration}\033[0m"
```

This changes only the bright yellow (`38;5;214`) to a calm gray-blue (`38;5;109`) while keeping everything else the same.

---

## 📝 Notes

- All themes maintain compatibility with quota tracking system (`qu` command)
- 300ms update interval preserved
- No changes to layout or information display
- Only color adjustments
- Window title icon/name unchanged
- Git dirty indicators still work
- All project type detection unchanged

---

## 🐛 Troubleshooting

**Theme didn't apply:**
- Restart Claude Code session
- Check that `~/.claude/statusline-p10k.sh` was modified
- Verify permissions: `chmod +x ~/.claude/statusline-p10k.sh`

**Colors look different than expected:**
- Your iTerm2 color profile may affect 256-color rendering
- Try switching iTerm2 to a dark background profile
- Some colors may render differently with Solarized or other color schemes

**Want to customize further:**
- Edit the color codes directly in `~/.claude/statusline-p10k.sh`
- ANSI 256 color chart: https://www.ditig.com/256-colors-cheat-sheet
- Test colors: `for i in {0..255}; do echo -e "\033[38;5;${i}m Color ${i}\033[0m"; done`

---

## 📚 Further Reading

- [ANSI 256 Color Chart](https://www.ditig.com/256-colors-cheat-sheet)
- [Claude Code StatusLine Reference](https://code.claude.com/docs/en/statusline.md)
- [iTerm2 Color Schemes](https://iterm2colorschemes.com/)
- [ADHD-Friendly Color Design](https://www.additudemag.com/visual-design-adhd/)
