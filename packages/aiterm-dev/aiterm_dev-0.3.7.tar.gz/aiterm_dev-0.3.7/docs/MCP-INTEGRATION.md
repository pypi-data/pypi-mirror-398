# MCP Server Management

**Status:** ✅ Complete (v0.2.0-dev)

The MCP (Model Context Protocol) integration allows you to discover, test, and validate MCP servers configured in Claude Code.

## Overview

MCP servers extend Claude Code's capabilities by providing access to external tools, APIs, and services. The `aiterm mcp` commands help you manage these servers effectively.

**Key Features:**
- 📡 Discover all configured MCP servers
- ✅ Test server reachability and health
- 🔍 Validate configuration format
- 📊 View detailed server information
- 🏥 Health check for all servers

---

## Quick Start

```bash
# List all configured servers
aiterm mcp list

# Validate your configuration
aiterm mcp validate

# Test a specific server
aiterm mcp test statistical-research

# View server details
aiterm mcp info statistical-research

# Test all servers
aiterm mcp test-all
```

---

## Commands

### `aiterm mcp list`

List all configured MCP servers from `~/.claude/settings.json`.

**Output:**
```
                📡 Configured MCP Servers
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Server Name          ┃ Command    ┃ Args           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ statistical-research │ bun        │ run src/ind... │
│ github               │ npx        │ -y @modelco... │
│ rforge               │ rforge-mcp │ -              │
└──────────────────────┴────────────┴────────────────┘

Total servers: 3
Config: /Users/dt/.claude/settings.json

Test a server: aiterm mcp test <name>
```

**Use Cases:**
- See what MCP servers you have configured
- Quick overview of server commands
- Check if a server is installed

---

### `aiterm mcp test <server>`

Test if a specific MCP server is reachable by running its command with `--help`.

**Arguments:**
- `server` - Name of the server to test

**Options:**
- `--timeout, -t` - Timeout in seconds (default: 5.0)

**Example:**
```bash
aiterm mcp test statistical-research --timeout 10
```

**Output (Success):**
```
Testing MCP server: statistical-research...
✓ Server reachable (234ms)

╭──────────── Server: statistical-research ─────────────╮
│ Command: bun                                          │
│ Args: run src/index.ts                                │
│ Full: bun run src/index.ts                            │
╰───────────────────────────────────────────────────────╯
```

**Output (Success):**
```
Testing MCP server: rforge...
✓ Server reachable (142ms)

╭────────────────── Server: rforge ─────────────────────╮
│ Command: rforge                                       │
│ Args: (none)                                          │
│ Full: rforge                                          │
╰───────────────────────────────────────────────────────╯
```

**Use Cases:**
- Verify a server is properly installed
- Debug server configuration issues
- Check if command is in PATH

---

### `aiterm mcp test-all`

Test all configured MCP servers and display a summary.

**Options:**
- `--timeout, -t` - Timeout per server in seconds (default: 5.0)

**Example:**
```bash
aiterm mcp test-all --timeout 3
```

**Output:**
```
Testing 3 MCP servers...

                    🧪 Server Test Results
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Server               ┃ Status      ┃ Time ┃ Notes          ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━┩
│ statistical-research │ ✓ Reachable │ 234ms│ -              │
│ github               │ ✓ Reachable │ 156ms│ -              │
│ rforge               │ ✓ Reachable │ 142ms│ -              │
└──────────────────────┴─────────────┴──────┴────────────────┘

Results: 3 passed, 0 failed
```

**Use Cases:**
- Health check for all servers
- Verify MCP setup after installation
- Troubleshoot multiple server issues

---

### `aiterm mcp validate`

Validate the MCP server configuration in `~/.claude/settings.json`.

**Output (Valid):**
```
Validating MCP configuration...

  🔍 Configuration Validation
┌────────────────────┬─────────┐
│ Settings file      │ ✓ Found │
│ JSON syntax        │ ✓ Valid │
│ Servers configured │ 5       │
└────────────────────┴─────────┘

Configuration is valid! ✨

Config: /Users/dt/.claude/settings.json
```

