"""Tests for context detection."""

import tempfile
from pathlib import Path

import pytest

from aiterm.context.detector import (
    ContextInfo,
    ContextType,
    detect_context,
    detect_context_type,
)


class TestContextDetection:
    """Tests for detect_context function."""

    def test_default_context(self, tmp_path: Path) -> None:
        """Empty directory should return default context."""
        context = detect_context(tmp_path)
        assert context.type == ContextType.DEFAULT
        assert context.profile == "Default"
        assert context.icon == ""

    def test_python_project(self, tmp_path: Path) -> None:
        """Directory with pyproject.toml should be Python."""
        (tmp_path / "pyproject.toml").write_text('name = "myproject"\n')
        context = detect_context(tmp_path)
        assert context.type == ContextType.PYTHON
        assert context.profile == "Python-Dev"
        assert context.icon == "🐍"
        assert context.name == "myproject"

    def test_r_package(self, tmp_path: Path) -> None:
        """Directory with DESCRIPTION should be R package."""
        (tmp_path / "DESCRIPTION").write_text("Package: mypackage\nVersion: 1.0.0\n")
        context = detect_context(tmp_path)
        assert context.type == ContextType.R_PACKAGE
        assert context.profile == "R-Dev"
        assert context.icon == "📦"
        assert context.name == "mypackage"

    def test_node_project(self, tmp_path: Path) -> None:
        """Directory with package.json should be Node."""
        (tmp_path / "package.json").write_text('{"name": "my-node-app"}')
        context = detect_context(tmp_path)
        assert context.type == ContextType.NODE
        assert context.profile == "Node-Dev"
        assert context.icon == "📦"
        assert context.name == "my-node-app"

    def test_quarto_project(self, tmp_path: Path) -> None:
        """Directory with _quarto.yml should be Quarto."""
        (tmp_path / "_quarto.yml").write_text('title: "My Document"\n')
        context = detect_context(tmp_path)
        assert context.type == ContextType.QUARTO
        assert context.profile == "R-Dev"
        assert context.icon == "📊"
        assert context.name == "My Document"

    def test_emacs_project(self, tmp_path: Path) -> None:
        """Directory with Emacs files should be Emacs."""
        (tmp_path / "init.el").write_text(";; Emacs config")
        context = detect_context(tmp_path)
        assert context.type == ContextType.EMACS
        assert context.profile == "Emacs"
        assert context.icon == "⚡"

    def test_production_path(self, tmp_path: Path) -> None:
        """Path containing /production/ should be Production."""
        prod_path = tmp_path / "production" / "app"
        prod_path.mkdir(parents=True)
        context = detect_context(prod_path)
        assert context.type == ContextType.PRODUCTION
        assert context.profile == "Production"
        assert context.icon == "🚨"

    def test_ai_session_path(self, tmp_path: Path) -> None:
        """Path containing /claude-sessions/ should be AI Session."""
        session_path = tmp_path / "claude-sessions" / "task1"
        session_path.mkdir(parents=True)
        context = detect_context(session_path)
        assert context.type == ContextType.AI_SESSION
        assert context.profile == "AI-Session"
        assert context.icon == "🤖"


class TestContextInfo:
    """Tests for ContextInfo dataclass."""

    def test_title_with_icon(self) -> None:
        """Title should include icon if present."""
        info = ContextInfo(
            type=ContextType.PYTHON,
            name="myproject",
            icon="🐍",
            profile="Python-Dev",
        )
        assert info.title == "🐍 myproject"

    def test_title_without_icon(self) -> None:
        """Title should work without icon."""
        info = ContextInfo(
            type=ContextType.DEFAULT,
            name="myproject",
            icon="",
            profile="Default",
        )
        assert info.title == "myproject"

    def test_title_with_git(self) -> None:
        """Title should include git info."""
        info = ContextInfo(
            type=ContextType.PYTHON,
            name="myproject",
            icon="🐍",
            profile="Python-Dev",
            branch="main",
            is_dirty=False,
        )
        assert info.title == "🐍 myproject (main)"

    def test_title_with_dirty_git(self) -> None:
        """Title should show dirty indicator."""
        info = ContextInfo(
            type=ContextType.PYTHON,
            name="myproject",
            icon="🐍",
            profile="Python-Dev",
            branch="feature",
            is_dirty=True,
        )
        assert info.title == "🐍 myproject (feature)*"


class TestDetectContextType:
    """Tests for simplified detect_context_type function."""

    def test_returns_type_only(self, tmp_path: Path) -> None:
        """Should return just the ContextType enum."""
        (tmp_path / "pyproject.toml").write_text("")
        result = detect_context_type(tmp_path)
        assert result == ContextType.PYTHON
        assert isinstance(result, ContextType)
