# MCP Servers Migration Plan

**Date:** 2025-12-19
**Project:** Consolidate MCP servers into unified location
**Time Estimate:** 45-60 minutes

---

## 🎯 Goal

Move all MCP servers to `~/projects/dev-tools/mcp-servers/` for better organization and discoverability.

---

## 📊 Current → New Structure

### Before
```
~/projects/dev-tools/
├── claude-statistical-research/
│   ├── mcp-server/          ← MCP subdirectory
│   ├── skills/
│   ├── docs/
│   └── ... (full project)
├── shell-mcp-server/        ← Standalone MCP
│   └── index.js
└── project-refactor-mcp/    ← Standalone MCP
    └── index.js
```

### After
```
~/projects/dev-tools/
├── mcp-servers/             ← NEW unified location
│   ├── statistical-research/
│   │   ├── src/
│   │   ├── skills/
│   │   └── ...
│   ├── shell/
│   │   └── index.js
│   ├── project-refactor/
│   │   └── index.js
│   └── README.md
└── claude-statistical-research/  ← Archive or keep docs/skills
    ├── docs/
    ├── skills/
    └── README.md
```

---

## 🔧 ZSH Functions & Aliases (Following Standards)

Based on `/Users/dt/projects/dev-tools/zsh-configuration/` conventions:

### Function Design Principles
1. **Verb-noun pattern**: `action-target` (e.g., `list-servers`, `test-mcp`)
2. **Short aliases**: 2-3 chars for frequent commands
3. **Smart dispatchers**: Use existing `cc` (Claude Code) or `gm` (Gemini) patterns
4. **Help integration**: Works with `ah` (alias help) system

### Proposed Functions (in `mcp-utils.zsh`)

```zsh
#!/usr/bin/env zsh
# mcp-utils.zsh - MCP server management utilities

# === Core Functions ===

# List all MCP servers
mcp-list() {
    local mcp_dir="$HOME/projects/dev-tools/mcp-servers"

    print_header "MCP Servers"

    if [[ ! -d "$mcp_dir" ]]; then
        print_error "MCP servers directory not found: $mcp_dir"
        return 1
    fi

    for server in "$mcp_dir"/*(/); do
        local name=$(basename "$server")
        echo "${fg[cyan]}●${reset_color} $name"

        # Check if configured
        if grep -q "\"$name\"" ~/.claude/settings.json 2>/dev/null; then
            echo "  ${fg[green]}✓${reset_color} Desktop/CLI"
        fi

        if grep -q "\"$name\"" ~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json 2>/dev/null; then
            echo "  ${fg[green]}✓${reset_color} Browser"
        fi
    done
}

# Navigate to MCP servers directory
mcp-cd() {
    local server="$1"
    local mcp_dir="$HOME/projects/dev-tools/mcp-servers"

    if [[ -z "$server" ]]; then
        cd "$mcp_dir"
    else
        if [[ -d "$mcp_dir/$server" ]]; then
            cd "$mcp_dir/$server"
        else
            print_error "Server not found: $server"
            print_info "Available servers:"
            ls -1 "$mcp_dir"
            return 1
        fi
    fi
}

# Edit MCP server code
mcp-edit() {
    local server="$1"
    local mcp_dir="$HOME/projects/dev-tools/mcp-servers"

    if [[ -z "$server" ]]; then
        print_error "Usage: mcp-edit <server-name>"
        mcp-list
        return 1
    fi

    if [[ -d "$mcp_dir/$server" ]]; then
        ${EDITOR:-code} "$mcp_dir/$server"
    else
        print_error "Server not found: $server"
        return 1
    fi
}

# View MCP server README
mcp-readme() {
    local server="$1"
    local mcp_dir="$HOME/projects/dev-tools/mcp-servers"

    if [[ -z "$server" ]]; then
        # Show main README
        if [[ -f "$mcp_dir/README.md" ]]; then
            ${PAGER:-less} "$mcp_dir/README.md"
        else
            print_error "README.md not found"
        fi
    else
        # Show server README
        if [[ -f "$mcp_dir/$server/README.md" ]]; then
            ${PAGER:-less} "$mcp_dir/$server/README.md"
        else
            print_error "README not found for: $server"
        fi
    fi
}

# Test MCP server (validate it runs)
mcp-test() {
    local server="$1"
    local mcp_dir="$HOME/projects/dev-tools/mcp-servers"

    if [[ -z "$server" ]]; then
        print_error "Usage: mcp-test <server-name>"
        mcp-list
        return 1
    fi

    if [[ ! -d "$mcp_dir/$server" ]]; then
        print_error "Server not found: $server"
        return 1
    fi

    print_info "Testing MCP server: $server"

    # Different runtimes for different servers
    case "$server" in
        statistical-research)
            cd "$mcp_dir/$server" && bun run src/index.ts &
            ;;
        shell|project-refactor)
            cd "$mcp_dir/$server" && node index.js &
            ;;
        *)
            print_warning "Unknown runtime for: $server"
            return 1
            ;;
    esac

    local pid=$!
    sleep 2

    if kill -0 $pid 2>/dev/null; then
        print_success "Server started (PID: $pid)"
        print_warning "Stopping test server..."
        kill $pid
    else
        print_error "Server failed to start"
        return 1
    fi
}

# Show MCP configuration status
mcp-status() {
    print_header "MCP Configuration Status"

    echo "${fg[cyan]}Desktop/CLI:${reset_color}"
    if [[ -f ~/.claude/settings.json ]]; then
        local desktop_count=$(grep -c "\"command\"" ~/.claude/settings.json | tail -1)
        print_success "~/.claude/settings.json ($desktop_count servers configured)"
    else
        print_error "~/.claude/settings.json not found"
    fi

    echo ""
    echo "${fg[cyan]}Browser Extension:${reset_color}"
    if [[ -f ~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json ]]; then
        local browser_count=$(grep -c "\"command\"" ~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json | tail -1)
        print_success "MCP_SERVER_CONFIG.json ($browser_count servers configured)"
    else
        print_error "MCP_SERVER_CONFIG.json not found"
    fi
}

# Interactive MCP server picker (using fzf)
mcp-pick() {
    local mcp_dir="$HOME/projects/dev-tools/mcp-servers"

    if ! command -v fzf &>/dev/null; then
        print_error "fzf not installed"
        return 1
    fi

    local server=$(ls -1 "$mcp_dir" | fzf --prompt="Select MCP server: " --height=40%)

    if [[ -n "$server" ]]; then
        echo "${fg[cyan]}Selected:${reset_color} $server"
        echo ""
        echo "What would you like to do?"
        echo "  ${fg[green]}1)${reset_color} Navigate to server"
        echo "  ${fg[green]}2)${reset_color} Edit in $EDITOR"
        echo "  ${fg[green]}3)${reset_color} View README"
        echo "  ${fg[green]}4)${reset_color} Test server"
        echo ""
        read "choice?Choice: "

        case "$choice" in
            1) mcp-cd "$server" ;;
            2) mcp-edit "$server" ;;
            3) mcp-readme "$server" ;;
            4) mcp-test "$server" ;;
            *) print_error "Invalid choice" ;;
        esac
    fi
}

# === Aliases ===

# Short aliases (ADHD-friendly)
alias mcpl='mcp-list'           # List servers
alias mcpc='mcp-cd'             # Navigate to server
alias mcpe='mcp-edit'           # Edit server
alias mcpt='mcp-test'           # Test server
alias mcps='mcp-status'         # Show config status
alias mcpr='mcp-readme'         # View README
alias mcpp='mcp-pick'           # Interactive picker

# Ultra-short for frequent use
alias ml='mcp-list'             # Most common: list servers
alias mc='mcp-cd'               # Most common: navigate

# Integration with smart dispatchers
# cc mcp <command>  - Claude Code MCP management (already exists)
# gm mcp <command>  - Gemini MCP management (already exists)
```