**Output (Invalid):**
```
Validating MCP configuration...

  🔍 Configuration Validation
┌────────────────────┬──────────┐
│ Settings file      │ ✓ Found  │
│ JSON syntax        │ ✗ Invalid│
└────────────────────┴──────────┘

Issues found:
  ✗ Invalid JSON: Expecting ',' delimiter: line 12 column 5

Config: /Users/dt/.claude/settings.json
```

**Checks Performed:**
- ✅ Settings file exists
- ✅ Valid JSON syntax
- ✅ `mcpServers` section present
- ✅ Each server has required `command` field
- ✅ `args` field is an array (if present)
- ✅ `env` field is an object (if present)
- ⚠️ Command path exists (for absolute paths)

**Use Cases:**
- Verify settings.json format
- Debug configuration errors
- Check for missing required fields

---

### `aiterm mcp info <server>`

Show detailed information about a specific MCP server.

**Arguments:**
- `server` - Name of the server

**Example:**
```bash
aiterm mcp info statistical-research
```

**Output:**
```
╭──────────── MCP Server Info ────────────╮
│ statistical-research                    │
│                                         │
│ Command: bun                            │
│ Args: run src/index.ts                  │
│ Environment: 2 variables                │
│                                         │
│ Full command:                           │
│ bun run src/index.ts                    │
╰─────────────────────────────────────────╯

Environment Variables:
  R_LIBS_USER=~/R/library
  ZOTERO_API_KEY=***xyz123

Config: /Users/dt/.claude/settings.json
```

**Features:**
- 📋 Full command string
- 🔐 Masked sensitive environment variables
  - Keys containing: `key`, `secret`, `token`, `password`
  - Shows only last 4 characters
- 📁 Configuration file location

**Use Cases:**
- View complete server configuration
- Debug environment variables
- Copy full command for manual testing

---

## Configuration

MCP servers are configured in `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "statistical-research": {
      "command": "bun",
      "args": ["run", "src/index.ts"],
      "env": {
        "R_LIBS_USER": "~/R/library",
        "ZOTERO_API_KEY": "your-key-here"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/projects"
      ]
    }
  }
}
```

**Configuration Fields:**

| Field     | Required | Type   | Description                    |
|-----------|----------|--------|--------------------------------|
| `command` | ✅ Yes   | string | Command to execute             |
| `args`    | ❌ No    | array  | Command-line arguments         |
| `env`     | ❌ No    | object | Environment variables          |

---

## Common Workflows

### 1. Initial Setup Check

After installing Claude Code and configuring MCP servers:

```bash
# Validate configuration
aiterm mcp validate

# List all servers
aiterm mcp list

# Test all servers
aiterm mcp test-all
```

### 2. Adding a New Server

After adding a new MCP server to settings.json:

```bash
# Validate the configuration
aiterm mcp validate

# Test the new server
aiterm mcp test new-server-name

# View server details
aiterm mcp info new-server-name
```

### 3. Troubleshooting

When a server isn't working in Claude Code:

```bash
# Check if server is configured
aiterm mcp list | grep server-name

# Test server reachability
aiterm mcp test server-name

# View full configuration
aiterm mcp info server-name

# Validate all settings
aiterm mcp validate
```

### 4. Health Monitoring

Periodic health check for all servers:

```bash
# Quick test of all servers
aiterm mcp test-all --timeout 3

# For slower servers, increase timeout
aiterm mcp test-all --timeout 10
```

---

## Troubleshooting

### Server Not Found

**Error:** `Server 'xyz' not found in settings`

**Solution:**
1. Check server name spelling
2. Run `aiterm mcp list` to see configured servers
3. Verify settings.json has the server entry

### Command Not Found

**Error:** `Command not found: xyz`

**Solutions:**
1. **Check if command is installed:**
   ```bash
   which xyz
   ```

2. **Use absolute path:**
   ```json
   {
     "command": "/usr/local/bin/xyz"
   }
   ```

3. **Add to PATH:**
   ```bash
   export PATH="/path/to/command:$PATH"
   ```

4. **For Node.js packages:**
   ```bash
   npm install -g package-name
   ```

5. **For Python packages:**
   ```bash
   pip install package-name
   ```

### Timeout Errors

**Error:** `Server timed out after 5s`

**Solutions:**
1. **Increase timeout:**
   ```bash
   aiterm mcp test server-name --timeout 10
   ```

