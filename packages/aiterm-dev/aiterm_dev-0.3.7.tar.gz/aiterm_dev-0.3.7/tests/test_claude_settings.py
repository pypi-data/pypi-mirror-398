"""Tests for Claude settings management."""

import json
from pathlib import Path

import pytest

from aiterm.claude.settings import (
    ClaudeSettings,
    PRESETS,
    add_preset_to_settings,
    get_preset,
    list_presets,
    load_settings,
    save_settings,
)


class TestClaudeSettings:
    """Tests for ClaudeSettings dataclass."""

    def test_allow_list(self) -> None:
        """Should return allow list from permissions."""
        settings = ClaudeSettings(
            path=Path("/test"),
            permissions={"allow": ["Bash(ls:*)", "Bash(cat:*)"]},
        )
        assert settings.allow_list == ["Bash(ls:*)", "Bash(cat:*)"]

    def test_deny_list(self) -> None:
        """Should return deny list from permissions."""
        settings = ClaudeSettings(
            path=Path("/test"),
            permissions={"deny": ["Bash(rm:*)"]},
        )
        assert settings.deny_list == ["Bash(rm:*)"]

    def test_empty_lists(self) -> None:
        """Should return empty lists when not configured."""
        settings = ClaudeSettings(path=Path("/test"))
        assert settings.allow_list == []
        assert settings.deny_list == []


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_valid_settings(self, tmp_path: Path) -> None:
        """Should load valid settings file."""
        settings_file = tmp_path / ".claude" / "settings.local.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps({
            "permissions": {"allow": ["Bash(ls:*)"]}
        }))

        settings = load_settings(settings_file)
        assert settings is not None
        assert settings.allow_list == ["Bash(ls:*)"]

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """Should return None for missing file."""
        settings = load_settings(tmp_path / "nonexistent.json")
        assert settings is None

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Should return None for invalid JSON."""
        settings_file = tmp_path / "invalid.json"
        settings_file.write_text("not json")

        settings = load_settings(settings_file)
        assert settings is None


class TestSaveSettings:
    """Tests for save_settings function."""

    def test_save_settings(self, tmp_path: Path) -> None:
        """Should save settings to file."""
        settings_file = tmp_path / "settings.json"
        settings = ClaudeSettings(
            path=settings_file,
            permissions={"allow": ["Bash(ls:*)"]},
            raw={"permissions": {"allow": ["Bash(ls:*)"]}},
        )

        assert save_settings(settings) is True
        assert settings_file.exists()

        # Verify content
        data = json.loads(settings_file.read_text())
        assert data["permissions"]["allow"] == ["Bash(ls:*)"]


class TestPresets:
    """Tests for preset management."""

    def test_list_presets(self) -> None:
        """Should return all presets."""
        presets = list_presets()
        assert "safe-reads" in presets
        assert "git-ops" in presets
        assert "python-dev" in presets

    def test_get_preset(self) -> None:
        """Should return preset by name."""
        preset = get_preset("safe-reads")
        assert preset is not None
        assert "description" in preset
        assert "permissions" in preset

    def test_get_unknown_preset(self) -> None:
        """Should return None for unknown preset."""
        assert get_preset("unknown-preset") is None

    def test_all_presets_have_required_fields(self) -> None:
        """All presets should have description and permissions."""
        for name, preset in PRESETS.items():
            assert "description" in preset, f"{name} missing description"
            assert "permissions" in preset, f"{name} missing permissions"
            assert isinstance(preset["permissions"], list), f"{name} permissions not list"


class TestAddPreset:
    """Tests for add_preset_to_settings function."""

    def test_add_preset(self) -> None:
        """Should add preset permissions."""
        settings = ClaudeSettings(
            path=Path("/test"),
            permissions={"allow": []},
        )

        success, added = add_preset_to_settings(settings, "minimal")
        assert success is True
        assert len(added) == 3
        assert "Bash(ls:*)" in added

    def test_add_preset_no_duplicates(self) -> None:
        """Should not add duplicate permissions."""
        settings = ClaudeSettings(
            path=Path("/test"),
            permissions={"allow": ["Bash(ls:*)"]},
        )

        success, added = add_preset_to_settings(settings, "minimal")
        assert success is True
        assert "Bash(ls:*)" not in added  # Already present

    def test_add_unknown_preset(self) -> None:
        """Should return False for unknown preset."""
        settings = ClaudeSettings(path=Path("/test"))
        success, added = add_preset_to_settings(settings, "unknown")
        assert success is False
        assert added == []
