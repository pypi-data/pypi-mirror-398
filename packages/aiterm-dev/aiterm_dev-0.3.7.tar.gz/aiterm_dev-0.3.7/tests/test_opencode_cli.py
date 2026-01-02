"""Tests for OpenCode CLI commands."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aiterm.cli.main import app

runner = CliRunner()


# =============================================================================
# OpenCode Config Command Tests
# =============================================================================


class TestOpenCodeConfig:
    """Tests for opencode config command."""

    def test_config_no_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle missing config file gracefully."""
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: tmp_path / "nonexistent" / "config.json",
        )
        result = runner.invoke(app, ["opencode", "config"])
        assert result.exit_code == 0
        assert "No OpenCode configuration found" in result.output

    def test_config_with_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should display config from valid file."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "model": "anthropic/claude-sonnet-4-5",
                    "small_model": "anthropic/claude-haiku-4-5",
                    "tui": {"scroll_acceleration": {"enabled": True}},
                    "mcp": {
                        "filesystem": {"type": "local", "enabled": True},
                        "memory": {"type": "local", "enabled": True},
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "config"])
        assert result.exit_code == 0
        assert "anthropic/claude-sonnet-4-5" in result.output
        assert "2 enabled" in result.output

    def test_config_raw_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should output raw JSON with --raw flag."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "model": "anthropic/claude-sonnet-4-5",
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "config", "--raw"])
        assert result.exit_code == 0
        # Should be valid JSON
        output_data = json.loads(result.output)
        assert output_data["model"] == "anthropic/claude-sonnet-4-5"


