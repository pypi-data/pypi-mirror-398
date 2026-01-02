# iTerm2 Profiles

Configure iTerm2 profiles for visual context switching.

## Auto-Installed Profiles

Dynamic profiles are automatically installed and ready to use:

| Profile | Icon | Theme | Use Case |
|---------|------|-------|----------|
| Dev-Tools | 🔧 | Amber/Orange | Shell scripts, CLI tools |
| Emacs | ⚡ | Purple/Magenta | Emacs configurations |
| Python-Dev | 🐍 | Green | Python projects |
| Node-Dev | 📦 | Dark | Node.js projects |
| R-Dev | 📦 | Blue | R packages, Quarto |
| AI-Session | 🤖 | Purple | Claude/Gemini sessions |
| Production | 🚨 | Red | Production warning |

## Profile Mappings

| Context Type | Profile Used | Icon |
|--------------|--------------|------|
| R packages | R-Dev | 📦 |
| Python projects | Python-Dev | 🐍 |
| Node.js projects | Node-Dev | 📦 |
| Quarto projects | R-Dev | 📊 |
| MCP servers | AI-Session | 🔌 |
| Emacs configs | Emacs | ⚡ |
| Dev-tools | Dev-Tools | 🔧 |
| AI sessions | AI-Session | 🤖 |
| Production | Production | 🚨 |
| Default | Default | (none) |

## Important: Title Configuration

For profile switching to work, each profile must have:

1. **General → Title**: Set to **"Session Name"**
2. **Check**: "Applications in terminal may change title"

Without this, escape sequences won't update the title.

## Dynamic Profiles Location

Profiles are stored in:

```
~/Library/Application Support/iTerm2/DynamicProfiles/context-switcher-profiles.json
```

## Creating Custom Profiles

### Custom Dynamic Profiles

Add to the existing JSON file:

```json
{
  "Name": "My-Profile",
  "Guid": "unique-id-here",
  "Dynamic Profile Parent Name": "Default",
  "Background Color": {
    "Red Component": 0.1,
    "Green Component": 0.1,
    "Blue Component": 0.1,
    "Alpha Component": 1
  }
}
```

## Profile Color Reference

| Profile | Background | Foreground |
|---------|------------|------------|
| R-Dev | Dark blue (#141f2e) | Light blue (#cce6ff) |
| AI-Session | Dark purple (#1f1429) | Light purple (#e6d9ff) |
| Production | Dark red (#330d0d) | Light red (#ffd9d9) |
| Dev-Tools | Dark brown (#1f1a0f) | Amber (#ffc259) |
| Emacs | Dark purple (#1a1424) | Light purple (#d9ccf2) |
| Python-Dev | Green (#137746) | Yellow (#fff0a5) |
| Node-Dev | Dark (#121212) | Gray (#bfbfbf) |

## Troubleshooting

**Profile doesn't switch:**

- Ensure `$TERM_PROGRAM` equals `iTerm.app`
- Check profile name matches exactly (case-sensitive)
- Verify profile exists in iTerm2 Preferences

**Title doesn't update:**

- Set Title to "Session Name" in profile settings
- Enable "Applications in terminal may change title"
