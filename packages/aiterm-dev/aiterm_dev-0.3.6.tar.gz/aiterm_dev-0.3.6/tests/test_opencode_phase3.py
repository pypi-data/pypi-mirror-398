"""Tests for OpenCode Phase 3 features.

Phase 3 features:
- Research agent (Opus 4.5)
- Custom commands (with template field)
- Tool configuration (boolean enable/disable)
- Time MCP server

Note: Keybinds are NOT supported by OpenCode schema (v1.0.203+).
Tests for keybinds have been removed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aiterm.cli.main import app
from aiterm.opencode.config import (
    Command,
    OpenCodeConfig,
    load_config,
    save_config,
)

runner = CliRunner()


# =============================================================================
# Command Dataclass Tests
# =============================================================================


class TestCommand:
    """Tests for Command dataclass (new schema with template field)."""

    def test_create_basic_command(self) -> None:
        """Should create a basic command with template."""
        cmd = Command(
            name="test",
            template="echo test",
            description="Test command",
        )
        assert cmd.name == "test"
        assert cmd.template == "echo test"
        assert cmd.description == "Test command"

    def test_command_defaults(self) -> None:
        """Should have correct default values."""
        cmd = Command(name="test")
        assert cmd.template == ""
        assert cmd.description == ""
        assert cmd.agent == ""
        assert cmd.model == ""
        assert cmd.subtask is False

    def test_command_to_dict(self) -> None:
        """Should convert to dictionary correctly."""
        cmd = Command(
            name="sync",
            template="git add -A && git commit -m 'sync' && git push",
            description="Git sync",
        )
        d = cmd.to_dict()
        assert d["description"] == "Git sync"
        assert d["template"] == "git add -A && git commit -m 'sync' && git push"

    def test_command_to_dict_minimal(self) -> None:
        """Should exclude empty fields in to_dict."""
        cmd = Command(name="test")
        d = cmd.to_dict()
        assert d == {}


# =============================================================================
# Research Agent Tests
# =============================================================================


class TestResearchAgent:
    """Tests for research agent configuration."""

    def test_research_agent_exists(self, tmp_path: Path) -> None:
        """Should load config with research agent (new schema)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "agent": {
                "research": {
                    "description": "Academic research and manuscript writing",
                    "model": "anthropic/claude-opus-4-5",
                    "tools": {"read": True, "write": True, "websearch": True, "webfetch": True},
                }
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert "research" in config.agents
        assert config.agents["research"].model == "anthropic/claude-opus-4-5"

    def test_research_agent_with_old_format(self, tmp_path: Path) -> None:
        """Should load config with research agent (old schema with list tools)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "agents": {
                "research": {
                    "description": "Academic research",
                    "model": "anthropic/claude-opus-4-5",
                    "tools": ["read", "write", "websearch", "webfetch"],
                }
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert "research" in config.agents
        # Old list format should be converted to dict
        assert config.agents["research"].tools == {
            "read": True, "write": True, "websearch": True, "webfetch": True
        }

    def test_research_agent_tools(self, tmp_path: Path) -> None:
        """Should have web tools for research."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "agent": {
                "research": {
                    "model": "anthropic/claude-opus-4-5",
                    "tools": {"read": True, "write": True, "websearch": True, "webfetch": True},
                }
            }
        }))

        config = load_config(config_file)
        assert config is not None
        tools = config.agents["research"].tools
        assert tools.get("websearch") is True
        assert tools.get("webfetch") is True

    def test_research_agent_uses_opus(self, tmp_path: Path) -> None:
        """Research agent should use Opus model."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "agent": {
                "research": {"model": "anthropic/claude-opus-4-5"}
            }
        }))

        config = load_config(config_file)
        assert "opus" in config.agents["research"].model.lower()


# =============================================================================
# Commands Tests (New Schema)
# =============================================================================


class TestCommands:
    """Tests for custom commands configuration (new schema with template)."""

    def test_load_commands_new_format(self, tmp_path: Path) -> None:
        """Should load commands from config (new schema with template)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "command": {
                "sync": {
                    "template": "git add -A && git commit -m 'sync' && git push",
                    "description": "Git sync",
                },
                "status": {
                    "template": "git status",
                    "description": "Show status",
                },
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert len(config.commands) == 2
        assert "sync" in config.commands
        assert config.commands["sync"].template == "git add -A && git commit -m 'sync' && git push"

    def test_load_commands_old_format(self, tmp_path: Path) -> None:
        """Should load commands from old schema (with command field)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "commands": {
                "sync": {
                    "command": "git push",
                    "description": "Git sync",
                },
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert "sync" in config.commands
        # Old "command" field should be parsed into "template"
        assert config.commands["sync"].template == "git push"

    def test_r_package_commands(self, tmp_path: Path) -> None:
        """Should load R package commands."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "command": {
                "rpkg-check": {
                    "template": "R CMD check --as-cran .",
                    "description": "Run R CMD check",
                },
                "rpkg-document": {
                    "template": "Rscript -e 'devtools::document()'",
                    "description": "Generate documentation",
                },
                "rpkg-test": {
                    "template": "Rscript -e 'devtools::test()'",
                    "description": "Run tests",
                },
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert len(config.commands) == 3
        assert "rpkg-check" in config.commands
        assert "rpkg-document" in config.commands
        assert "rpkg-test" in config.commands

    def test_commands_to_dict(self, tmp_path: Path) -> None:
        """Should serialize commands correctly (new schema)."""
        config = OpenCodeConfig(
            path=tmp_path / "config.json",
            commands={
                "test": Command(
                    name="test",
                    template="echo test",
                    description="Test command",
                ),
            },
        )
        d = config.to_dict()
        # Should use singular "command" key
        assert "command" in d
        assert "commands" not in d
        assert d["command"]["test"]["template"] == "echo test"
        assert d["command"]["test"]["description"] == "Test command"


# =============================================================================
# Tool Configuration Tests (New Schema)
# =============================================================================


class TestToolConfiguration:
    """Tests for tool configuration (new schema with boolean values)."""

    def test_load_tools_new_format(self, tmp_path: Path) -> None:
        """Should load tools from config (new boolean format)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "tools": {
                "bash": True,
                "read": True,
                "write": True,
                "edit": True,
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert len(config.tools) == 4
        assert config.tools["bash"] is True
        assert config.tools["write"] is True

    def test_load_tools_old_format(self, tmp_path: Path) -> None:
        """Should load tools from old schema (with permission objects)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "tools": {
                "bash": {"permission": "auto"},
                "read": {"permission": "auto"},
                "write": {"permission": "ask"},
                "edit": {"permission": "deny"},
            }
        }))

        config = load_config(config_file)
        assert config is not None
        # Old format should be converted to boolean (deny = False, others = True)
        assert config.tools["bash"] is True
        assert config.tools["read"] is True
        assert config.tools["write"] is True  # "ask" still means enabled
        assert config.tools["edit"] is False  # "deny" means disabled

    def test_enabled_disabled_tools(self, tmp_path: Path) -> None:
        """Should track enabled and disabled tools."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "tools": {
                "bash": True,
                "read": True,
                "write": False,
                "edit": False,
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert set(config.enabled_tools) == {"bash", "read"}
        assert set(config.disabled_tools) == {"write", "edit"}

    def test_tools_to_dict(self, tmp_path: Path) -> None:
        """Should serialize tools correctly (new boolean format)."""
        config = OpenCodeConfig(
            path=tmp_path / "config.json",
            tools={"bash": True, "write": False},
        )
        d = config.to_dict()
        assert "tools" in d
        assert d["tools"]["bash"] is True
        assert d["tools"]["write"] is False


# =============================================================================
# Time MCP Server Tests
# =============================================================================


class TestTimeMCPServer:
    """Tests for Time MCP server configuration."""

    def test_time_server_enabled(self, tmp_path: Path) -> None:
        """Should load config with time server enabled."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "mcp": {
                "time": {
                    "type": "local",
                    "enabled": True,
                    "command": ["npx", "-y", "@modelcontextprotocol/server-time"],
                }
            }
        }))

        config = load_config(config_file)
        assert config is not None
        assert "time" in config.mcp_servers
        assert config.mcp_servers["time"].enabled is True

    def test_time_server_in_enabled_list(self, tmp_path: Path) -> None:
        """Time server should appear in enabled_servers."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "mcp": {
                "filesystem": {"type": "local", "enabled": True, "command": ["test"]},
                "memory": {"type": "local", "enabled": True, "command": ["test"]},
                "time": {"type": "local", "enabled": True, "command": ["test"]},
            }
        }))

        config = load_config(config_file)
        assert "time" in config.enabled_servers


# =============================================================================
# CLI Commands Command Tests
# =============================================================================


class TestCommandsCommand:
    """Tests for commands CLI command."""

    def test_commands_list_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should show message when no commands configured."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "commands"])
        assert result.exit_code == 0
        assert "No custom commands" in result.output

    def test_commands_list_with_commands(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should list configured commands."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "command": {
                "sync": {
                    "template": "git add -A && git commit",
                    "description": "Git sync",
                }
            }
        }))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "commands"])
        assert result.exit_code == 0
        assert "sync" in result.output
        assert "Git sync" in result.output


# =============================================================================
# CLI Tools Command Tests
# =============================================================================


class TestToolsCommand:
    """Tests for tools CLI command."""

    def test_tools_list_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should show message when no tools configured."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "tools"])
        assert result.exit_code == 0
        assert "No tool" in result.output or "configuration" in result.output.lower()

    def test_tools_list_with_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should list configured tools (new boolean format)."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "tools": {
                "bash": True,
                "write": False,
            }
        }))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "tools"])
        assert result.exit_code == 0
        assert "bash" in result.output


# =============================================================================
# CLI Summary Command Tests
# =============================================================================


class TestSummaryCommand:
    """Tests for summary CLI command."""

    def test_summary_full_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should show complete configuration summary."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "model": "anthropic/claude-sonnet-4-5",
            "small_model": "anthropic/claude-haiku-4-5",
            "default_agent": "build",
            "instructions": ["CLAUDE.md"],
            "tui": {"scroll_acceleration": {"enabled": True}},
            "command": {"sync": {"template": "git push"}},
            "tools": {"bash": True, "read": True},
            "agent": {
                "r-dev": {"model": "anthropic/claude-sonnet-4-5"},
                "quick": {"model": "anthropic/claude-haiku-4-5"},
            },
            "mcp": {
                "filesystem": {"type": "local", "enabled": True, "command": ["test"]},
                "memory": {"type": "local", "enabled": True, "command": ["test"]},
            },
        }))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "summary"])
        assert result.exit_code == 0
        # Check summary includes key sections
        assert "anthropic/claude-sonnet-4-5" in result.output
        assert "Agents" in result.output or "agent" in result.output.lower()


# =============================================================================
# Integration Test: Full Phase 3 Config (New Schema)
# =============================================================================


class TestPhase3Integration:
    """Integration tests for complete Phase 3 configuration."""

    def test_full_phase3_config(self, tmp_path: Path) -> None:
        """Should load and validate complete Phase 3 config (new schema)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "model": "anthropic/claude-sonnet-4-5",
            "small_model": "anthropic/claude-haiku-4-5",
            "default_agent": "build",
            "instructions": ["CLAUDE.md", ".claude/rules/*.md"],
            "tui": {"scroll_acceleration": {"enabled": True}},
            "command": {
                "rpkg-check": {"template": "R CMD check --as-cran .", "description": "Run R CMD check"},
                "rpkg-document": {"template": "Rscript -e 'devtools::document()'", "description": "Generate docs"},
                "rpkg-test": {"template": "Rscript -e 'devtools::test()'", "description": "Run tests"},
                "sync": {"template": "git add -A && git commit -m 'sync' && git push", "description": "Git sync"},
                "status": {"template": "git status && git log --oneline -5", "description": "Show status"},
            },
            "tools": {
                "bash": True,
                "read": True,
                "glob": True,
                "grep": True,
                "write": True,
                "edit": True,
            },
            "agent": {
                "r-dev": {
                    "description": "R package development specialist",
                    "model": "anthropic/claude-sonnet-4-5",
                    "tools": {"bash": True, "read": True, "write": True, "edit": True, "glob": True, "grep": True},
                },
                "quick": {
                    "description": "Fast responses for simple questions",
                    "model": "anthropic/claude-haiku-4-5",
                    "tools": {"read": True, "glob": True, "grep": True},
                },
                "research": {
                    "description": "Academic research and manuscript writing",
                    "model": "anthropic/claude-opus-4-5",
                    "tools": {"read": True, "write": True, "edit": True, "glob": True, "grep": True, "websearch": True, "webfetch": True},
                },
            },
            "mcp": {
                "filesystem": {"type": "local", "enabled": True, "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"]},
                "memory": {"type": "local", "enabled": True, "command": ["npx", "-y", "@modelcontextprotocol/server-memory"]},
                "time": {"type": "local", "enabled": True, "command": ["npx", "-y", "@modelcontextprotocol/server-time"]},
                "github": {"type": "local", "enabled": True, "command": ["npx", "-y", "@modelcontextprotocol/server-github"]},
            },
        }))

        config = load_config(config_file)
        assert config is not None

        # Validate Phase 3 features
        # 3.1: Research agent
        assert "research" in config.agents
        assert "opus" in config.agents["research"].model.lower()
        assert config.agents["research"].tools.get("websearch") is True

        # 3.2: Commands (new schema)
        assert len(config.commands) == 5
        assert "rpkg-check" in config.commands
        assert "sync" in config.commands
        assert config.commands["sync"].template == "git add -A && git commit -m 'sync' && git push"

        # 3.3: Tools (new boolean format)
        assert len(config.tools) == 6
        assert config.tools["bash"] is True
        assert config.tools["write"] is True

        # 3.4: Time MCP
        assert "time" in config.mcp_servers
        assert config.mcp_servers["time"].enabled is True
        assert "time" in config.enabled_servers

        # Validate config is valid
        valid, errors = config.is_valid()
        assert valid is True, f"Config should be valid: {errors}"

    def test_roundtrip_phase3_config(self, tmp_path: Path) -> None:
        """Should save and reload Phase 3 config identically."""
        config_file = tmp_path / "config.json"

        # Create Phase 3 config with new schema
        original = OpenCodeConfig(
            path=config_file,
            model="anthropic/claude-sonnet-4-5",
            commands={"sync": Command(name="sync", template="git push")},
            tools={"bash": True, "read": True, "write": False},
        )

        # Save
        assert save_config(original) is True

        # Reload
        loaded = load_config(config_file)
        assert loaded is not None

        # Compare
        assert loaded.tools == original.tools
        assert "sync" in loaded.commands
        assert loaded.commands["sync"].template == "git push"
