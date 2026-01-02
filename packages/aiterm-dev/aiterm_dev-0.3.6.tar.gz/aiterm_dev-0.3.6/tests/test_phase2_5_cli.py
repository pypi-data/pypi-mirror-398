"""Tests for Phase 2.5 CLI modules: agents, memory, styles, plugins.

Self-diagnosing test suite with validation.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_claude_dir(tmp_path):
    """Create temporary .claude directory."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return claude_dir


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock home directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


# =============================================================================
# Agents CLI Tests (Phase 2.5.1)
# =============================================================================


class TestAgentsCLI:
    """Tests for agents CLI module."""

    def test_import_module(self):
        """Test module imports correctly."""
        from aiterm.cli import agents
        assert hasattr(agents, "app")
        assert hasattr(agents, "SubagentConfig")
        assert hasattr(agents, "SUBAGENT_TEMPLATES")

    def test_subagent_config_dataclass(self):
        """Test SubagentConfig dataclass."""
        from aiterm.cli.agents import SubagentConfig

        config = SubagentConfig(
            name="test-agent",
            description="Test agent",
            model="anthropic/claude-sonnet-4-5",
            tools=["Read", "Write"],
        )
        assert config.name == "test-agent"
        assert config.model == "anthropic/claude-sonnet-4-5"
        assert len(config.tools) == 2

    def test_subagent_config_validation(self):
        """Test SubagentConfig validation."""
        from aiterm.cli.agents import SubagentConfig

        # Valid config
        config = SubagentConfig(
            name="valid",
            model="anthropic/claude-sonnet-4-5",
        )
        valid, errors = config.is_valid()
        assert valid is True
        assert len(errors) == 0

        # Invalid - no name
        config = SubagentConfig(name="")
        valid, errors = config.is_valid()
        assert valid is False
        assert any("name" in e.lower() for e in errors)

    def test_subagent_templates_exist(self):
        """Test built-in templates are defined."""
        from aiterm.cli.agents import SUBAGENT_TEMPLATES

        expected = ["research", "coding", "review", "quick", "statistical"]
        for name in expected:
            assert name in SUBAGENT_TEMPLATES, f"Missing template: {name}"

    def test_subagent_to_dict(self):
        """Test SubagentConfig.to_dict()."""
        from aiterm.cli.agents import SubagentConfig

        config = SubagentConfig(
            name="test",
            description="Desc",
            model="anthropic/claude-sonnet-4-5",
            tools=["Read"],
        )
        d = config.to_dict()
        assert "description" in d
        assert "model" in d
        assert "tools" in d
        assert d["tools"] == ["Read"]

    def test_agents_list_empty(self, runner, mock_home):
        """Test agents list with no agents."""
        from aiterm.cli.agents import app

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No subagents" in result.output or "create" in result.output.lower()

    def test_agents_templates_command(self, runner):
        """Test agents templates command."""
        from aiterm.cli.agents import app

        result = runner.invoke(app, ["templates"])
        assert result.exit_code == 0
        assert "research" in result.output
        assert "coding" in result.output


# =============================================================================
# Memory CLI Tests (Phase 2.5.2)
# =============================================================================


class TestMemoryCLI:
    """Tests for memory CLI module."""

    def test_import_module(self):
        """Test module imports correctly."""
        from aiterm.cli import memory
        assert hasattr(memory, "app")
        assert hasattr(memory, "MemoryFile")
        assert hasattr(memory, "get_memory_hierarchy")

    def test_memory_file_dataclass(self):
        """Test MemoryFile dataclass."""
        from aiterm.cli.memory import MemoryFile

        mf = MemoryFile(
            path=Path("/test/CLAUDE.md"),
            level="project",
            exists=True,
            size=100,
            modified=datetime.now(),
            lines=10,
        )
        assert mf.level == "project"
        assert mf.exists is True

    def test_memory_file_age_days(self):
        """Test MemoryFile.age_days property."""
        from aiterm.cli.memory import MemoryFile
        from datetime import timedelta

        # Recent file
        mf = MemoryFile(
            path=Path("/test"),
            level="project",
            exists=True,
            modified=datetime.now() - timedelta(days=5),
        )
        assert mf.age_days == 5

        # No modified date
        mf2 = MemoryFile(path=Path("/test"), level="project", exists=False)
        assert mf2.age_days is None

    def test_get_memory_hierarchy(self, mock_home):
        """Test get_memory_hierarchy function."""
        from aiterm.cli.memory import get_memory_hierarchy

        # Create global CLAUDE.md
        claude_dir = mock_home / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Global")

        hierarchy = get_memory_hierarchy(mock_home)
        assert len(hierarchy) >= 1  # At least global
        assert any(m.level == "global" for m in hierarchy)


# =============================================================================
# Styles CLI Tests (Phase 2.5.3)
# =============================================================================


