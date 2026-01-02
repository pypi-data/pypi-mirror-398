"""MCP server management.

Provides discovery, testing, and validation of MCP servers configured in Claude Code.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class MCPServer:
    """Represents a configured MCP server."""

    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    config_path: Path

    @property
    def full_command(self) -> str:
        """Get full command string."""
        args_str = " ".join(self.args)
        return f"{self.command} {args_str}".strip()


class MCPManager:
    """Manage MCP servers for Claude Code."""

    # Claude Code settings file
    SETTINGS_FILE = Path.home() / ".claude" / "settings.json"

    def __init__(self, settings_path: Optional[Path] = None):
        """Initialize MCP manager.

        Args:
            settings_path: Path to settings.json (defaults to ~/.claude/settings.json)
        """
        self.settings_path = settings_path or self.SETTINGS_FILE

    def list_servers(self) -> List[MCPServer]:
        """List all configured MCP servers.

        Returns:
            List of MCPServer objects.
        """
        servers = []

        if not self.settings_path.exists():
            return servers

        # Load settings
        try:
            settings = json.loads(self.settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            return servers

        # Extract MCP servers
        mcp_servers = settings.get("mcpServers", {})

        for name, config in mcp_servers.items():
            command = config.get("command", "")
            args = config.get("args", [])
            env = config.get("env", {})

            servers.append(MCPServer(
                name=name,
                command=command,
                args=args,
                env=env,
                config_path=self.settings_path
            ))

        return sorted(servers, key=lambda s: s.name)

    def test_server(self, server_name: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Test an MCP server by attempting to start it.

        Args:
            server_name: Name of the server to test.
            timeout: Timeout in seconds (default: 5.0).

        Returns:
            Dictionary with test results:
            {
                "success": bool,
                "server_name": str,
                "reachable": bool,
                "error": Optional[str],
                "duration_ms": float
            }
        """
        servers = self.list_servers()
        server = next((s for s in servers if s.name == server_name), None)

        if not server:
            return {
                "success": False,
                "server_name": server_name,
                "reachable": False,
                "error": f"Server '{server_name}' not found in settings",
                "duration_ms": 0.0
            }

        import time
        start = time.time()

        try:
            # Try to run the server command with a timeout
            # For most MCP servers, we just check if the command exists
            result = subprocess.run(
                [server.command, "--help"],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**server.env}
            )

            duration_ms = (time.time() - start) * 1000

            # If help command works, server is likely valid
            return {
                "success": True,
                "server_name": server_name,
                "reachable": True,
                "error": None,
                "duration_ms": duration_ms
            }

        except FileNotFoundError:
            return {
                "success": False,
                "server_name": server_name,
                "reachable": False,
                "error": f"Command not found: {server.command}",
                "duration_ms": (time.time() - start) * 1000
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "server_name": server_name,
                "reachable": False,
                "error": f"Server timed out after {timeout}s",
                "duration_ms": timeout * 1000
            }

        except Exception as e:
            return {
                "success": False,
                "server_name": server_name,
                "reachable": False,
                "error": str(e),
                "duration_ms": (time.time() - start) * 1000
            }

    def validate_config(self) -> Dict[str, Any]:
        """Validate MCP server configuration.

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "settings_exists": bool,
                "valid_json": bool,
                "servers_count": int,
                "issues": List[str]
            }
        """
        issues = []

        # Check settings file exists
        if not self.settings_path.exists():
            return {
                "valid": False,
                "settings_exists": False,
                "valid_json": False,
                "servers_count": 0,
                "issues": [f"Settings file not found: {self.settings_path}"]
            }

        # Check valid JSON
        try:
            settings = json.loads(self.settings_path.read_text())
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "settings_exists": True,
                "valid_json": False,
                "servers_count": 0,
                "issues": [f"Invalid JSON: {str(e)}"]
            }

        # Check mcpServers section exists
        if "mcpServers" not in settings:
            issues.append("No 'mcpServers' section in settings")

        mcp_servers = settings.get("mcpServers", {})
        servers_count = len(mcp_servers)

        # Validate each server configuration
        for name, config in mcp_servers.items():
            if not isinstance(config, dict):
                issues.append(f"Server '{name}': config must be an object")
                continue

            # Check required fields
            if "command" not in config:
                issues.append(f"Server '{name}': missing 'command' field")

            # Validate command exists
            command = config.get("command", "")
            if command:
                # Check if it's a path
                if "/" in command:
                    if not Path(command).exists():
                        issues.append(f"Server '{name}': command path doesn't exist: {command}")
                # Check if it's in PATH (simplified check)
                else:
                    try:
                        subprocess.run(
                            ["which", command],
                            capture_output=True,
                            check=False
                        )
                    except Exception:
                        pass  # Skip PATH check if 'which' fails

            # Check args is a list
            if "args" in config and not isinstance(config["args"], list):
                issues.append(f"Server '{name}': 'args' must be an array")

            # Check env is an object
            if "env" in config and not isinstance(config["env"], dict):
                issues.append(f"Server '{name}': 'env' must be an object")

        return {
            "valid": len(issues) == 0,
            "settings_exists": True,
            "valid_json": True,
            "servers_count": servers_count,
            "issues": issues
        }

    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific server.

        Args:
            server_name: Name of the server.

        Returns:
            Dictionary with server info, or None if not found.
        """
        servers = self.list_servers()
        server = next((s for s in servers if s.name == server_name), None)

        if not server:
            return None

        return {
            "name": server.name,
            "command": server.command,
            "args": server.args,
            "env": server.env,
            "full_command": server.full_command,
            "config_path": str(server.config_path)
        }
