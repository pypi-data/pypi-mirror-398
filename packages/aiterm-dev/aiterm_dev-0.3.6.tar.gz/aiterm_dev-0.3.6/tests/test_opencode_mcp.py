"""Tests for OpenCode MCP server connectivity and validation."""

import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aiterm.opencode.config import MCPServer, OpenCodeConfig, load_config


# =============================================================================
# MCPServer Model Tests
# =============================================================================


class TestMCPServerModel:
    """Tests for MCPServer dataclass."""

    def test_server_with_command(self) -> None:
        """Should create server with command list."""
        server = MCPServer(
            name="filesystem",
            type="local",
            enabled=True,
            command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/Users/dt"],
        )
        assert server.name == "filesystem"
        assert server.enabled is True
        assert len(server.command) == 4
        assert server.command[0] == "npx"

    def test_server_with_environment(self) -> None:
        """Should create server with environment variables."""
        server = MCPServer(
            name="github",
            type="local",
            enabled=True,
            command=["npx", "-y", "@modelcontextprotocol/server-github"],
            environment={"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
        )
        assert server.environment is not None
        assert "GITHUB_TOKEN" in server.environment

    def test_server_to_dict(self) -> None:
        """Should serialize server to dict."""
        server = MCPServer(
            name="memory",
            type="local",
            enabled=True,
            command=["npx", "-y", "@modelcontextprotocol/server-memory"],
        )
        data = server.to_dict()
        assert data["type"] == "local"
        assert data["enabled"] is True
        assert data["command"] == ["npx", "-y", "@modelcontextprotocol/server-memory"]

    def test_server_uvx_command(self) -> None:
        """Should handle uvx-based servers."""
        server = MCPServer(
            name="time",
            type="local",
            enabled=True,
            command=["uvx", "mcp-server-time"],
        )
        assert server.command[0] == "uvx"
        assert server.command[1] == "mcp-server-time"


# =============================================================================
# MCP Server Command Validation Tests
# =============================================================================


class TestMCPServerCommandValidation:
    """Tests for validating MCP server commands."""

    def test_npx_available(self) -> None:
        """npx should be available for npm-based servers."""
        result = shutil.which("npx")
        assert result is not None, "npx not found in PATH"

    def test_uvx_available(self) -> None:
        """uvx should be available for Python-based servers."""
        result = shutil.which("uvx")
        assert result is not None, "uvx not found in PATH"

    def test_validate_server_command_npx(self) -> None:
        """Should validate npx-based server command."""
        server = MCPServer(
            name="filesystem",
            type="local",
            enabled=True,
            command=["npx", "-y", "@modelcontextprotocol/server-filesystem"],
        )
        # Check executable exists
        executable = server.command[0] if server.command else None
        assert executable is not None
        assert shutil.which(executable) is not None

    def test_validate_server_command_uvx(self) -> None:
        """Should validate uvx-based server command."""
        server = MCPServer(
            name="time",
            type="local",
            enabled=True,
            command=["uvx", "mcp-server-time"],
        )
        executable = server.command[0] if server.command else None
        assert executable is not None
        assert shutil.which(executable) is not None

    def test_invalid_executable(self) -> None:
        """Should detect invalid executable."""
        server = MCPServer(
            name="invalid",
            type="local",
            enabled=True,
            command=["nonexistent-binary-xyz", "arg1"],
        )
        executable = server.command[0] if server.command else None
        assert shutil.which(executable) is None


# =============================================================================
# MCP Server Connectivity Tests (Mocked)
# =============================================================================


class TestMCPServerConnectivity:
    """Tests for MCP server connectivity (mocked)."""

    def test_server_startup_success(self) -> None:
        """Should detect successful server startup."""
        server = MCPServer(
            name="memory",
            type="local",
            enabled=True,
            command=["npx", "-y", "@modelcontextprotocol/server-memory"],
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = None  # Still running
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            # Simulate server startup
            process = subprocess.Popen(
                server.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            assert process.poll() is None  # Server should still be running
            assert process.pid == 12345

    def test_server_startup_failure(self) -> None:
        """Should detect failed server startup."""
        server = MCPServer(
            name="invalid",
            type="local",
            enabled=True,
            command=["nonexistent-command"],
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("Command not found")

            with pytest.raises(FileNotFoundError):
                subprocess.Popen(
                    server.command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

    def test_server_immediate_exit(self) -> None:
        """Should detect server that exits immediately."""
        server = MCPServer(
            name="broken",
            type="local",
            enabled=True,
            command=["echo", "exit"],
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = 1  # Exited with error
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            process = subprocess.Popen(
                server.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            assert process.poll() == 1  # Server exited


# =============================================================================
# MCP Server Configuration Tests
# =============================================================================


class TestMCPServerConfiguration:
    """Tests for MCP server configuration parsing."""

    def test_load_servers_from_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load MCP servers from config file."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
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
                        "time": {
                            "type": "local",
                            "enabled": False,
                            "command": ["uvx", "mcp-server-time"],
                        },
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )

        config = load_config()
        assert len(config.mcp_servers) == 3
        assert config.mcp_servers["filesystem"].enabled is True
        assert config.mcp_servers["memory"].enabled is True
        assert config.mcp_servers["time"].enabled is False

    def test_enabled_servers_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return list of enabled servers."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "mcp": {
                        "filesystem": {"type": "local", "enabled": True},
                        "memory": {"type": "local", "enabled": True},
                        "time": {"type": "local", "enabled": False},
                        "github": {"type": "local", "enabled": True},
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )

        config = load_config()
        enabled = config.enabled_servers
        assert len(enabled) == 3
        assert "filesystem" in enabled
        assert "memory" in enabled
        assert "github" in enabled
        assert "time" not in enabled

    def test_disabled_servers_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return list of disabled servers."""
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "mcp": {
                        "filesystem": {"type": "local", "enabled": True},
                        "playwright": {"type": "local", "enabled": False},
                        "puppeteer": {"type": "local", "enabled": False},
                    },
                }
            )
        )
        monkeypatch.setattr(
            "aiterm.opencode.config.get_config_path",
            lambda: config_path,
        )

        config = load_config()
        disabled = config.disabled_servers
        assert len(disabled) == 2
        assert "playwright" in disabled
        assert "puppeteer" in disabled


# =============================================================================
# MCP Server Health Check Tests
# =============================================================================


class TestMCPServerHealthCheck:
    """Tests for MCP server health check functionality."""

    def test_check_server_command_exists(self) -> None:
        """Should check if server command executable exists."""
        # Valid npx command
        assert shutil.which("npx") is not None

        # Valid uvx command
        assert shutil.which("uvx") is not None

    def test_check_environment_variables(self) -> None:
        """Should validate environment variable references."""
        server = MCPServer(
            name="github",
            type="local",
            enabled=True,
            command=["npx", "-y", "@modelcontextprotocol/server-github"],
            environment={"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
        )

        # Check for variable reference pattern
        for key, value in (server.environment or {}).items():
            if value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                # This is a reference, not a literal value
                assert var_name == "GITHUB_TOKEN"


# =============================================================================
# Integration Tests (require actual servers)
# =============================================================================


@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration tests for actual MCP server connectivity.

    These tests require actual MCP servers to be installed.
    Run with: pytest -m integration
    """

    def test_filesystem_server_starts(self) -> None:
        """Test that filesystem server can start."""
        try:
            # Try to start the server briefly
            process = subprocess.Popen(
                ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Give it a moment to start
            import time

            time.sleep(2)

            # Check if still running (good) or exited with error (bad)
            exit_code = process.poll()

            # Clean up
            if exit_code is None:
                process.terminate()
                process.wait(timeout=5)

            # Server should either still be running (None) or exit cleanly
            # Note: MCP servers may exit immediately without stdin
            assert exit_code is None or exit_code == 0

        except FileNotFoundError:
            pytest.skip("npx not available")

    def test_memory_server_starts(self) -> None:
        """Test that memory server can start."""
        try:
            process = subprocess.Popen(
                ["npx", "-y", "@modelcontextprotocol/server-memory"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            import time

            time.sleep(2)

            exit_code = process.poll()

            if exit_code is None:
                process.terminate()
                process.wait(timeout=5)

            assert exit_code is None or exit_code == 0

        except FileNotFoundError:
            pytest.skip("npx not available")

    def test_time_server_starts(self) -> None:
        """Test that time server can start."""
        try:
            process = subprocess.Popen(
                ["uvx", "mcp-server-time"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            import time

            time.sleep(2)

            exit_code = process.poll()

            if exit_code is None:
                process.terminate()
                process.wait(timeout=5)

            assert exit_code is None or exit_code == 0

        except FileNotFoundError:
            pytest.skip("uvx not available")


# =============================================================================
# Server Test Utility Functions
# =============================================================================


def validate_server_executable(server: MCPServer) -> tuple[bool, str]:
    """Validate that server executable exists.

    Args:
        server: MCPServer instance to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not server.command:
        return False, "No command specified"

    executable = server.command[0]
    if shutil.which(executable) is None:
        return False, f"Executable '{executable}' not found in PATH"

    return True, f"Executable '{executable}' found"


def check_server_can_start(server: MCPServer, timeout: float = 3.0) -> tuple[bool, str]:
    """Check if server can start successfully.

    Args:
        server: MCPServer instance to check
        timeout: How long to wait for startup

    Returns:
        Tuple of (can_start, message)
    """
    if not server.command:
        return False, "No command specified"

    try:
        import time

        process = subprocess.Popen(
            server.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        time.sleep(timeout)
        exit_code = process.poll()

        if exit_code is None:
            # Still running - good!
            process.terminate()
            process.wait(timeout=5)
            return True, "Server started successfully"
        elif exit_code == 0:
            return True, "Server started and exited cleanly"
        else:
            stderr = process.stderr.read().decode() if process.stderr else ""
            return False, f"Server exited with code {exit_code}: {stderr[:200]}"

    except FileNotFoundError as e:
        return False, f"Command not found: {e}"
    except Exception as e:
        return False, f"Failed to start: {e}"


class TestServerTestUtilities:
    """Tests for server test utility functions."""

    def test_validate_server_executable_valid(self) -> None:
        """Should validate valid executable."""
        server = MCPServer(
            name="test",
            type="local",
            enabled=True,
            command=["npx", "-y", "test-package"],
        )
        is_valid, msg = validate_server_executable(server)
        assert is_valid is True
        assert "npx" in msg

    def test_validate_server_executable_invalid(self) -> None:
        """Should detect invalid executable."""
        server = MCPServer(
            name="test",
            type="local",
            enabled=True,
            command=["nonexistent-binary-xyz"],
        )
        is_valid, msg = validate_server_executable(server)
        assert is_valid is False
        assert "not found" in msg

    def test_validate_server_no_command(self) -> None:
        """Should handle server with no command."""
        server = MCPServer(
            name="test",
            type="local",
            enabled=True,
            command=[],
        )
        is_valid, msg = validate_server_executable(server)
        assert is_valid is False
        assert "No command" in msg