class TestStylesCLI:
    """Tests for styles CLI module."""

    def test_import_module(self):
        """Test module imports correctly."""
        from aiterm.cli import styles
        assert hasattr(styles, "app")
        assert hasattr(styles, "OutputStyle")
        assert hasattr(styles, "STYLE_PRESETS")

    def test_output_style_dataclass(self):
        """Test OutputStyle dataclass."""
        from aiterm.cli.styles import OutputStyle

        style = OutputStyle(
            name="test-style",
            description="Test",
            tone="casual",
            verbosity="concise",
        )
        assert style.name == "test-style"
        assert style.tone == "casual"

    def test_style_presets_exist(self):
        """Test built-in style presets are defined."""
        from aiterm.cli.styles import STYLE_PRESETS

        expected = ["default", "concise", "detailed", "academic", "teaching", "code-review"]
        for name in expected:
            assert name in STYLE_PRESETS, f"Missing preset: {name}"

    def test_style_to_dict(self):
        """Test OutputStyle.to_dict()."""
        from aiterm.cli.styles import OutputStyle

        style = OutputStyle(
            name="test",
            description="Test style",
            tone="formal",
            verbosity="detailed",
        )
        d = style.to_dict()
        assert d["name"] == "test"
        assert d["tone"] == "formal"

    def test_styles_list_command(self, runner):
        """Test styles list command."""
        from aiterm.cli.styles import app

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "default" in result.output or "concise" in result.output


# =============================================================================
# Plugins CLI Tests (Phase 2.5.4)
# =============================================================================


class TestPluginsCLI:
    """Tests for plugins CLI module."""

    def test_import_module(self):
        """Test module imports correctly."""
        from aiterm.cli import plugins
        assert hasattr(plugins, "app")
        assert hasattr(plugins, "Plugin")
        assert hasattr(plugins, "list_plugins")

    def test_plugin_dataclass(self):
        """Test Plugin dataclass."""
        from aiterm.cli.plugins import Plugin

        plugin = Plugin(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            commands=["cmd1", "cmd2"],
        )
        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"
        assert len(plugin.commands) == 2

    def test_plugin_component_count(self):
        """Test Plugin.component_count property."""
        from aiterm.cli.plugins import Plugin

        plugin = Plugin(
            name="test",
            commands=["cmd1"],
            agents=["agent1", "agent2"],
            skills=["skill1"],
        )
        assert plugin.component_count == 4

    def test_plugin_to_dict(self):
        """Test Plugin.to_dict()."""
        from aiterm.cli.plugins import Plugin

        plugin = Plugin(
            name="test",
            version="1.0.0",
            commands=["cmd1"],
        )
        d = plugin.to_dict()
        assert d["name"] == "test"
        assert d["version"] == "1.0.0"
        assert "commands" in d

    def test_plugins_list_empty(self, runner, mock_home):
        """Test plugins list with no plugins."""
        from aiterm.cli.plugins import app

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No plugins" in result.output or "create" in result.output.lower()


# =============================================================================
# Self-Diagnostic Tests
# =============================================================================


class TestSelfDiagnostics:
    """Self-diagnosing tests that validate test coverage and module integrity."""

    def test_all_phase25_modules_importable(self):
        """Verify all Phase 2.5 modules can be imported."""
        modules = ["agents", "memory", "styles", "plugins"]
        for name in modules:
            try:
                module = __import__(f"aiterm.cli.{name}", fromlist=[name])
                assert hasattr(module, "app"), f"{name}.app missing"
                assert hasattr(module, "console"), f"{name}.console missing"
            except ImportError as e:
                pytest.fail(f"Failed to import aiterm.cli.{name}: {e}")

    def test_all_cli_apps_are_typer(self):
        """Verify all CLI apps are Typer instances."""
        import typer
        from aiterm.cli import agents, memory, styles, plugins

        for module in [agents, memory, styles, plugins]:
            assert isinstance(module.app, typer.Typer), f"{module.__name__}.app is not Typer"

    def test_dataclasses_have_to_dict(self):
        """Verify all dataclasses have to_dict method."""
        from aiterm.cli.agents import SubagentConfig
        from aiterm.cli.memory import MemoryFile
        from aiterm.cli.styles import OutputStyle
        from aiterm.cli.plugins import Plugin

        for cls in [SubagentConfig, OutputStyle, Plugin]:
            assert hasattr(cls, "to_dict"), f"{cls.__name__} missing to_dict"

    def test_templates_are_complete(self):
        """Verify all templates have required fields."""
        from aiterm.cli.agents import SUBAGENT_TEMPLATES
        from aiterm.cli.styles import STYLE_PRESETS

        for name, template in SUBAGENT_TEMPLATES.items():
            assert "description" in template, f"agents template {name} missing description"
            assert "model" in template, f"agents template {name} missing model"

        for name, preset in STYLE_PRESETS.items():
            assert hasattr(preset, "name"), f"styles preset {name} missing name"
            assert hasattr(preset, "description"), f"styles preset {name} missing description"