class TestOpenCodeValidate:
    """Tests for opencode validate command."""

    def test_validate_no_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should report missing config."""
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: tmp_path / "nonexistent.json",
        )
        result = runner.invoke(app, ["opencode", "validate"])
        assert result.exit_code == 0
        assert "has issues" in result.output or "not found" in result.output

    def test_validate_valid_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should validate a proper config."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "model": "anthropic/claude-sonnet-4-5",
                    "mcp": {
                        "filesystem": {
                            "type": "local",
                            "enabled": True,
                            "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
                        },
                        "memory": {
                            "type": "local",
                            "enabled": True,
                            "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
                        },
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "validate"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()


class TestOpenCodeBackup:
    """Tests for opencode backup command."""

    def test_backup_no_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle missing config."""
        # Patch both the config module and CLI module's imported version
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: tmp_path / "nonexistent.json",
        )
        monkeypatch.setattr(
            "aiterm.cli.opencode.get_config_path",
            lambda: tmp_path / "nonexistent.json",
        )
        result = runner.invoke(app, ["opencode", "backup"])
        assert result.exit_code == 0
        assert "No OpenCode configuration found" in result.output

    def test_backup_creates_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should create backup file."""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"model": "test"}')
        # Need to patch both the source module AND the CLI module's imported reference
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        monkeypatch.setattr(
            "aiterm.cli.opencode.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "backup"])
        assert result.exit_code == 0
        assert "Backup created" in result.output
        # Check backup was created
        backups = list(tmp_path.glob("*.backup-*.json"))
        assert len(backups) == 1


# =============================================================================
# OpenCode Agents Command Tests
# =============================================================================


class TestOpenCodeAgents:
    """Tests for opencode agents commands."""

    def test_agents_list_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should show message when no agents configured."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "agents", "list"])
        assert result.exit_code == 0
        assert "No custom agents" in result.output
        assert "Built-in modes" in result.output

    def test_agents_list_with_agents(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should list configured agents."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "agent": {
                        "r-dev": {
                            "description": "R development",
                            "model": "anthropic/claude-sonnet-4-5",
                            "tools": {"bash": True, "read": True, "write": True},
                        }
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "agents", "list"])
        assert result.exit_code == 0
        assert "r-dev" in result.output
        assert "R development" in result.output

    def test_agents_add(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should add a new agent."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(
            app,
            [
                "opencode",
                "agents",
                "add",
                "quick",
                "--desc",
                "Fast responses",
                "--model",
                "anthropic/claude-haiku-4-5",
            ],
        )
        assert result.exit_code == 0
        assert "Added agent 'quick'" in result.output

        # Verify saved (uses singular "agent" key in new schema)
        saved = json.loads(config_path.read_text())
        assert "quick" in saved["agent"]
        assert saved["agent"]["quick"]["model"] == "anthropic/claude-haiku-4-5"

    def test_agents_add_invalid_model(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should reject invalid model format."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(
            app,
            ["opencode", "agents", "add", "test", "--model", "invalid-model"],
        )
        assert result.exit_code == 1
        assert "Invalid model format" in result.output

    def test_agents_remove(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should remove an agent."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "agent": {"r-dev": {"description": "R development"}},
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "agents", "remove", "r-dev"])
        assert result.exit_code == 0
        assert "Removed agent 'r-dev'" in result.output

        # Verify removed (uses singular "agent" key in new schema)
        saved = json.loads(config_path.read_text())
        assert "agent" not in saved or "r-dev" not in saved.get("agent", {})

    def test_agents_remove_nonexistent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should error when removing nonexistent agent."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "agents", "remove", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output


# =============================================================================
# OpenCode Servers Command Tests
# =============================================================================


class TestOpenCodeServers:
    """Tests for opencode servers commands."""

    def test_servers_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should list MCP servers."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "mcp": {
                        "filesystem": {"type": "local", "enabled": True},
                        "memory": {"type": "local", "enabled": True},
                        "playwright": {"type": "local", "enabled": False},
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "servers", "list"])
        assert result.exit_code == 0
        assert "filesystem" in result.output
        assert "enabled" in result.output

    def test_servers_enable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should enable a disabled server."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "mcp": {"playwright": {"type": "local", "enabled": False}},
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "servers", "enable", "playwright"])
        assert result.exit_code == 0
        assert "Enabled 'playwright'" in result.output

        # Verify saved
        saved = json.loads(config_path.read_text())
        assert saved["mcp"]["playwright"]["enabled"] is True

    def test_servers_disable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should disable an enabled server."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "mcp": {"filesystem": {"type": "local", "enabled": True}},
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "servers", "disable", "filesystem"])
        assert result.exit_code == 0
        assert "Disabled 'filesystem'" in result.output

        # Verify saved
        saved = json.loads(config_path.read_text())
        assert saved["mcp"]["filesystem"]["enabled"] is False


# =============================================================================
# OpenCode Models Command Tests
# =============================================================================


class TestOpenCodeModels:
    """Tests for opencode models commands."""

    def test_models_list(self) -> None:
        """Should list recommended models."""
        result = runner.invoke(app, ["opencode", "models"])
        assert result.exit_code == 0
        assert "anthropic/claude-sonnet-4-5" in result.output
        assert "anthropic/claude-haiku-4-5" in result.output

    def test_set_model(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should set primary model."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(
            app, ["opencode", "set-model", "anthropic/claude-opus-4-5"]
        )
        assert result.exit_code == 0
        assert "Set model to" in result.output

        # Verify saved
        saved = json.loads(config_path.read_text())
        assert saved["model"] == "anthropic/claude-opus-4-5"

    def test_set_small_model(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should set small model with --small flag."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(
            app, ["opencode", "set-model", "anthropic/claude-haiku-4-5", "--small"]
        )
        assert result.exit_code == 0
        assert "Set small_model to" in result.output

        # Verify saved
        saved = json.loads(config_path.read_text())
        assert saved["small_model"] == "anthropic/claude-haiku-4-5"

    def test_set_model_invalid_format(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should reject invalid model format."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}))
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )
        result = runner.invoke(app, ["opencode", "set-model", "invalid"])
        assert result.exit_code == 1
        assert "Invalid model format" in result.output
