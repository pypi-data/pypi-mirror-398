"""OpenCode configuration management.

This module provides tools for managing OpenCode CLI configuration,
including MCP servers, models, agents, and tools.

Schema Reference (OpenCode 1.0.203+):
- tools: dict[str, bool] (not permission objects)
- agent: singular key in JSON (not "agents")
- command: singular key in JSON (not "commands")
- mcp.*.environment: for env vars (not "env")
- Agent.tools: dict[str, bool] (not list)
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Recommended models for OpenCode
RECOMMENDED_MODELS = {
    "primary": [
        "anthropic/claude-sonnet-4-5",
        "anthropic/claude-opus-4-5",
        "anthropic/claude-sonnet-4-0",
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
    ],
    "small": [
        "anthropic/claude-haiku-4-5",
        "google/gemini-2.5-flash-lite",
        "anthropic/claude-3-5-haiku-latest",
    ],
}

# Default MCP servers configuration
DEFAULT_MCP_SERVERS = {
    "filesystem": {
        "type": "local",
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
        "enabled": True,
        "essential": True,
        "description": "File system read/write access",
    },
    "memory": {
        "type": "local",
        "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
        "enabled": True,
        "essential": True,
        "description": "Persistent context memory",
    },
    "sequential-thinking": {
        "type": "local",
        "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
        "enabled": False,
        "essential": False,
        "description": "Complex reasoning chains",
    },
    "playwright": {
        "type": "local",
        "command": ["npx", "-y", "@playwright/mcp@latest", "--browser", "chromium"],
        "enabled": False,
        "essential": False,
        "description": "Browser automation and testing",
    },
    "time": {
        "type": "local",
        "command": ["uvx", "mcp-server-time"],
        "enabled": False,
        "essential": False,
        "description": "Timezone and deadline tracking",
    },
    "github": {
        "type": "local",
        "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
        "enabled": False,
        "essential": False,
        "description": "GitHub integration for PRs and issues",
        "requires_env": ["GITHUB_TOKEN"],
    },
    "brave-search": {
        "type": "local",
        "command": ["npx", "-y", "@anthropic-ai/mcp-server-brave-search"],
        "enabled": False,
        "essential": False,
        "description": "Web search via Brave Search API",
        "requires_env": ["BRAVE_API_KEY"],
    },
    "slack": {
        "type": "local",
        "command": ["npx", "-y", "@anthropic-ai/mcp-server-slack"],
        "enabled": False,
        "essential": False,
        "description": "Slack workspace integration",
        "requires_env": ["SLACK_TOKEN"],
    },
    "sqlite": {
        "type": "local",
        "command": ["uvx", "mcp-server-sqlite"],
        "enabled": False,
        "essential": False,
        "description": "SQLite database access",
    },
    "puppeteer": {
        "type": "local",
        "command": ["npx", "-y", "@anthropic-ai/mcp-server-puppeteer"],
        "enabled": False,
        "essential": False,
        "description": "Headless browser automation",
    },
    "fetch": {
        "type": "local",
        "command": ["uvx", "mcp-server-fetch"],
        "enabled": False,
        "essential": False,
        "description": "HTTP fetch for web content",
    },
    "everything": {
        "type": "local",
        "command": ["npx", "-y", "@modelcontextprotocol/server-everything"],
        "enabled": False,
        "essential": False,
        "description": "Demo server with all features (testing only)",
    },
}

# Valid agent modes (built-in agents)
VALID_AGENT_MODES = ["build", "plan", "general", "explore", "title", "summary", "compaction"]


@dataclass
class MCPServer:
    """Represents an MCP server configuration."""

    name: str
    type: str = "local"
    command: list[str] = field(default_factory=list)
    enabled: bool = False
    environment: dict[str, str] = field(default_factory=dict)
    # Remote server fields
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int | None = None

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate the MCP server configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not self.name:
            errors.append("Server name is required")

        if self.type not in ["local", "remote"]:
            errors.append(f"Invalid server type: {self.type}")

        if self.type == "local" and not self.command:
            errors.append("Local servers require a command")

        if self.type == "remote" and not self.url:
            errors.append("Remote servers require a url")

        if self.command and not isinstance(self.command, list):
            errors.append("Command must be a list of strings")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "type": self.type,
            "enabled": self.enabled,
        }
        if self.command:
            result["command"] = self.command
        if self.environment:
            result["environment"] = self.environment
        if self.url:
            result["url"] = self.url
        if self.headers:
            result["headers"] = self.headers
        if self.timeout is not None:
            result["timeout"] = self.timeout
        return result


@dataclass
class Agent:
    """Represents an OpenCode agent configuration.

    Note: In the OpenCode schema, agent tools are a dict[str, bool],
    not a list of tool names.
    """

    name: str
    description: str = ""
    model: str = ""
    prompt: str = ""
    tools: dict[str, bool] = field(default_factory=dict)
    temperature: float | None = None
    top_p: float | None = None
    disable: bool = False
    mode: str = ""  # "subagent", "primary", or "all"
    color: str = ""  # hex color
    max_steps: int | None = None

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate the agent configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not self.name:
            errors.append("Agent name is required")

        if self.model and "/" not in self.model:
            errors.append(f"Model should be in format 'provider/model': {self.model}")

        if self.mode and self.mode not in ["subagent", "primary", "all"]:
            errors.append(f"Invalid agent mode: {self.mode}")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {}
        if self.description:
            result["description"] = self.description
        if self.model:
            result["model"] = self.model
        if self.prompt:
            result["prompt"] = self.prompt
        if self.tools:
            result["tools"] = self.tools
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.disable:
            result["disable"] = self.disable
        if self.mode:
            result["mode"] = self.mode
        if self.color:
            result["color"] = self.color
        if self.max_steps is not None:
            result["maxSteps"] = self.max_steps
        return result


@dataclass
class Command:
    """Represents a custom OpenCode command.

    Note: OpenCode requires 'template' field (not 'command').
    """

    name: str
    template: str = ""  # Required by OpenCode schema
    description: str = ""
    agent: str = ""  # Optional: which agent executes this
    model: str = ""  # Optional: override model for this command
    subtask: bool = False  # Optional: marks as subtask

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {}
        if self.template:
            result["template"] = self.template
        if self.description:
            result["description"] = self.description
        if self.agent:
            result["agent"] = self.agent
        if self.model:
            result["model"] = self.model
        if self.subtask:
            result["subtask"] = self.subtask
        return result


@dataclass
class OpenCodeConfig:
    """Represents a complete OpenCode configuration.

    Note: OpenCode uses singular keys in JSON:
    - "agent" (not "agents")
    - "command" (not "commands")
    - tools are dict[str, bool] (not permission objects)
    """

    path: Path
    model: str = ""
    small_model: str = ""
    default_agent: str = ""
    mcp_servers: dict[str, MCPServer] = field(default_factory=dict)
    agents: dict[str, Agent] = field(default_factory=dict)
    tools: dict[str, bool] = field(default_factory=dict)
    instructions: list[str] = field(default_factory=list)
    commands: dict[str, Command] = field(default_factory=dict)
    tui: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def enabled_servers(self) -> list[str]:
        """Return list of enabled MCP server names."""
        return [name for name, server in self.mcp_servers.items() if server.enabled]

    @property
    def disabled_servers(self) -> list[str]:
        """Return list of disabled MCP server names."""
        return [name for name, server in self.mcp_servers.items() if not server.enabled]

    @property
    def has_scroll_acceleration(self) -> bool:
        """Check if scroll acceleration is enabled."""
        return self.tui.get("scroll_acceleration", {}).get("enabled", False)

    @property
    def enabled_tools(self) -> list[str]:
        """Return list of enabled tool names."""
        return [name for name, enabled in self.tools.items() if enabled]

    @property
    def disabled_tools(self) -> list[str]:
        """Return list of disabled tool names."""
        return [name for name, enabled in self.tools.items() if not enabled]

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate the complete configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Validate model format
        if self.model and "/" not in self.model:
            errors.append(f"Model should be in format 'provider/model': {self.model}")

        if self.small_model and "/" not in self.small_model:
            errors.append(f"Small model should be in format 'provider/model': {self.small_model}")

        # Validate default agent
        if self.default_agent and self.default_agent not in VALID_AGENT_MODES:
            if self.default_agent not in self.agents:
                errors.append(f"Default agent '{self.default_agent}' not found in agents or modes")

        # Validate MCP servers
        for name, server in self.mcp_servers.items():
            valid, server_errors = server.is_valid()
            if not valid:
                errors.extend([f"MCP server '{name}': {e}" for e in server_errors])

        # Validate agents
        for name, agent in self.agents.items():
            valid, agent_errors = agent.is_valid()
            if not valid:
                errors.extend([f"Agent '{name}': {e}" for e in agent_errors])

        # Validate tools (should be boolean values)
        for tool_name, tool_value in self.tools.items():
            if not isinstance(tool_value, bool):
                errors.append(f"Tool '{tool_name}': expected boolean, got {type(tool_value).__name__}")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Note: Uses OpenCode schema keys (singular: agent, command).
        """
        result: dict[str, Any] = {"$schema": "https://opencode.ai/config.json"}

        if self.model:
            result["model"] = self.model
        if self.small_model:
            result["small_model"] = self.small_model
        if self.default_agent:
            result["default_agent"] = self.default_agent
        if self.instructions:
            result["instructions"] = self.instructions
        if self.tui:
            result["tui"] = self.tui
        if self.commands:
            # Use singular "command" for OpenCode schema
            result["command"] = {name: cmd.to_dict() for name, cmd in self.commands.items()}
        if self.tools:
            result["tools"] = self.tools
        if self.agents:
            # Use singular "agent" for OpenCode schema
            result["agent"] = {name: agent.to_dict() for name, agent in self.agents.items()}
        if self.mcp_servers:
            result["mcp"] = {name: server.to_dict() for name, server in self.mcp_servers.items()}

        return result


