# Quick Start After Restart

## Step 1: Check if JSON was captured

```bash
cat /tmp/claude-statusline-input.log | jq .
```

**Expected:** Fresh JSON with current session data

---

## Step 2: Verify structure

```bash
cat /tmp/claude-statusline-input.log | jq 'keys'
```

**Should include:** `["cost", "model", "session_id", "workspace", ...]`

---

## Step 3: Extract key fields

```bash
cat /tmp/claude-statusline-input.log | jq '{
  cwd: .workspace.current_dir,
  project: .workspace.project_dir,
  model: .model.display_name,
  session: .session_id,
  cost: .cost.total_cost_usd,
  lines: {
    added: .cost.total_lines_added,
    removed: .cost.total_lines_removed
  }
}'
```

---

## Step 4: Resume with Claude

Just say **"resume"** and share the results!

---

## If log is empty or old:

```bash
# Check file timestamp
ls -lh /tmp/claude-statusline-input.log

# Check current settings
cat .claude/settings.local.json | jq '.statusLine'

# Verify we're in Claude Code
echo $CLAUDECODE
```
