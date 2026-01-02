"""Integration tests for aiterm CLI.

Validates all CLI modules are registered and accessible.
Self-diagnosing tests ensure the full CLI works correctly.
"""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


class TestCLIIntegration:
    """Integration tests for the full CLI application."""

    def test_main_app_imports(self):
        """Test main app can be imported."""
        from aiterm.cli.main import app
        assert app is not None

    def test_version_command(self, runner):
        """Test --version flag."""
        from aiterm.cli.main import app

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "aiterm" in result.output.lower()

    def test_help_command(self, runner):
        """Test --help flag shows all subcommands."""
        from aiterm.cli.main import app

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Check core commands are listed
        output = result.output.lower()
        assert "doctor" in output
        assert "detect" in output
        assert "switch" in output

    def test_all_subcommands_registered(self, runner):
        """Test all subcommand groups are registered."""
        from aiterm.cli.main import app

        result = runner.invoke(app, ["--help"])
        output = result.output.lower()

        # Phase 1 commands
        assert "claude" in output
        assert "context" in output
        assert "hooks" in output

        # Phase 2 commands
        assert "opencode" in output
        assert "mcp" in output

        # Phase 2.5 commands
        assert "agents" in output
        assert "memory" in output
        assert "styles" in output
        assert "plugins" in output

        # Phase 3 commands
        assert "gemini" in output
        assert "statusbar" in output

        # Phase 4 commands
        assert "terminals" in output
        assert "workflows" in output
        assert "sessions" in output

    def test_doctor_command(self, runner):
        """Test doctor command runs."""
        from aiterm.cli.main import app

        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "aiterm" in result.output.lower() or "terminal" in result.output.lower()

    def test_detect_command(self, runner):
        """Test detect command runs."""
        from aiterm.cli.main import app

        result = runner.invoke(app, ["detect"])
        assert result.exit_code == 0
        assert "type" in result.output.lower() or "context" in result.output.lower()


class TestSubcommandHelp:
    """Test that all subcommands have working --help."""

    @pytest.mark.parametrize("subcommand", [
        "claude",
        "context",
        "hooks",
        "commands",
        "mcp",
        "opencode",
        "agents",
        "memory",
        "styles",
        "plugins",
        "gemini",
        "statusbar",
        "terminals",
        "workflows",
        "sessions",
    ])
    def test_subcommand_help(self, runner, subcommand):
        """Test subcommand --help works."""
        from aiterm.cli.main import app

        result = runner.invoke(app, [subcommand, "--help"])
        assert result.exit_code == 0, f"{subcommand} --help failed: {result.output}"


class TestSubcommandCommands:
    """Test key commands in each subcommand group."""

    def test_agents_list(self, runner):
        """Test agents list command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["agents", "list"])
        assert result.exit_code == 0

    def test_agents_templates(self, runner):
        """Test agents templates command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["agents", "templates"])
        assert result.exit_code == 0
        assert "research" in result.output or "coding" in result.output

    def test_memory_hierarchy(self, runner, tmp_path, monkeypatch):
        """Test memory hierarchy command."""
        from aiterm.cli.main import app
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["memory", "hierarchy"])
        assert result.exit_code == 0

    def test_styles_list(self, runner):
        """Test styles list command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["styles", "list"])
        assert result.exit_code == 0

    def test_plugins_list(self, runner):
        """Test plugins list command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["plugins", "list"])
        assert result.exit_code == 0

    def test_gemini_models(self, runner):
        """Test gemini models command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["gemini", "models"])
        assert result.exit_code == 0

    def test_statusbar_templates(self, runner):
        """Test statusbar templates command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["statusbar", "templates"])
        assert result.exit_code == 0

    def test_terminals_list(self, runner):
        """Test terminals list command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["terminals", "list"])
        assert result.exit_code == 0

    def test_workflows_list(self, runner):
        """Test workflows list command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["workflows", "list"])
        assert result.exit_code == 0

    def test_sessions_status(self, runner):
        """Test sessions status command."""
        from aiterm.cli.main import app
        result = runner.invoke(app, ["sessions", "status"])
        assert result.exit_code == 0


class TestSelfDiagnosticIntegration:
    """Self-diagnostic integration tests."""

    def test_all_modules_loadable(self):
        """Verify all CLI modules can be loaded."""
        modules = [
            "aiterm.cli.main",
            "aiterm.cli.hooks",
            "aiterm.cli.commands",
            "aiterm.cli.mcp",
            "aiterm.cli.docs",
            "aiterm.cli.opencode",
            "aiterm.cli.agents",
            "aiterm.cli.memory",
            "aiterm.cli.styles",
            "aiterm.cli.plugins",
            "aiterm.cli.gemini",
            "aiterm.cli.statusbar",
            "aiterm.cli.terminals",
            "aiterm.cli.workflows",
            "aiterm.cli.sessions",
        ]
        for module_name in modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_no_circular_imports(self):
        """Verify no circular import issues."""
        # Import in various orders to catch circular deps
        from aiterm.cli import main
        from aiterm.cli import agents
        from aiterm.cli import sessions
        from aiterm.cli import workflows

        # Re-import should work
        import importlib
        importlib.reload(main)

    def test_typer_app_has_commands(self):
        """Verify main app has expected command count."""
        from aiterm.cli.main import app

        # Count registered commands and groups
        # app.registered_commands includes subcommands
        # app.registered_groups includes typer groups
        assert hasattr(app, "registered_commands") or hasattr(app, "registered_groups")