def get_config_path() -> Path:
    """Get the default OpenCode config path.

    Returns:
        Path to ~/.config/opencode/config.json
    """
    return Path.home() / ".config" / "opencode" / "config.json"


def _parse_tools(tools_data: Any) -> dict[str, bool]:
    """Parse tools data, handling both old and new formats.

    Args:
        tools_data: Raw tools data from config

    Returns:
        Dictionary of tool_name -> enabled (bool)
    """
    if not isinstance(tools_data, dict):
        return {}

    result = {}
    for name, value in tools_data.items():
        if isinstance(value, bool):
            # New format: {"bash": true}
            result[name] = value
        elif isinstance(value, dict):
            # Old format: {"bash": {"permission": "auto"}}
            # Treat as enabled unless permission is "deny"
            permission = value.get("permission", "auto")
            result[name] = permission != "deny"
        else:
            # Unknown format, default to enabled
            result[name] = True
    return result


def _parse_agent_tools(tools_data: Any) -> dict[str, bool]:
    """Parse agent tools data, handling both list and dict formats.

    Args:
        tools_data: Raw tools data from agent config

    Returns:
        Dictionary of tool_name -> enabled (bool)
    """
    if isinstance(tools_data, dict):
        # New format: {"bash": true, "read": true}
        return {k: bool(v) for k, v in tools_data.items()}
    elif isinstance(tools_data, list):
        # Old format: ["bash", "read", "write"]
        return {name: True for name in tools_data}
    return {}


