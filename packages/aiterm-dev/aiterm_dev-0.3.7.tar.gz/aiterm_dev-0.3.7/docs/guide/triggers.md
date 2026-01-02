# iTerm2 Triggers

Automatic notifications for Claude Code sessions.

## Built-in Triggers (v2.3.0)

The **AI-Session** profile now includes triggers for Claude Code:

| Pattern | Action | Effect |
|---------|--------|--------|
| `Allow .+?` | Bounce Dock Icon | Dock bounces when tool approval needed |
| `Error:\|error:\|failed` | Highlight Text | Errors shown in red |
| `Session cost:\|Total cost:` | Post Notification | macOS notification on `/cost` |
| `✓\|completed` | Highlight Text | Success markers shown in green |

These triggers activate automatically when using the AI-Session profile.

---

## How Triggers Work

iTerm2 triggers watch terminal output and perform actions when regex patterns match.

```
Terminal Output → Regex Match → Action Triggered
```

Useful for:

- Getting notified when Claude needs input
- Highlighting errors and successes
- Bouncing dock when attention needed

---

## Customizing Triggers

### View/Edit Triggers

1. Open iTerm2 → Settings → Profiles
2. Select **AI-Session**
3. Go to **Advanced** tab
4. Click **Edit** next to Triggers

### Add New Trigger

| Field | Description |
|-------|-------------|
| Regular Expression | Regex pattern to match |
| Action | What to do when matched |
| Parameters | Action-specific options |
| Instant | Match immediately (don't wait for newline) |

---

## Additional Trigger Ideas

### Notification When Claude Idle

```
Regex: ^> $
Action: Post Notification
Parameters: Claude waiting for input
Instant: ✅
```

### Sound on Long Tasks

```
Regex: (completed|finished|done)
Action: Ring Bell
Instant: ❌
```

### Highlight Warnings

```
Regex: [Ww]arning:|WARN
Action: Highlight Text
Parameters: {#ffaa00,}
```

---

## Available Actions

| Action | Description |
|--------|-------------|
| Post Notification | macOS notification center |
| Bounce Dock Icon | Bounces until window focused |
| Ring Bell | Plays system bell sound |
| Highlight Line | Colors entire line |
| Highlight Text | Colors matched text only |
| Set Title | Changes tab title |
| Show Alert | Popup alert dialog |
| Run Command | Execute shell command |
| Send Text | Send text to terminal |

---

## Color Format

For Highlight triggers, use `{#rrggbb,#rrggbb}` format:

- First color: foreground
- Second color: background
- Empty string for unchanged: `{#ff0000,}` (red text, no bg change)

Examples:

- `{#ff4444,#330000}` - Red text on dark red background
- `{#44ff44,}` - Green text, default background
- `{,#ffffcc}` - Default text, yellow background

---

## Profile Inheritance

Triggers on the **Default** profile are inherited by child profiles.

Since all our profiles use `Dynamic Profile Parent Name: Default`, you can:

1. Add triggers to **Default** for global behavior
2. Add triggers to **AI-Session** for Claude-specific behavior

The AI-Session triggers are specific to Claude/AI sessions and won't affect other profiles.

---

## Troubleshooting

**Triggers not firing:**

- Check regex syntax (use ICU regex)
- Try enabling "Instant" for prompts without newlines
- Verify profile is active (check tab color)

**Too many notifications:**

- Make regex more specific
- Remove broad patterns like `completed`

**Dock won't stop bouncing:**

- Click on iTerm2 window to focus it
- Or disable the trigger temporarily
