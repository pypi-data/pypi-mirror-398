# aiterm Troubleshooting Guide

**Version:** 0.1.0-dev
**Last Updated:** 2025-12-21

---

## Quick Diagnosis

Answer these questions to find your solution:

1. **Is aiterm installed?** → [Installation Issues](#installation-issues)
2. **Profile not switching?** → [Profile Switching Issues](#profile-switching-issues)
3. **Context not detected?** → [Context Detection Issues](#context-detection-issues)
4. **Auto-approvals not working?** → [Claude Code Integration Issues](#claude-code-integration-issues)
5. **Terminal not supported?** → [Terminal Compatibility](#terminal-compatibility)

---

## Diagnostic Flowchart

Use this flowchart to quickly identify and resolve common issues:

```mermaid
flowchart TD
    Start([Issue with aiterm?]) --> Doctor[Run: aiterm doctor]

    Doctor --> DoctorOK{All checks<br/>passed?}

    DoctorOK -->|No| CheckFails{Which check<br/>failed?}
    DoctorOK -->|Yes| IssueType{What's the<br/>issue?}

    CheckFails -->|Python| PyFix[Python version < 3.10<br/>→ Upgrade Python]
    CheckFails -->|Terminal| TermFix[Unsupported terminal<br/>→ Install iTerm2]
    CheckFails -->|Claude Code| ClaudeFix[Claude Code not found<br/>→ Install Claude CLI]
    CheckFails -->|Settings| SettingsFix[Config missing<br/>→ Run: aiterm init]

    PyFix --> Retry[Retry: aiterm doctor]
    TermFix --> Retry
    ClaudeFix --> Retry
    SettingsFix --> Retry
    Retry --> DoctorOK

    IssueType -->|Profile not switching| ProfileIssue
    IssueType -->|Context not detected| ContextIssue
    IssueType -->|Auto-approvals failing| ApprovalIssue
    IssueType -->|Other| OtherIssue

    ProfileIssue{Manual switch<br/>works?}
    ProfileIssue -->|Yes| AutoSwitch[Auto-switching disabled<br/>→ Check AITERM_AUTO_SWITCH]
    ProfileIssue -->|No| ProfileNotFound[Profile doesn't exist<br/>→ Run: aiterm profile list]

    AutoSwitch --> AddHook[Add chpwd hook to .zshrc<br/>See: Shell Integration]
    ProfileNotFound --> CreateProfile[Create custom profile<br/>See: Profile Management]

    ContextIssue --> DetectCmd[Run: aiterm detect]
    DetectCmd --> DetectResult{Context<br/>detected?}

    DetectResult -->|No| CheckMarkers[Check for context markers:<br/>- DESCRIPTION (R)<br/>- pyproject.toml (Python)<br/>- package.json (Node)]
    DetectResult -->|Yes| WrongProfile[Wrong profile selected?<br/>→ Adjust detection priority]

    CheckMarkers --> NoMarkers{Markers<br/>exist?}
    NoMarkers -->|No| AddMarkers[Add project markers or<br/>use manual profile switch]
    NoMarkers -->|Yes| CustomDetector[Create custom detector<br/>See: Integration Guide]

    ApprovalIssue --> ListPresets[Run: aiterm claude approvals list]
    ListPresets --> SetPreset[Run: aiterm claude approvals set PRESET]
    SetPreset --> VerifySettings[Check: ~/.claude/settings.json<br/>autoApprovals section]

    VerifySettings --> ValidJSON{Valid<br/>JSON?}
    ValidJSON -->|No| RestoreBackup[Restore from backup:<br/>~/.claude/settings.json.backup.*]
    ValidJSON -->|Yes| RestartClaude[Restart Claude Code]

    OtherIssue --> Debug[Run with debug logging:<br/>export AITERM_DEBUG=1]
    Debug --> Logs[Check logs and error messages]
    Logs --> GithubIssue[Still stuck?<br/>→ GitHub Issue with logs]

    AddHook --> Done([Issue Resolved])
    CreateProfile --> Done
    WrongProfile --> Done
    AddMarkers --> Done
    CustomDetector --> Done
    RestartClaude --> Done
    RestoreBackup --> Done

    style Start fill:#e1f5e1
    style Done fill:#e1f5e1
    style DoctorOK fill:#fff4e6
    style CheckFails fill:#fff4e6
    style IssueType fill:#fff4e6
    style ProfileIssue fill:#fff4e6
    style DetectResult fill:#fff4e6
    style NoMarkers fill:#fff4e6
    style ValidJSON fill:#fff4e6
    style GithubIssue fill:#ffe1e1
```

**How to Use This Flowchart:**

1. **Start with `aiterm doctor`** - Verifies installation and environment
2. **Follow your specific issue** - Each path provides targeted solutions
3. **Check the relevant section** - Links point to detailed documentation
4. **Still stuck?** - Enable debug logging and file a GitHub issue

---

## Common Issues

### Installation Issues

#### Issue: `aiterm: command not found`

**Symptom:**
```bash
$ aiterm --version
zsh: command not found: aiterm
```

**Diagnosis:**
```bash
# Check if installed
python3 -m pip show aiterm

# Check Python bin directory in PATH
echo $PATH | grep -o '/[^:]*python[^:]*bin'
```

**Solution 1: Reinstall**
```bash
# With UV
uv pip install --force-reinstall aiterm

# With pip
pip install --force-reinstall aiterm
```

**Solution 2: Add to PATH**
```bash
# Find Python bin directory
python3 -m site --user-base

# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.zshrc
```

---

#### Issue: `ImportError: No module named 'aiterm'`

**Symptom:**
```python
>>> import aiterm
ImportError: No module named 'aiterm'
```

**Diagnosis:**
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check installed packages
python3 -m pip list | grep aiterm
```

**Solution:**
```bash
# Install in correct Python environment
python3 -m pip install aiterm

# Or activate virtual environment first
source venv/bin/activate
pip install aiterm
```

---

### Profile Switching Issues

#### Issue: Profile not switching automatically

**Symptom:**
Profile doesn't change when `cd` into project

**Diagnosis:**
```bash
# 1. Check if context detected
cd ~/your-project
aiterm detect
# Should show context type and profile

# 2. Check if auto-switching enabled
echo $AITERM_AUTO_SWITCH
# Should be empty or "1"

# 3. Check terminal type
echo $TERM_PROGRAM
# Should show "iTerm.app" or "WezTerm"
```

**Solution 1: Auto-switching disabled**
```bash
# Enable auto-switching
unset AITERM_AUTO_SWITCH

# Or set explicitly
export AITERM_AUTO_SWITCH=1
```

**Solution 2: Terminal not supported**
```bash
# Check supported terminals
aiterm doctor

# If using Terminal.app:
# → Download iTerm2 from https://iterm2.com
# → Install and set as default
```

**Solution 3: Shell integration needed**

Add to `~/.zshrc`:
```bash
# aiterm automatic context switching
function chpwd() {
    aiterm detect --silent --auto-switch
}
```

---

#### Issue: Profile exists but switch fails

**Symptom:**
```bash
$ aiterm profile switch R-Dev
❌ Failed to switch profile: R-Dev
```

**Diagnosis:**
```bash
# 1. List available profiles
aiterm profile list

# 2. Check iTerm2 profiles
# iTerm2 → Preferences → Profiles
# Verify "R-Dev" profile exists

# 3. Check terminal connection
ps aux | grep iTerm
```

**Solution 1: Profile doesn't exist**

Create profile in iTerm2:
1. iTerm2 → Preferences → Profiles
2. Click "+" to add new profile
3. Name it "R-Dev"
4. Configure colors, fonts, etc.
5. Try switch again

**Solution 2: iTerm2 not responding**
```bash
# Restart iTerm2
pkill -9 iTerm2
open -a iTerm

# Try again
aiterm profile switch R-Dev
```

---

### Context Detection Issues

#### Issue: Context not detected

**Symptom:**
```bash
$ cd ~/projects/my-r-package
$ aiterm detect
📁 Path: /Users/dt/projects/my-r-package
🎯 Type: Unknown
📋 Profile: Default
```

**Diagnosis:**
```bash
# Check for marker files
ls -la

# R package should have:
ls DESCRIPTION R/

# Python should have:
ls pyproject.toml setup.py

# Node.js should have:
ls package.json
```

**Solution 1: Missing marker file**

**For R packages:**
```bash
# Create minimal DESCRIPTION
cat > DESCRIPTION << 'EOF'
Package: MyPackage
Title: My R Package
Version: 0.1.0
Description: My package description.
License: MIT
Encoding: UTF-8
EOF

# Create R directory
mkdir -p R
```

**For Python:**
```bash
# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "my-package"
version = "0.1.0"
EOF
```

**Solution 2: Wrong directory**
```bash
# Navigate to package root
cd ~/projects/my-r-package

# Verify marker files
ls DESCRIPTION R/

# Try detect again
aiterm detect
```

---

#### Issue: Wrong context detected

**Symptom:**
Context type is incorrect for your project

**Example:**
```bash
$ cd ~/my-quarto-project
$ aiterm detect
🎯 Type: R Package  # Wrong! Should be Quarto
```

**Diagnosis:**
```bash
# Check marker files
ls -la

# Multiple markers?
ls DESCRIPTION _quarto.yml
```

**Cause:** Multiple context types match, priority determines winner

**Solution 1: Remove conflicting markers**
```bash
# If not actually an R package, remove DESCRIPTION
rm DESCRIPTION

# Now should detect as Quarto
aiterm detect
```

**Solution 2: Manual override**
```bash
# Force specific profile
aiterm profile switch Quarto-Dev
```

**Solution 3: Adjust priority (advanced)**

Create custom detector with higher priority (see Integration Guide)

---

### Claude Code Integration Issues

#### Issue: Auto-approvals not applied

**Symptom:**
```bash
$ aiterm claude approvals set r-package
✅ Applied preset: r-package (35 tools)

# But Claude Code still asking for approvals
```

**Diagnosis:**
```bash
# 1. Check settings file
cat ~/.claude/settings.json | grep -A 5 autoApprovals

# 2. Verify Claude Code version
claude --version

# 3. Check file permissions
ls -l ~/.claude/settings.json
```

**Solution 1: Claude Code not reading settings**
```bash
# Restart Claude Code
pkill claude
claude

# Or restart terminal
```

**Solution 2: Settings file corrupted**
```bash
# Backup current
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Validate JSON
python3 -c "
import json
with open('~/.claude/settings.json') as f:
    json.load(f)  # Will error if invalid
"

# If invalid, restore from backup
aiterm claude settings show --validate
```

**Solution 3: Wrong settings location**
```bash
# Check Claude Code config directory
ls ~/.claude/

# Should contain settings.json
# If not, create it:
mkdir -p ~/.claude
echo '{"autoApprovals": []}' > ~/.claude/settings.json

# Try preset again
aiterm claude approvals set r-package
```

---

#### Issue: Settings backup failed

**Symptom:**
```bash
$ aiterm claude approvals set r-package
❌ Failed to create backup
```

**Diagnosis:**
```bash
# Check permissions
ls -la ~/.claude/

# Check disk space
df -h ~
```

**Solution:**
```bash
# Fix permissions
chmod 700 ~/.claude
chmod 600 ~/.claude/settings.json

# Clean old backups if disk full
rm ~/.claude/settings.json.backup.*

# Try again
aiterm claude approvals set r-package
```

---

### Terminal Compatibility

#### macOS - Terminal.app

**Status:** ❌ Not supported

**Why:** Terminal.app doesn't support:
- Profile switching via escape sequences
- User-defined status bar variables
- Advanced escape sequences

**Solution:** Install iTerm2
```bash
# Download and install
open https://iterm2.com

# Or with Homebrew
brew install --cask iterm2

# Set as default terminal
# System Settings → General → Default terminal → iTerm
```

---

#### macOS - iTerm2

**Status:** ✅ Fully supported

**Requirements:**
- iTerm2 3.4.0 or higher
- Accessibility permissions (for full features)

**Setup:**
1. Download from https://iterm2.com
2. Create profiles (Preferences → Profiles)
3. Grant accessibility (System Settings → Privacy → Accessibility → iTerm)

**Common Issue: Accessibility permission denied**

**Symptom:** Profile switching works but slow/unreliable

**Solution:**
```bash
# 1. Open System Settings
# 2. Privacy & Security → Accessibility
# 3. Find iTerm2 in list
# 4. Toggle OFF then ON
# 5. Restart iTerm2
```

---

#### Linux - gnome-terminal

**Status:** ⚠️ Partial support

**Supported:**
- ✅ Title setting (OSC sequences)
- ❌ Profile switching (not supported by gnome-terminal)
- ❌ Status bar variables

**Workaround:** Use another terminal (Alacritty, Wezterm)

---

#### Linux - Alacritty

**Status:** 🚧 Planned (Phase 2)

**Current:**
- ✅ Title setting works
- ❌ Profile switching requires config file editing
- ❌ Real-time profile switching not implemented

**Workaround:**
```bash
# Manual profile switching
cp ~/.config/alacritty/themes/r-dev.yml \
   ~/.config/alacritty/alacritty.yml

# Reload Alacritty
pkill -USR1 alacritty
```

---

#### Linux - Wezterm

**Status:** 🚧 Planned (Phase 2)

**Current:**
- ✅ Title setting works
- ⚠️ Profile switching via CLI (slow)
- ❌ Optimized integration not implemented

**Workaround:**
```bash
# Use Wezterm CLI
wezterm cli set-tab-color-scheme "R-Dev"
```

---

#### Windows - Windows Terminal

**Status:** 🚧 Planned (Phase 3)

**Not yet implemented.** aiterm is macOS/Linux focused initially.

**Workaround:** Use WSL with supported terminal (Wezterm, Alacritty)

---

## Platform-Specific Issues

### macOS

#### Issue: "Operation not permitted"

**Symptom:**
```bash
$ aiterm profile switch R-Dev
❌ Operation not permitted
```

**Cause:** macOS security restrictions

**Solution:**
```bash
# Grant Full Disk Access
# 1. System Settings → Privacy & Security
# 2. Full Disk Access
# 3. Add iTerm2
# 4. Toggle ON
# 5. Restart iTerm2
```

---

#### Issue: Slow profile switching

**Symptom:** Profile switch takes > 1 second

**Cause:** macOS App Nap

**Solution:**
```bash
# Disable App Nap for iTerm2
defaults write com.googlecode.iterm2 NSAppSleepDisabled -bool YES

# Restart iTerm2
pkill iTerm2
open -a iTerm
```

---

### Linux

#### Issue: `libpython not found`

**Symptom:**
```bash
$ aiterm
error while loading shared libraries: libpython3.11.so.1.0
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3.11 python3.11-dev

# Fedora/RHEL
sudo dnf install python3.11 python3.11-devel

# Arch
sudo pacman -S python
```

---

#### Issue: Permission denied on config directory

**Symptom:**
```bash
$ aiterm doctor
❌ Settings: Permission denied
```

**Solution:**
```bash
# Fix ownership
sudo chown -R $USER:$USER ~/.aiterm
sudo chown -R $USER:$USER ~/.claude

# Fix permissions
chmod 700 ~/.aiterm
chmod 700 ~/.claude
chmod 600 ~/.claude/settings.json
```

---

## Error Messages Reference

### `ProfileNotFoundError`

**Message:** `Profile 'NAME' not found`

**Cause:** Profile doesn't exist in terminal

**Solution:**
```bash
# List available profiles
aiterm profile list

# Create profile in terminal settings
# Or use existing profile name
```

---

### `TerminalUnsupportedError`

**Message:** `Terminal 'NAME' not supported`

**Cause:** Using unsupported terminal

**Solution:**
```bash
# Check supported terminals
aiterm doctor

# Install supported terminal (iTerm2, Wezterm, etc.)
```

---

### `ConfigError`

**Message:** `Invalid configuration: DETAILS`

**Cause:** Malformed config file

**Solution:**
```bash
# Validate config
aiterm claude settings show --validate

# Reset to defaults
rm ~/.aiterm/config.json
aiterm doctor  # Recreates defaults
```

---

### `SettingsError`

**Message:** `Failed to update settings: DETAILS`

**Cause:** Can't write to settings file

**Solution:**
```bash
# Check permissions
ls -la ~/.claude/settings.json

# Fix permissions
chmod 600 ~/.claude/settings.json

# Check disk space
df -h ~
```

---

## Performance Issues

### Slow context detection

**Expected:** < 50ms
**If slower:** > 500ms

**Diagnosis:**
```bash
# Time detection
time aiterm detect
# Should complete in < 0.1s
```

**Causes:**
1. Network-mounted directories (NFS, SMB)
2. Very deep directory structure
3. Large number of files

**Solutions:**
```bash
# 1. Work on local disk
cd ~/local/copy/of/project

# 2. Exclude from detection
export AITERM_SKIP_DETECT=1

# 3. Use manual profile switching
aiterm profile switch PROFILE_NAME
```

---

### High CPU usage

**Symptom:** aiterm using > 10% CPU

**Diagnosis:**
```bash
# Check process
top -p $(pgrep -f aiterm)

# Check if running background tasks
ps aux | grep aiterm
```

**Solution:**
```bash
# Kill background processes
pkill -f aiterm

# Restart with clean state
aiterm doctor
```

---

## Diagnostic Tools

### Complete diagnostic script

Save as `diagnose-aiterm.sh`:

```bash
#!/bin/bash

echo "=== aiterm Diagnostic Report ==="
echo

echo "1. Installation:"
echo "   Python: $(python3 --version)"
echo "   aiterm: $(aiterm --version 2>&1 || echo 'NOT INSTALLED')"
echo

echo "2. Environment:"
echo "   TERM_PROGRAM: $TERM_PROGRAM"
echo "   AITERM_AUTO_SWITCH: $AITERM_AUTO_SWITCH"
echo "   AITERM_CONFIG: $AITERM_CONFIG"
echo

echo "3. Terminal:"
ps aux | grep -i iterm | grep -v grep || echo "   iTerm2: Not running"
echo

echo "4. Config Files:"
ls -la ~/.aiterm/ 2>/dev/null || echo "   ~/.aiterm/: Not found"
ls -la ~/.claude/settings.json 2>/dev/null || echo "   ~/.claude/settings.json: Not found"
echo

echo "5. Current Directory:"
pwd
ls -la | head -10
echo

echo "6. Context Detection:"
aiterm detect 2>&1 || echo "   Detection failed"
echo

echo "=== End Diagnostic Report ==="
```

**Usage:**
```bash
chmod +x diagnose-aiterm.sh
./diagnose-aiterm.sh > aiterm-diagnostic.txt
```

---

## Getting Help

### Before asking for help

Run these diagnostic commands:

```bash
# 1. Check installation
aiterm doctor

# 2. Check context detection
aiterm detect

# 3. Check settings
aiterm claude settings show

# 4. Run diagnostic script
./diagnose-aiterm.sh > diagnostic.txt
```

### Useful information to include

When reporting issues:

1. **Error message** (exact text)
2. **Diagnostic output** (`aiterm doctor`)
3. **Terminal type** (`echo $TERM_PROGRAM`)
4. **Operating system** (macOS, Linux, Windows)
5. **aiterm version** (`aiterm --version`)
6. **Steps to reproduce**

### Support channels

- **GitHub Issues:** https://github.com/Data-Wise/aiterm/issues
- **Discussions:** https://github.com/Data-Wise/aiterm/discussions
- **Documentation:** https://Data-Wise.github.io/aiterm/

---

## FAQ

### Q: Can I use aiterm without iTerm2?

**A:** Yes, but with limited features:
- ✅ Context detection works
- ✅ Settings management works
- ❌ Profile switching doesn't work (terminal-specific)

**Supported terminals:** iTerm2 (full), Wezterm (planned), Alacritty (planned)

---

### Q: Why isn't my custom detector working?

**A:** Check:
1. Priority (lower number = higher priority)
2. Registration (`register_detector()`)
3. Detection logic (`_has_file()`, etc.)
4. Return value (`Context` object or `None`)

**Debug:**
```python
from aiterm.context import detect_context
import logging

logging.basicConfig(level=logging.DEBUG)
context = detect_context("/path")
# Should show detector execution
```

---

### Q: Can I roll back auto-approval changes?

**A:** Yes! aiterm creates automatic backups:

```bash
# List backups
ls ~/.claude/settings.json.backup.*

# Restore from backup
cp ~/.claude/settings.json.backup.TIMESTAMP \
   ~/.claude/settings.json
```

---

### Q: How do I reset aiterm to defaults?

**A:**
```bash
# Remove config
rm -rf ~/.aiterm

# Recreate defaults
aiterm doctor

# Settings will be regenerated
```

**Note:** Claude Code settings are NOT removed (safe)

---

## Next Steps

- **[User Guide](../guides/AITERM-USER-GUIDE.md)** - Learn how to use aiterm
- **[Integration Guide](../guides/AITERM-INTEGRATION.md)** - Extend aiterm
- **[API Documentation](../api/AITERM-API.md)** - API reference
- **[Architecture](../architecture/AITERM-ARCHITECTURE.md)** - How it works

---

**Last Updated:** 2025-12-21
**Maintained By:** aiterm Development Team
