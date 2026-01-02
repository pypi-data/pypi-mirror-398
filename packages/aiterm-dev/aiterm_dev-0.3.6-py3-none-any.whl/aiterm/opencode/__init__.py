"""OpenCode configuration management module.

Schema Reference (OpenCode 1.0.203+):
- tools: dict[str, bool] (not permission objects)
- agent: singular key in JSON (not "agents")
- command: singular key in JSON (not "commands")
- mcp.*.environment: for env vars (not "env")
- Agent.tools: dict[str, bool] (not list)
- Command.template: required (not "command")
"""

from .config import (
    OpenCodeConfig,
    MCPServer,
    Agent,
    Command,
    load_config,
    save_config,
    validate_config,
    get_config_path,
    backup_config,
    RECOMMENDED_MODELS,
    DEFAULT_MCP_SERVERS,
    VALID_AGENT_MODES,
)

__all__ = [
    "OpenCodeConfig",
    "MCPServer",
    "Agent",
    "Command",
    "load_config",
    "save_config",
    "validate_config",
    "get_config_path",
    "backup_config",
    "RECOMMENDED_MODELS",
    "DEFAULT_MCP_SERVERS",
    "VALID_AGENT_MODES",
]
