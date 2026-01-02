# Video Walkthrough Guide

This guide outlines creating video tutorials for aiterm.

## Recommended Videos

### 1. Quick Start (2 min)

**Title:** "aiterm in 2 Minutes"

**Script:**
```
0:00 - Title card
0:05 - Install: brew install data-wise/tap/aiterm
0:20 - Run: ait doctor (show output)
0:35 - Navigate to project: cd ~/my-python-project
0:45 - Detect: ait detect (show Python detection)
0:55 - Switch: ait switch (show profile change)
1:10 - Claude settings: ait claude settings
1:30 - Add approvals: ait claude approvals add safe
1:45 - Recap + outro
```

**Key Shots:**
- Terminal split screen (commands left, iTerm2 profile change right)
- Zoom on context detection output
- Profile color change animation

---

### 2. Context Detection Deep Dive (5 min)

**Title:** "Smart Terminal Context with aiterm"

**Script:**
```
0:00 - Intro: What is context detection?
0:30 - Demo: Navigate to R package, Python, Node projects
1:30 - Show detection for each type
2:30 - Explain priority: path → file → directory → default
3:30 - Show profile switching in action
4:30 - Custom context (brief mention)
4:50 - Recap
```

**Key Shots:**
- Side-by-side: file tree + terminal
- Profile color palette comparison
- Git dirty indicator demo

---

### 3. Claude Code Integration (5 min)

**Title:** "Managing Claude Code with aiterm"

**Script:**
```
0:00 - Intro: What are auto-approvals?
0:30 - Show: ait claude settings
1:00 - Explain: permissions allow/deny
1:30 - Demo: ait claude approvals presets
2:00 - Add safe preset
2:30 - Add moderate preset
3:00 - Show combined permissions
3:30 - Backup workflow
4:00 - MCP server check: ait mcp list
4:30 - Recap
```

---

### 4. MCP Server Management (3 min)

**Title:** "MCP Servers with aiterm"

**Script:**
```
0:00 - Intro: What are MCP servers?
0:30 - List servers: ait mcp list
1:00 - Test server: ait mcp test filesystem
1:30 - Test all: ait mcp test-all
2:00 - Validate config: ait mcp validate
2:30 - Server info: ait mcp info filesystem
2:50 - Recap
```

---

## Recording Setup

### Software
- **Screen Recording:** OBS Studio or ScreenFlow
- **Terminal:** iTerm2 with larger font (18pt+)
- **Resolution:** 1920x1080 (YouTube-friendly)

### Terminal Settings
```bash
# Increase font size for recording
# iTerm2 → Preferences → Profiles → Text → Font → 18pt

# Clear terminal before recording
clear

# Use simple prompt
export PS1='$ '
```

### Recording Tips

1. **Pre-type commands** in a script, paste during recording
2. **Pause briefly** after each command for viewers to read
3. **Zoom on important output** using QuickTime or OBS crop
4. **Add captions** for accessibility
5. **Keep videos under 5 minutes** for engagement

---

## Publishing Checklist

- [ ] Record in 1080p or 4K
- [ ] Add intro/outro cards
- [ ] Include captions (.srt file)
- [ ] Create thumbnail (terminal screenshot + title)
- [ ] Write description with timestamps
- [ ] Add tags: aiterm, claude code, terminal, iTerm2, productivity

---

## Hosting Options

| Platform | Pros | Cons |
|----------|------|------|
| YouTube | SEO, free hosting | Requires account |
| Loom | Easy sharing | Limited free tier |
| GitHub (gif) | In-repo, no account | No audio, size limits |
| Asciinema | Terminal-native | No audio |

### GitHub GIF Method

For quick demos without audio:

```bash
# Using aiterm's GIF recording (via Claude in Chrome)
# Or use asciinema + gif conversion:

asciinema rec demo.cast
# ... do your demo ...
# Ctrl+D to stop

# Convert to gif
agg demo.cast demo.gif --speed 2
```

---

## Video Ideas Backlog

- [ ] "Setting up aiterm from scratch"
- [ ] "aiterm + OpenCode workflow"
- [ ] "Custom hooks with aiterm"
- [ ] "ADHD-friendly terminal setup"
- [ ] "aiterm for R developers"
- [ ] "Migrating from manual iTerm2 profiles"

---

## Related

- [Quick Start](../QUICK-START.md)
- [Getting Started Tutorial](../GETTING-STARTED.md)
- [Reference Card](../REFCARD.md)
