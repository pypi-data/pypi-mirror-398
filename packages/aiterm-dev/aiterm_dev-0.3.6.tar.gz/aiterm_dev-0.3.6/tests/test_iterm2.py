"""Tests for iTerm2 terminal integration."""

import os
from unittest.mock import patch

import pytest

from aiterm.context.detector import ContextInfo, ContextType
from aiterm.terminal import iterm2


class TestITerm2Detection:
    """Tests for iTerm2 detection."""

    def test_is_iterm2_true(self) -> None:
        """Should detect iTerm2 when TERM_PROGRAM is set."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            assert iterm2.is_iterm2() is True

    def test_is_iterm2_false(self) -> None:
        """Should return False when not in iTerm2."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "Apple_Terminal"}, clear=False):
            assert iterm2.is_iterm2() is False

    def test_is_iterm2_missing(self) -> None:
        """Should return False when TERM_PROGRAM is not set."""
        env = os.environ.copy()
        env.pop("TERM_PROGRAM", None)
        with patch.dict(os.environ, env, clear=True):
            assert iterm2.is_iterm2() is False


class TestProfileSwitching:
    """Tests for profile switching."""

    def setup_method(self) -> None:
        """Reset state before each test."""
        iterm2.reset_state()

    def test_switch_profile_not_iterm(self) -> None:
        """Should return False when not in iTerm2."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "other"}):
            result = iterm2.switch_profile("Test")
            assert result is False

    def test_switch_profile_same(self) -> None:
        """Should return False when switching to same profile."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            with patch("sys.stdout.write"):
                iterm2.switch_profile("Test")
                result = iterm2.switch_profile("Test")
                assert result is False

    def test_switch_profile_different(self) -> None:
        """Should return True when switching to different profile."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            with patch("sys.stdout.write") as mock_write:
                result = iterm2.switch_profile("NewProfile")
                assert result is True
                mock_write.assert_called()


class TestTitleSetting:
    """Tests for title setting."""

    def setup_method(self) -> None:
        """Reset state before each test."""
        iterm2.reset_state()

    def test_set_title_not_iterm(self) -> None:
        """Should return False when not in iTerm2."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "other"}):
            result = iterm2.set_title("Test")
            assert result is False

    def test_set_title_same(self) -> None:
        """Should return False when setting same title."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            with patch("sys.stdout.write"):
                iterm2.set_title("Test")
                result = iterm2.set_title("Test")
                assert result is False


class TestSessionManagement:
    """Tests for focus session management."""

    def setup_method(self) -> None:
        """Reset state before each test."""
        iterm2.reset_state()

    def test_session_end_no_session(self) -> None:
        """Should return False when no session is active."""
        result = iterm2.session_end()
        assert result is False


class TestApplyContext:
    """Tests for applying context to terminal."""

    def setup_method(self) -> None:
        """Reset state before each test."""
        iterm2.reset_state()

    def test_apply_context(self) -> None:
        """Should apply context settings."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            with patch("sys.stdout.write"):
                context = ContextInfo(
                    type=ContextType.PYTHON,
                    name="myproject",
                    icon="🐍",
                    profile="Python-Dev",
                    branch="main",
                    is_dirty=False,
                )
                iterm2.apply_context(context)
                state = iterm2.get_current_state()
                assert state.current_profile == "Python-Dev"
                assert "myproject" in state.current_title