2. **Check if server is slow to start:**
   - Some servers require initialization
   - Try running command manually first

3. **Check network connectivity:**
   - Some servers require internet access
   - Verify firewall settings

### Invalid JSON

**Error:** `Invalid JSON: ...`

**Solutions:**
1. **Use a JSON validator:**
   ```bash
   python3 -m json.tool ~/.claude/settings.json
   ```

2. **Common JSON mistakes:**
   - Missing commas between entries
   - Trailing commas in arrays/objects
   - Unquoted keys or values
   - Unescaped special characters

3. **Backup before editing:**
   ```bash
   cp ~/.claude/settings.json ~/.claude/settings.json.backup
   ```

---

## Integration with Claude Code

The MCP manager integrates with Claude Code's settings file:

**Settings Location:**
- macOS: `~/.claude/settings.json`
- Linux: `~/.claude/settings.json`
- Windows: `%USERPROFILE%\.claude\settings.json`

**Reading Settings:**
```python
from aiterm.mcp import MCPManager

manager = MCPManager()
servers = manager.list_servers()

for server in servers:
    print(f"{server.name}: {server.full_command}")
```

**Testing Servers:**
```python
result = manager.test_server("statistical-research", timeout=5.0)

if result["success"]:
    print(f"✓ Server reachable in {result['duration_ms']:.0f}ms")
else:
    print(f"✗ Failed: {result['error']}")
```

**Validating Configuration:**
```python
validation = manager.validate_config()

if validation["valid"]:
    print(f"✓ Configuration valid ({validation['servers_count']} servers)")
else:
    for issue in validation["issues"]:
        print(f"✗ {issue}")
```

---

## Architecture

### MCPServer Dataclass

```python
@dataclass
class MCPServer:
    name: str              # Server name (key in settings.json)
    command: str           # Command to execute
    args: List[str]        # Command arguments
    env: Dict[str, str]    # Environment variables
    config_path: Path      # Path to settings.json

    @property
    def full_command(self) -> str:
        """Get full command string."""
        args_str = " ".join(self.args)
        return f"{self.command} {args_str}".strip()
```

### MCPManager Class

**Methods:**
- `list_servers()` → List[MCPServer]
  - Parse settings.json
  - Return list of configured servers
  - Sorted alphabetically by name

- `test_server(name, timeout)` → Dict[str, Any]
  - Run `command --help` to test reachability
  - Measure execution time
  - Return success/failure with error details

- `validate_config()` → Dict[str, Any]
  - Check settings.json exists and is valid JSON
  - Validate mcpServers section structure
  - Check each server has required fields
  - Verify command paths exist (for absolute paths)

- `get_server_info(name)` → Optional[Dict[str, Any]]
  - Get detailed server configuration
  - Return None if server not found
  - Include masked environment variables

---

## Examples

### Example 1: List Servers Programmatically

```python
from aiterm.mcp import MCPManager

manager = MCPManager()
servers = manager.list_servers()

print(f"Found {len(servers)} MCP servers:")
for server in servers:
    print(f"  - {server.name}: {server.command}")
```

### Example 2: Test All Servers

```python
from aiterm.mcp import MCPManager

manager = MCPManager()
servers = manager.list_servers()

for server in servers:
    result = manager.test_server(server.name)

    if result["success"]:
        print(f"✓ {server.name}: {result['duration_ms']:.0f}ms")
    else:
        print(f"✗ {server.name}: {result['error']}")
```

### Example 3: Validate Configuration

```python
from aiterm.mcp import MCPManager

manager = MCPManager()
validation = manager.validate_config()

if validation["valid"]:
    print("✓ Configuration valid")
    print(f"  - Settings file exists: {validation['settings_exists']}")
    print(f"  - Valid JSON: {validation['valid_json']}")
    print(f"  - Servers configured: {validation['servers_count']}")
else:
    print("✗ Configuration invalid:")
    for issue in validation["issues"]:
        print(f"  - {issue}")
```

---

## See Also

- [Claude Code Documentation](https://docs.anthropic.com/claude/docs)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [aiterm API Reference](api/AITERM-API.md)

---

**Version:** v0.2.0-dev
**Last Updated:** 2025-12-24
**Status:** ✅ Complete