### Integration with Existing Smart Dispatchers

The existing `cc` (Claude Code) and `gm` (Gemini) dispatchers already support:
- `cc mcp` - MCP server management via Claude Code CLI
- `gm mcp` - MCP server management via Gemini CLI

Our functions complement these by adding:
- Direct server access (navigate, edit, test)
- Quick visualization (list, status)
- Interactive selection (pick with fzf)

---

## 📋 Migration Steps

### Phase 1: Preparation (10 min)

1. **Backup current state**
   ```bash
   cd ~/projects/dev-tools
   tar -czf ~/mcp-servers-backup-$(date +%Y%m%d).tar.gz \
     claude-statistical-research/mcp-server \
     shell-mcp-server \
     project-refactor-mcp
   ```

2. **Create new directory**
   ```bash
   mkdir -p ~/projects/dev-tools/mcp-servers
   ```

3. **Verify git status**
   ```bash
   cd ~/projects/dev-tools/claude-statistical-research && git status
   cd ~/projects/dev-tools/shell-mcp-server && git status
   cd ~/projects/dev-tools/project-refactor-mcp && git status
   ```

### Phase 2: Move Servers (15 min)

**Decision Point:** statistical-research is a full project, not just an MCP server.

**Option A (Recommended):** Move only MCP implementation, keep project structure
```bash
# Move MCP server
mv ~/projects/dev-tools/claude-statistical-research/mcp-server \
   ~/projects/dev-tools/mcp-servers/statistical-research

# Keep skills with MCP server (they're tightly coupled)
mv ~/projects/dev-tools/claude-statistical-research/skills \
   ~/projects/dev-tools/mcp-servers/statistical-research/

# Optionally keep docs in original location or move
# (Docs describe the whole ecosystem, not just MCP)
```

**Option B:** Move entire project
```bash
mv ~/projects/dev-tools/claude-statistical-research \
   ~/projects/dev-tools/mcp-servers/statistical-research
```

**Move standalone servers:**
```bash
# Shell MCP
mv ~/projects/dev-tools/shell-mcp-server \
   ~/projects/dev-tools/mcp-servers/shell

# Project Refactor MCP
mv ~/projects/dev-tools/project-refactor-mcp \
   ~/projects/dev-tools/mcp-servers/project-refactor
```

