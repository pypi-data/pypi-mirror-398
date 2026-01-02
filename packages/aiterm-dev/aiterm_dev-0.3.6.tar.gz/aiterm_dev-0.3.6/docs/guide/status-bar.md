# Status Bar Integration

Display context information in iTerm2's status bar.

## Available Variables (v2.4.0)

The context switcher sets these user variables on every directory change:

| Variable | Content | Example |
|----------|---------|---------|
| `\(user.ctxIcon)` | Context icon | `📦`, `🐍`, `🔧` |
| `\(user.ctxName)` | Project name | `medfit`, `myapp` |
| `\(user.ctxBranch)` | Git branch | `main`, `dev` |
| `\(user.ctxProfile)` | Active profile | `R-Dev`, `Python-Dev` |

---

## Step-by-Step Setup

### Step 1: Enable Status Bar

1. Open **iTerm2** → **Settings** (⌘,)
2. Click **Profiles** tab
3. Select your profile (e.g., **Default**) in the left sidebar
4. Click **Session** sub-tab (in the row: General, Colors, Text, **Session**, etc.)
5. Check the box: **Status bar enabled**
6. Click **Configure Status Bar** button

> 📖 See [iTerm2 Status Bar Documentation](https://iterm2.com/documentation-status-bar.html) for official reference.

### Step 2: Add Interpolated String Component

The Configure Status Bar panel has two sections:

- **Top**: Available components (drag from here)
- **Bottom**: Active components (your status bar)

1. Scroll down in the **available components** list
2. Find **Interpolated String** (near the bottom)
3. **Drag** it to the **Active Components** area at the bottom
4. Position it where you want (left side recommended)

### Step 3: Configure the Component

1. **Click** on the Interpolated String component you just added
2. Click **Configure Component** button (bottom left)
3. In the **String Value** field, enter:

```
\(user.ctxIcon) \(user.ctxName) (\(user.ctxBranch))
```

4. Optionally set:
   - **Background Color**: Pick a color or leave default
   - **Text Color**: Pick a color or leave default
   - **Size**: Fixed or Auto

5. Click **OK** to close the component config
6. Click **OK** to close the status bar config

### Step 4: Reload Your Shell

```bash
source ~/.zshrc
```

Then `cd` to a project directory to see it update!

---

## Understanding Interpolated Strings

iTerm2 interpolated strings use `\(expression)` syntax:

```
\(variableName)           → Evaluates to variable value
\(user.customVar)         → User-defined variables start with "user."
```

**Our variables:**

- `\(user.ctxIcon)` → `📦`
- `\(user.ctxName)` → `medfit`
- `\(user.ctxBranch)` → `main`
- `\(user.ctxProfile)` → `R-Dev`

**Combining them:**

```
\(user.ctxIcon) \(user.ctxName)
```

Result: `📦 medfit`

---

## Built-in Variables You Can Also Use

iTerm2 provides many built-in variables:

| Variable | Description |
|----------|-------------|
| `\(session.path)` | Current directory path |
| `\(session.hostname)` | Current hostname |
| `\(session.username)` | Current username |
| `\(session.jobName)` | Running command name |
| `\(session.columns)` | Terminal width |
| `\(session.rows)` | Terminal height |

**Example combining built-in and custom:**

```
\(user.ctxIcon) \(user.ctxName) @ \(session.hostname)
```

Result: `📦 medfit @ macbook`

---

## Example Configurations

### Minimal: Icon + Name

```
\(user.ctxIcon) \(user.ctxName)
```

Shows: `🔧 aiterm`

### Full: Icon + Name + Branch

```
\(user.ctxIcon) \(user.ctxName) (\(user.ctxBranch))
```

Shows: `📦 medfit (main)`

### Profile-Aware

```
[\(user.ctxProfile)] \(user.ctxIcon) \(user.ctxName)
```

Shows: `[R-Dev] 📦 medfit`

### Branch Only

```
\(user.ctxBranch)
```

Shows: `main` or `feature/new-api`

---

## Recommended Status Bar Layout

A balanced status bar setup:

```
┌────────────────────────────────────────────────────────┐
│ 📦 medfit (main)  │  ~/projects/...  │  CPU  │  12:30 │
└────────────────────────────────────────────────────────┘
     ↑                    ↑               ↑        ↑
  Context            Current Dir       System   Clock
```

**Components (left to right):**

1. **Interpolated String** - `\(user.ctxIcon) \(user.ctxName) (\(user.ctxBranch))`
2. **Spring** (spacer)
3. **Current Directory** (built-in)
4. **CPU Utilization** (built-in, optional)
5. **Clock** (built-in)

---

## Status Bar Position

By default, the status bar appears at the **top**. To move it to the **bottom**:

1. Open **iTerm2** → **Settings** (⌘,)
2. Click **Appearance** tab
3. Under **General**, find **Status bar location**
4. Select **Bottom**

!!! tip "Bottom Recommended"
    Bottom placement keeps the status bar near your command line, making it easier to glance at context while typing.

---

## Available Components

### Recommended Components

| Component | Description | Use Case |
|-----------|-------------|----------|
| **Interpolated String** | Custom variables | Your context info |
| **git state** | Branch, dirty, ahead/behind | Built-in git info |
| **Current Directory** | Full path | Know where you are |
| **Clock** | Time and date | Always useful |
| **Job Name** | Running process | See what's executing |

### System Monitors

| Component | Description | Use Case |
|-----------|-------------|----------|
| **CPU Utilization** | CPU graph over time | Monitor heavy jobs |
| **Memory Utilization** | RAM graph over time | Watch data analysis |
| **Battery Level** | Battery with charging | Laptop users |
| **Network Throughput** | Upload/download | Monitor transfers |

### Spacers

| Component | Description |
|-----------|-------------|
| **Spring** | Flexible spacer (pushes items apart) |
| **Fixed-size Spacer** | Fixed width gap |
| **Empty Space** | Minimal gap |

### UI Tools

| Component | Description |
|-----------|-------------|
| **Composer** | Edit commands before sending |
| **Search Tool** | Search terminal history |
| **Filter** | Filter terminal output |
| **Snippets** | Quick text insertion |

---

## Suggested Layouts

### Minimal (Recommended)

```
┌──────────────────────────────────────────────────────────────┐
│ 📦 medfit (main)  │  ~/projects/r-packages/active/medfit  │  14:30 │
└──────────────────────────────────────────────────────────────┘
```

**Components:**

1. Interpolated String: `\(user.ctxIcon) \(user.ctxName) (\(user.ctxBranch))`
2. Spring
3. Current Directory
4. Clock

### With System Monitors

```
┌──────────────────────────────────────────────────────────────┐
│ 📦 medfit  │  CPU ▃▅▂  │  RAM ▆▄▅  │  ~/proj...  │  14:30   │
└──────────────────────────────────────────────────────────────┘
```

**Components:**

1. Interpolated String: `\(user.ctxIcon) \(user.ctxName)`
2. CPU Utilization
3. Memory Utilization
4. Spring
5. Current Directory
6. Clock

### Developer Focus

```
┌──────────────────────────────────────────────────────────────┐
│ 📦 medfit  │  main*  │  R  │  ~/projects/...  │  14:30     │
└──────────────────────────────────────────────────────────────┘
```

**Components:**

1. Interpolated String: `\(user.ctxIcon) \(user.ctxName)`
2. git state (built-in)
3. Job Name
4. Spring
5. Current Directory
6. Clock

---

## Status Bar Styling

### Component Settings

For each component, you can set:

- **Background Color** - Override default
- **Text Color** - Override default
- **Priority** - Higher priority keeps component visible when space is tight (default: 5)
- **Minimum Width** - Prevent component from shrinking too small

### Recommended Settings for Context Component

- **Priority**: 10 (high - keep visible)
- **Minimum Width**: 100
- **Background Color**: Match your theme or leave default

---

## Per-Profile Status Bars

Each iTerm2 profile can have its own status bar configuration.

**Tip:** Configure the status bar on your **Default** profile, then child profiles (R-Dev, Python-Dev, etc.) will inherit it automatically.

---

## Built-in Git Component

iTerm2 also has a built-in **git state** component that shows:

- Branch name
- Dirty/clean status
- Ahead/behind remote

You can use this alongside or instead of `\(user.ctxBranch)`.

To add it:

1. Configure Status Bar
2. Drag **git state** to your bar
3. It auto-updates based on the current directory

---

## Troubleshooting

**Variables show empty or literal text:**

- Reload your shell: `source ~/.zshrc`
- Verify integration is loaded: `type _iterm_detect_context`
- Run `cd .` to trigger an update

**Status bar not visible:**

- Enable in Settings → Profiles → Session → Status bar enabled
- Check the profile you're using has status bar enabled

**Variables not updating:**

- Variables update on directory change (`cd`)
- Run `_iterm_detect_context` manually to force update

**Wrong variable values:**

- Check you're in the expected directory
- Verify git repo exists for branch info

---

## Technical Details

User variables are set via iTerm2's OSC 1337 escape sequence:

```bash
printf '\033]1337;SetUserVar=%s=%s\007' "name" "$(echo -n 'value' | base64)"
```

The context switcher calls this automatically on every `chpwd` hook (directory change).

Variables persist in the session until changed or the session ends.
