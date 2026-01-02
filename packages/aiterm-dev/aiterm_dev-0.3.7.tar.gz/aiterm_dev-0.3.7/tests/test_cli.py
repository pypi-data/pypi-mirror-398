"""Tests for aiterm CLI."""

import json
import platform
import sys

from typer.testing import CliRunner

from aiterm import __version__
from aiterm.cli.main import app, get_install_path, get_platform_info

runner = CliRunner()


def test_version():
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_shows_python_version():
    """Test --version flag shows Python version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert python_version in result.output


def test_version_shows_platform():
    """Test --version flag shows platform info."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert platform.system() in result.output


def test_version_shows_install_path():
    """Test --version flag shows installation path."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Path:" in result.output
    # Should contain 'aiterm' in the path
    assert "aiterm" in result.output


def test_get_install_path():
    """Test get_install_path helper function."""
    path = get_install_path()
    assert "aiterm" in path
    assert path.endswith("aiterm") or "aiterm" in path


def test_get_platform_info():
    """Test get_platform_info helper function."""
    info = get_platform_info()
    assert platform.system() in info
    assert platform.machine() in info


def test_help():
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "aiterm" in result.output


def test_init():
    """Test init command."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Setup wizard" in result.output


def test_hello():
    """Test hello command."""
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output
    assert "aiterm is working correctly" in result.output


def test_hello_with_name():
    """Test hello command with --name option."""
    result = runner.invoke(app, ["hello", "--name", "Claude"])
    assert result.exit_code == 0
    assert "Hello, Claude!" in result.output


def test_hello_with_short_option():
    """Test hello command with -n short option."""
    result = runner.invoke(app, ["hello", "-n", "DT"])
    assert result.exit_code == 0
    assert "Hello, DT!" in result.output


def test_goodbye():
    """Test goodbye command."""
    result = runner.invoke(app, ["goodbye"])
    assert result.exit_code == 0
    assert "Goodbye, World!" in result.output
    assert "Until next time!" in result.output


def test_goodbye_with_name():
    """Test goodbye command with --name option."""
    result = runner.invoke(app, ["goodbye", "--name", "Claude"])
    assert result.exit_code == 0
    assert "Goodbye, Claude!" in result.output


def test_goodbye_with_short_option():
    """Test goodbye command with -n short option."""
    result = runner.invoke(app, ["goodbye", "-n", "DT"])
    assert result.exit_code == 0
    assert "Goodbye, DT!" in result.output


def test_doctor():
    """Test doctor command."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Health check" in result.output


def test_profile_list():
    """Test profile list command."""
    result = runner.invoke(app, ["profile", "list"])
    assert result.exit_code == 0
    assert "Available Profiles" in result.output


def test_claude_settings():
    """Test claude settings command."""
    result = runner.invoke(app, ["claude", "settings"])
    assert result.exit_code == 0


def test_context_detect():
    """Test context detect command."""
    result = runner.invoke(app, ["context", "detect"])
    assert result.exit_code == 0
    assert "Context Detection" in result.output


def test_context_show():
    """Test context show command."""
    result = runner.invoke(app, ["context", "show"])
    assert result.exit_code == 0
    assert "Context Detection" in result.output


def test_context_apply():
    """Test context apply command."""
    result = runner.invoke(app, ["context", "apply"])
    assert result.exit_code == 0
    # Should show warning about not being in iTerm2
    assert "Context Detection" in result.output


# ─── Shortcut command tests ──────────────────────────────────────────────────


def test_detect_shortcut():
    """Test detect shortcut command."""
    result = runner.invoke(app, ["detect"])
    assert result.exit_code == 0
    assert "Context Detection" in result.output


def test_switch_shortcut():
    """Test switch shortcut command."""
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0
    assert "Context Detection" in result.output


# ─── Claude command tests ────────────────────────────────────────────────────


def test_claude_backup():
    """Test claude backup command."""
    result = runner.invoke(app, ["claude", "backup"])
    # Will either create backup or report no settings found
    assert result.exit_code == 0


def test_claude_approvals_list():
    """Test claude approvals list command."""
    result = runner.invoke(app, ["claude", "approvals", "list"])
    assert result.exit_code == 0


def test_claude_approvals_presets():
    """Test claude approvals presets command."""
    result = runner.invoke(app, ["claude", "approvals", "presets"])
    assert result.exit_code == 0
    assert "Available Presets" in result.output
    assert "safe-reads" in result.output
    assert "git-ops" in result.output


# ─── Info command tests ───────────────────────────────────────────────────────


def test_info():
    """Test info command."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "System Information" in result.output
    assert __version__ in result.output


def test_info_shows_python():
    """Test info command shows Python information."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Python" in result.output
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert python_version in result.output


def test_info_shows_platform():
    """Test info command shows platform information."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Platform" in result.output
    assert platform.system() in result.output


def test_info_shows_dependencies():
    """Test info command shows dependencies."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Dependencies" in result.output
    assert "typer" in result.output
    assert "rich" in result.output


def test_info_shows_tools():
    """Test info command shows external tools."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "External Tools" in result.output
    assert "git" in result.output
    assert "claude" in result.output


def test_info_shows_environment():
    """Test info command shows environment info."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Environment" in result.output
    assert "Shell" in result.output


def test_info_json_output():
    """Test info command with --json flag."""
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    # Should be valid JSON
    data = json.loads(result.output)
    assert "aiterm" in data
    assert "python" in data
    assert "platform" in data
    assert "dependencies" in data
    assert "tools" in data


def test_info_json_contains_version():
    """Test info --json contains version info."""
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["aiterm"]["version"] == __version__


def test_info_json_contains_python_info():
    """Test info --json contains Python info."""
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    expected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert data["python"]["version"] == expected_version
    assert "executable" in data["python"]


def test_info_json_contains_platform():
    """Test info --json contains platform info."""
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["platform"]["system"] == platform.system()
    assert data["platform"]["machine"] == platform.machine()


def test_info_short_json_flag():
    """Test info command with -j short flag."""
    result = runner.invoke(app, ["info", "-j"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "aiterm" in data