def load_config(path: Path | None = None) -> OpenCodeConfig | None:
    """Load OpenCode configuration from file.

    Args:
        path: Path to config file. Defaults to ~/.config/opencode/config.json

    Returns:
        OpenCodeConfig object or None if file doesn't exist or is invalid

    Note:
        Handles both old schema (agents, commands, env) and new schema
        (agent, command, environment) for backward compatibility.
    """
    if path is None:
        path = get_config_path()

    if not path.exists():
        return None

    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    # Parse MCP servers
    mcp_servers = {}
    for name, server_data in raw.get("mcp", {}).items():
        if isinstance(server_data, dict):
            # Handle both "environment" (new) and "env" (old) keys
            environment = server_data.get("environment", server_data.get("env", {}))
            mcp_servers[name] = MCPServer(
                name=name,
                type=server_data.get("type", "local"),
                command=server_data.get("command", []),
                enabled=server_data.get("enabled", False),
                environment=environment,
                url=server_data.get("url", ""),
                headers=server_data.get("headers", {}),
                timeout=server_data.get("timeout"),
            )

    # Parse agents - handle both "agent" (new) and "agents" (old) keys
    agents = {}
    agents_data = raw.get("agent", raw.get("agents", {}))
    for name, agent_data in agents_data.items():
        if isinstance(agent_data, dict):
            agents[name] = Agent(
                name=name,
                description=agent_data.get("description", ""),
                model=agent_data.get("model", ""),
                prompt=agent_data.get("prompt", ""),
                tools=_parse_agent_tools(agent_data.get("tools", {})),
                temperature=agent_data.get("temperature"),
                top_p=agent_data.get("top_p"),
                disable=agent_data.get("disable", False),
                mode=agent_data.get("mode", ""),
                color=agent_data.get("color", ""),
                max_steps=agent_data.get("maxSteps"),
            )

    # Parse commands - handle both "command" (new) and "commands" (old) keys
    commands = {}
    commands_data = raw.get("command", raw.get("commands", {}))
    for name, cmd_data in commands_data.items():
        if isinstance(cmd_data, dict):
            # Handle both "template" (new) and "command" (old) keys
            template = cmd_data.get("template", cmd_data.get("command", ""))
            commands[name] = Command(
                name=name,
                template=template,
                description=cmd_data.get("description", ""),
                agent=cmd_data.get("agent", ""),
                model=cmd_data.get("model", ""),
                subtask=cmd_data.get("subtask", False),
            )

    # Parse tools with format detection
    tools = _parse_tools(raw.get("tools", {}))

    # Parse instructions - can be list of strings or list of dicts
    instructions_raw = raw.get("instructions", [])
    instructions = []
    for item in instructions_raw:
        if isinstance(item, str):
            instructions.append(item)
        elif isinstance(item, dict) and "path" in item:
            instructions.append(item["path"])

    return OpenCodeConfig(
        path=path,
        model=raw.get("model", ""),
        small_model=raw.get("small_model", ""),
        default_agent=raw.get("default_agent", ""),
        mcp_servers=mcp_servers,
        agents=agents,
        tools=tools,
        instructions=instructions,
        commands=commands,
        tui=raw.get("tui", {}),
        raw=raw,
    )