### Phase 3: Update Configurations (10 min)

1. **Update Claude Desktop/CLI config** (`~/.claude/settings.json`):
   ```json
   {
     "mcpServers": {
       "statistical-research": {
         "command": "bun",
         "args": ["run", "/Users/dt/projects/dev-tools/mcp-servers/statistical-research/src/index.ts"],
         "env": {
           "R_LIBS_USER": "~/R/library"
         }
       },
       "project-refactor": {
         "command": "node",
         "args": ["/Users/dt/projects/dev-tools/mcp-servers/project-refactor/index.js"]
       }
     }
   }
   ```

2. **Update Browser Extension config** (`~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json`):
   ```json
   {
     "servers": {
       "shell": {
         "args": ["/Users/dt/projects/dev-tools/mcp-servers/shell/index.js"]
       },
       "statistical-research": {
         "args": ["run", "/Users/dt/projects/dev-tools/mcp-servers/statistical-research/src/index.ts"]
       },
       "project-refactor": {
         "args": ["/Users/dt/projects/dev-tools/mcp-servers/project-refactor/index.js"]
       }
     }
   }
   ```

3. **Update symlinks**:
   ```bash
   rm -rf ~/mcp-servers
   mkdir -p ~/mcp-servers

   ln -s ~/projects/dev-tools/mcp-servers/statistical-research ~/mcp-servers/statistical-research
   ln -s ~/projects/dev-tools/mcp-servers/shell ~/mcp-servers/shell
   ln -s ~/projects/dev-tools/mcp-servers/project-refactor ~/mcp-servers/project-refactor
   ```

### Phase 4: Update Documentation (10 min)

1. **Create main README** (`~/projects/dev-tools/mcp-servers/README.md`)
2. **Update `_MCP_SERVERS.md`** with new paths
3. **Update `~/.claude/CLAUDE.md`** MCP section
4. **Update aiterm CLAUDE.md** if it references MCP servers

### Phase 5: Testing (10 min)

1. **Test Claude Desktop/CLI**:
   ```bash
   # Restart Claude Code to reload config
   claude --version

   # Test a session - MCP tools should be available
   cd ~/test-project
   claude
   ```

2. **Test Browser Extension**:
   - Reload extension in Chrome: `chrome://extensions/`
   - Open claude.ai
   - Test MCP tools availability

3. **Test ZSH functions**:
   ```bash
   mcp-list              # Should show all 3 servers
   mcp-cd shell          # Should navigate to shell server
   mcp-status            # Should show configs are valid
   ```

### Phase 6: Cleanup (5 min)

1. **Remove old directories** (if fully moved):
   ```bash
   # Only if you moved everything and verified it works
   rm -rf ~/projects/dev-tools/shell-mcp-server
   rm -rf ~/projects/dev-tools/project-refactor-mcp
   # (Keep claude-statistical-research if you kept docs there)
   ```

2. **Commit changes**:
   ```bash
   cd ~/projects/dev-tools/mcp-servers/statistical-research
   git add -A
   git commit -m "chore: move MCP server to unified location"

   # Similar for other servers
   ```

---

## ⚠️ Rollback Plan

If something breaks:

```bash
# Restore from backup
cd ~/projects/dev-tools
tar -xzf ~/mcp-servers-backup-$(date +%Y%m%d).tar.gz

# Restore old configs
git checkout ~/.claude/settings.json
git checkout ~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json

# Remove new directory
rm -rf ~/projects/dev-tools/mcp-servers

# Restore old symlinks
rm -rf ~/mcp-servers
mkdir -p ~/mcp-servers
ln -s ~/projects/dev-tools/claude-statistical-research/mcp-server ~/mcp-servers/statistical-research
ln -s ~/projects/dev-tools/shell-mcp-server ~/mcp-servers/shell
ln -s ~/projects/dev-tools/project-refactor-mcp ~/mcp-servers/project-refactor
```

---

## 📝 Post-Migration Checklist

- [ ] All 3 servers appear in `mcp-list`
- [ ] Can navigate with `mcp-cd <server>`
- [ ] Claude Desktop loads MCP tools
- [ ] Browser extension loads MCP tools
- [ ] Symlinks work: `cd ~/mcp-servers/<server>`
- [ ] Documentation updated
- [ ] Old directories removed (optional)
- [ ] Git repos have proper history

---

## 🚀 Next Steps (After Migration)

1. **Add ZSH functions to zsh-configuration**:
   - Create `~/projects/dev-tools/zsh-configuration/zsh/functions/mcp-utils.zsh`
   - Source in `.zshrc`

2. **Integrate with aiterm v0.2.0**:
   - `aiterm mcp list` - Wrapper around `mcp-list`
   - `aiterm mcp test` - Automated testing
   - `aiterm mcp migrate` - For future moves

3. **Document in ALIAS-REFERENCE-CARD.md**:
   - Add MCP section with all aliases
   - Update `ah mcp` help text

---

**Ready to proceed?** Let's execute Phase 1 (Preparation)!
