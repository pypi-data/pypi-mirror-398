"""
Unit tests for aiterm IDE integration module.

Tests for:
- IDE configuration data models
- IDE detection and status checking
- Settings management (load/save)
- Terminal profile generation
- Theme synchronization
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import pytest

from aiterm.cli.ide import (
    IDEConfig,
    IDE_CONFIGS,
    AI_DEV_EXTENSIONS,
    check_ide_installed,
    get_ide_config,
    load_ide_settings,
    save_ide_settings,
)


# ─── IDE Configuration Tests ─────────────────────────────────────────────────


class TestIDEConfig:
    """Tests for IDEConfig dataclass."""

    def test_ide_config_creation(self):
        """Test creating an IDEConfig instance."""
        config = IDEConfig(
            name="test-ide",
            display_name="Test IDE",
            config_path=Path("/test/path/settings.json"),
            supported_features=["terminal", "extensions"],
        )
        assert config.name == "test-ide"
        assert config.display_name == "Test IDE"
        assert config.config_path == Path("/test/path/settings.json")
        assert "terminal" in config.supported_features
        assert config.installed is False  # Default

    def test_ide_config_with_extensions(self):
        """Test IDEConfig with extensions dict."""
        config = IDEConfig(
            name="test",
            display_name="Test",
            config_path=Path("/test"),
            extensions={"ext1": {"version": "1.0"}},
        )
        assert "ext1" in config.extensions

    def test_ide_configs_dictionary_complete(self):
        """Test that IDE_CONFIGS has all expected IDEs."""
        expected_ides = ["vscode", "positron", "zed", "cursor", "windsurf"]
        for ide in expected_ides:
            assert ide in IDE_CONFIGS
            assert isinstance(IDE_CONFIGS[ide], IDEConfig)

    def test_vscode_config_correct(self):
        """Test VS Code configuration is correct."""
        vscode = IDE_CONFIGS["vscode"]
        assert vscode.name == "vscode"
        assert vscode.display_name == "Visual Studio Code"
        assert "terminal" in vscode.supported_features
        assert "extensions" in vscode.supported_features

    def test_positron_config_correct(self):
        """Test Positron configuration is correct."""
        positron = IDE_CONFIGS["positron"]
        assert positron.name == "positron"
        assert "r-support" in positron.supported_features

    def test_zed_config_correct(self):
        """Test Zed configuration is correct."""
        zed = IDE_CONFIGS["zed"]
        assert zed.name == "zed"
        assert "themes" in zed.supported_features


# ─── IDE Detection Tests ─────────────────────────────────────────────────────


class TestIDEDetection:
    """Tests for IDE detection functions."""

    @patch("shutil.which")
    def test_check_ide_installed_vscode_found(self, mock_which):
        """Test detecting VS Code when installed."""
        mock_which.return_value = "/usr/local/bin/code"
        assert check_ide_installed("vscode") is True
        mock_which.assert_called_once_with("code")

    @patch("shutil.which")
    def test_check_ide_installed_not_found(self, mock_which):
        """Test detecting IDE when not installed."""
        mock_which.return_value = None
        assert check_ide_installed("vscode") is False

    @patch("shutil.which")
    def test_check_ide_installed_unknown_ide(self, mock_which):
        """Test detecting unknown IDE."""
        assert check_ide_installed("unknown-ide") is False
        mock_which.assert_not_called()

    @patch("shutil.which")
    def test_get_ide_config_valid(self, mock_which):
        """Test getting IDE config for valid IDE."""
        mock_which.return_value = "/usr/local/bin/code"
        config = get_ide_config("vscode")
        assert config is not None
        assert config.name == "vscode"
        assert config.installed is True

    @patch("shutil.which")
    def test_get_ide_config_not_installed(self, mock_which):
        """Test getting IDE config when IDE not installed."""
        mock_which.return_value = None
        config = get_ide_config("vscode")
        assert config is not None
        assert config.installed is False

    def test_get_ide_config_invalid(self):
        """Test getting IDE config for invalid IDE."""
        config = get_ide_config("not-a-real-ide")
        assert config is None


# ─── Settings Management Tests ────────────────────────────────────────────────


class TestSettingsManagement:
    """Tests for IDE settings load/save functions."""

    def test_load_ide_settings_nonexistent(self):
        """Test loading settings from nonexistent file."""
        settings = load_ide_settings("vscode")
        # Should return empty dict if file doesn't exist
        assert isinstance(settings, dict)

    def test_load_ide_settings_invalid_ide(self):
        """Test loading settings for invalid IDE."""
        settings = load_ide_settings("not-real")
        assert settings == {}

    def test_save_ide_settings_invalid_ide(self):
        """Test saving settings for invalid IDE."""
        result = save_ide_settings("not-real", {"test": "value"})
        assert result is False

    def test_load_ide_settings_with_file(self):
        """Test loading settings from an existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock settings file
            settings_dir = Path(tmpdir) / ".vscode"
            settings_dir.mkdir()
            settings_file = settings_dir / "settings.json"
            test_settings = {"editor.fontSize": 14}
            settings_file.write_text(json.dumps(test_settings))

            # Patch the config path
            with patch.dict(IDE_CONFIGS, {
                "test-ide": IDEConfig(
                    name="test-ide",
                    display_name="Test",
                    config_path=settings_file,
                )
            }):
                settings = load_ide_settings("test-ide")
                assert settings == test_settings

    def test_load_ide_settings_invalid_json(self):
        """Test loading settings from invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "settings.json"
            settings_file.write_text("not valid json")

            with patch.dict(IDE_CONFIGS, {
                "test-ide": IDEConfig(
                    name="test-ide",
                    display_name="Test",
                    config_path=settings_file,
                )
            }):
                settings = load_ide_settings("test-ide")
                assert settings == {}

    def test_save_ide_settings_creates_directory(self):
        """Test that save_ide_settings creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "new_dir" / "settings.json"

            with patch.dict(IDE_CONFIGS, {
                "test-ide": IDEConfig(
                    name="test-ide",
                    display_name="Test",
                    config_path=settings_file,
                )
            }):
                result = save_ide_settings("test-ide", {"test": "value"})
                assert result is True
                assert settings_file.exists()
                saved = json.loads(settings_file.read_text())
                assert saved == {"test": "value"}


