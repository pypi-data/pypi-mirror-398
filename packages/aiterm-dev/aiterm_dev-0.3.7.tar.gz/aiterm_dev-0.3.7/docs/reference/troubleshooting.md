# Troubleshooting

## Common Issues

### Profiles Not Switching

**Symptom:** Colors don't change when you `cd` to a project.

**Check:**

1. Verify you're in iTerm2:
   ```bash
   echo $TERM_PROGRAM
   # Should show: iTerm.app
   ```

2. Verify profiles exist (exact names, case-sensitive):
   - R-Dev
   - Python-Dev
   - Node-Dev
   - AI-Session
   - Production

3. Verify integration is loaded:
   ```bash
   typeset -f _iterm_detect_context
   # Should show function definition
   ```

4. If not loaded, source it:
   ```bash
   source ~/.config/zsh/.zshrc
   ```

### Title Not Showing

**Symptom:** Tab shows "zsh" or directory instead of icon + name.

**Check:**

1. iTerm2 title setting:
   - Settings → Profiles → General → Title
   - Set to: **Session Name**

2. OMZ auto-title disabled:
   ```bash
   echo $DISABLE_AUTO_TITLE
   # Should show: true
   ```

3. If not set, add **before** antidote/OMZ in .zshrc:
   ```zsh
   DISABLE_AUTO_TITLE="true"
   ```

### Title Shows Briefly Then Disappears

**Symptom:** Title flashes correct value then changes.

**Cause:** Something else is overwriting the title (usually OMZ).

**Fix:** Ensure `DISABLE_AUTO_TITLE="true"` is set **before** plugins load.

### Loops / Terminal Hangs

**Symptom:** Terminal freezes after `cd`.

**Fix:**

1. Disable integration temporarily:
   ```bash
   # Comment out in .zshrc
   # source ~/path/to/iterm2-integration.zsh
   ```

2. Open new terminal

3. Check for conflicting hooks:
   ```bash
   echo $chpwd_functions
   ```

### Wrong Profile Detected

**Symptom:** Shows R-Dev but it's a Python project.

**Cause:** Detection priority - R is checked before Python.

**Check:** Does the directory have a `DESCRIPTION` file?

```bash
ls DESCRIPTION
```

If yes, R detection wins. This is by design for R packages with Python scripts.

## Diagnostic Script

Run the included diagnostic:

```bash
~/path/to/aiterm/scripts/diagnose.sh
```

## Reset Everything

If all else fails:

```bash
# 1. Comment out integration in .zshrc
# 2. Restart terminal
# 3. Clear caches
unset _ITERM_CURRENT_PROFILE
unset _ITERM_CURRENT_TITLE
unset _ITERM_HOOK_REGISTERED

# 4. Re-source
source ~/.config/zsh/.zshrc
```