def save_config(config: OpenCodeConfig) -> bool:
    """Save OpenCode configuration to file.

    Args:
        config: OpenCodeConfig object to save

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        config.path.parent.mkdir(parents=True, exist_ok=True)
        config.path.write_text(json.dumps(config.to_dict(), indent=2))
        return True
    except OSError:
        return False


def backup_config(path: Path | None = None) -> Path | None:
    """Create a timestamped backup of the config file.

    Args:
        path: Path to config file. Defaults to ~/.config/opencode/config.json

    Returns:
        Path to backup file or None if backup failed
    """
    if path is None:
        path = get_config_path()

    if not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(f".backup-{timestamp}.json")

    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except OSError:
        return None


def validate_config(path: Path | None = None) -> tuple[bool, list[str]]:
    """Validate an OpenCode configuration file.

    Args:
        path: Path to config file. Defaults to ~/.config/opencode/config.json

    Returns:
        Tuple of (is_valid, list of error/warning messages)
    """
    if path is None:
        path = get_config_path()

    errors = []

    # Check file exists
    if not path.exists():
        return False, [f"Config file not found: {path}"]

    # Check JSON is valid
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except OSError as e:
        return False, [f"Cannot read file: {e}"]

    # Check schema
    if "$schema" not in raw:
        errors.append("Missing $schema field (recommended: https://opencode.ai/config.json)")

    # Warn about deprecated keys
    if "agents" in raw:
        errors.append("Deprecated key 'agents' found - use 'agent' (singular)")
    if "commands" in raw:
        errors.append("Deprecated key 'commands' found - use 'command' (singular)")
    if "keybinds" in raw:
        errors.append("Key 'keybinds' is not currently supported by OpenCode")

    # Check for old tool format
    tools_data = raw.get("tools", {})
    for name, value in tools_data.items():
        if isinstance(value, dict):
            errors.append(f"Tool '{name}' uses deprecated format - should be boolean, not object")

    # Check for old env format in MCP servers
    for server_name, server_data in raw.get("mcp", {}).items():
        if isinstance(server_data, dict) and "env" in server_data:
            errors.append(f"MCP server '{server_name}' uses deprecated 'env' key - use 'environment'")

    # Load and validate config
    config = load_config(path)
    if config is None:
        return False, ["Failed to parse configuration"]

    valid, config_errors = config.is_valid()
    errors.extend(config_errors)

    # Additional warnings
    if not config.model:
        errors.append("No model specified (recommend: anthropic/claude-sonnet-4-5)")

    if not config.enabled_servers:
        errors.append("No MCP servers enabled")

    essential_servers = ["filesystem", "memory"]
    for server in essential_servers:
        if server not in config.enabled_servers:
            errors.append(f"Essential server '{server}' not enabled")

    return len([e for e in errors if not e.startswith("No ") and "Deprecated" not in e and "not currently supported" not in e]) == 0, errors