# ─── AI Extensions Tests ──────────────────────────────────────────────────────


class TestAIExtensions:
    """Tests for AI development extensions data."""

    def test_vscode_extensions_defined(self):
        """Test VS Code extensions are defined."""
        assert "vscode" in AI_DEV_EXTENSIONS
        extensions = AI_DEV_EXTENSIONS["vscode"]
        assert len(extensions) > 0
        # Check structure
        ext = extensions[0]
        assert "id" in ext
        assert "name" in ext
        assert "desc" in ext

    def test_positron_extensions_defined(self):
        """Test Positron extensions are defined."""
        assert "positron" in AI_DEV_EXTENSIONS

    def test_zed_extensions_defined(self):
        """Test Zed extensions are defined."""
        assert "zed" in AI_DEV_EXTENSIONS


# ─── Integration Tests ────────────────────────────────────────────────────────


class TestIDEIntegration:
    """Integration tests for IDE module."""

    def test_all_ides_have_valid_config_paths(self):
        """Test all IDE configs have valid path structure."""
        for name, config in IDE_CONFIGS.items():
            assert isinstance(config.config_path, Path)
            # Path should end with settings.json
            assert config.config_path.name == "settings.json"

    def test_all_ides_have_terminal_support(self):
        """Test all IDEs support terminal feature."""
        for name, config in IDE_CONFIGS.items():
            assert "terminal" in config.supported_features, f"{name} missing terminal support"

    def test_ide_module_imports_correctly(self):
        """Test that IDE module can be imported."""
        from aiterm.cli import ide
        assert hasattr(ide, "app")
        assert hasattr(ide, "IDE_CONFIGS")

    def test_ide_typer_app_has_commands(self):
        """Test that IDE Typer app has expected commands."""
        from aiterm.cli.ide import app

        # Get registered commands
        command_names = [cmd.name for cmd in app.registered_commands]

        expected = ["list", "status", "extensions", "configure", "terminal-profile", "sync-theme", "open", "compare"]
        for cmd in expected:
            assert cmd in command_names, f"Missing command: {cmd}"


# ─── CLI Command Tests ────────────────────────────────────────────────────────


class TestIDECLICommands:
    """Tests for IDE CLI commands."""

    def test_ide_list_command_exists(self):
        """Test that 'ide list' command exists."""
        from aiterm.cli.ide import ide_list
        assert callable(ide_list)

    def test_ide_status_command_exists(self):
        """Test that 'ide status' command exists."""
        from aiterm.cli.ide import ide_status
        assert callable(ide_status)

    def test_ide_configure_command_exists(self):
        """Test that 'ide configure' command exists."""
        from aiterm.cli.ide import ide_configure
        assert callable(ide_configure)

    def test_ide_open_command_exists(self):
        """Test that 'ide open' command exists."""
        from aiterm.cli.ide import ide_open
        assert callable(ide_open)


# ─── Edge Cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_settings_save(self):
        """Test saving empty settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "settings.json"

            with patch.dict(IDE_CONFIGS, {
                "test-ide": IDEConfig(
                    name="test-ide",
                    display_name="Test",
                    config_path=settings_file,
                )
            }):
                result = save_ide_settings("test-ide", {})
                assert result is True

    def test_unicode_in_settings(self):
        """Test settings with unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "settings.json"

            with patch.dict(IDE_CONFIGS, {
                "test-ide": IDEConfig(
                    name="test-ide",
                    display_name="Test",
                    config_path=settings_file,
                )
            }):
                settings = {"comment": "Unicode test: \u2713 \u2717"}
                save_ide_settings("test-ide", settings)
                loaded = load_ide_settings("test-ide")
                assert loaded["comment"] == "Unicode test: \u2713 \u2717"

    def test_nested_settings(self):
        """Test deeply nested settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "settings.json"

            with patch.dict(IDE_CONFIGS, {
                "test-ide": IDEConfig(
                    name="test-ide",
                    display_name="Test",
                    config_path=settings_file,
                )
            }):
                settings = {
                    "level1": {
                        "level2": {
                            "level3": {"value": 42}
                        }
                    }
                }
                save_ide_settings("test-ide", settings)
                loaded = load_ide_settings("test-ide")
                assert loaded["level1"]["level2"]["level3"]["value"] == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
