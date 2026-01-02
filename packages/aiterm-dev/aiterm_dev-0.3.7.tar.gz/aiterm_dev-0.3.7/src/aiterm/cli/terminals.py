"""Multi-terminal support CLI.

Phase 4.1: Unified interface for managing different terminal emulators.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    help="Manage terminal emulator integrations.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Terminal Types and Detection
# =============================================================================


class TerminalType(str, Enum):
    """Supported terminal emulators."""

    ITERM2 = "iterm2"
    TERMINAL = "terminal"  # macOS Terminal.app
    KITTY = "kitty"
    ALACRITTY = "alacritty"
    WEZTERM = "wezterm"
    HYPER = "hyper"
    WARP = "warp"
    GHOSTTY = "ghostty"
    UNKNOWN = "unknown"


@dataclass
class TerminalInfo:
    """Information about a terminal emulator."""

    type: TerminalType
    name: str
    version: str = ""
    config_path: Path | None = None
    is_active: bool = False
    features: list[str] = field(default_factory=list)


class TerminalBackend(ABC):
    """Abstract base class for terminal backends."""

    @property
    @abstractmethod
    def terminal_type(self) -> TerminalType:
        """Return the terminal type."""

    @property
    @abstractmethod
    def config_path(self) -> Path | None:
        """Return the config file path."""

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if terminal is installed."""

    @abstractmethod
    def get_version(self) -> str:
        """Get terminal version."""

    @abstractmethod
    def set_profile(self, profile: str) -> bool:
        """Set the active profile."""

    @abstractmethod
    def set_title(self, title: str) -> bool:
        """Set the terminal/tab title."""

    @abstractmethod
    def get_features(self) -> list[str]:
        """Return supported features."""


class ITerm2Backend(TerminalBackend):
    """iTerm2 terminal backend."""

    @property
    def terminal_type(self) -> TerminalType:
        return TerminalType.ITERM2

    @property
    def config_path(self) -> Path | None:
        return Path.home() / "Library" / "Preferences" / "com.googlecode.iterm2.plist"

    def is_installed(self) -> bool:
        return Path("/Applications/iTerm.app").exists()

    def get_version(self) -> str:
        try:
            result = subprocess.run(
                ["defaults", "read", "com.googlecode.iterm2", "CFBundleShortVersionString"],
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def set_profile(self, profile: str) -> bool:
        """Set iTerm2 profile using escape sequences."""
        # iTerm2 proprietary escape sequence
        print(f"\033]1337;SetProfile={profile}\a", end="", flush=True)
        return True

    def set_title(self, title: str) -> bool:
        """Set tab title."""
        print(f"\033]0;{title}\a", end="", flush=True)
        return True

    def get_features(self) -> list[str]:
        return [
            "profiles",
            "tab_title",
            "badge",
            "user_vars",
            "triggers",
            "shell_integration",
            "status_bar",
        ]


class KittyBackend(TerminalBackend):
    """Kitty terminal backend."""

    @property
    def terminal_type(self) -> TerminalType:
        return TerminalType.KITTY

    @property
    def config_path(self) -> Path | None:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "kitty" / "kitty.conf"

    def is_installed(self) -> bool:
        return shutil.which("kitty") is not None

    def get_version(self) -> str:
        try:
            result = subprocess.run(["kitty", "--version"], capture_output=True, text=True)
            return result.stdout.split()[1] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def set_profile(self, profile: str) -> bool:
        """Kitty uses themes/configs, not profiles."""
        # Kitty escape sequence to set colors
        return False  # Not directly supported like iTerm2

    def set_title(self, title: str) -> bool:
        print(f"\033]0;{title}\a", end="", flush=True)
        return True

    def get_features(self) -> list[str]:
        return ["tab_title", "themes", "kitten", "remote_control"]


class AlacrittyBackend(TerminalBackend):
    """Alacritty terminal backend."""

    @property
    def terminal_type(self) -> TerminalType:
        return TerminalType.ALACRITTY

    @property
    def config_path(self) -> Path | None:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "alacritty" / "alacritty.toml"

    def is_installed(self) -> bool:
        return shutil.which("alacritty") is not None

    def get_version(self) -> str:
        try:
            result = subprocess.run(["alacritty", "--version"], capture_output=True, text=True)
            return result.stdout.split()[1] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def set_profile(self, profile: str) -> bool:
        return False  # Alacritty doesn't have runtime profiles

    def set_title(self, title: str) -> bool:
        print(f"\033]0;{title}\a", end="", flush=True)
        return True

    def get_features(self) -> list[str]:
        return ["tab_title", "themes", "live_reload"]


class WezTermBackend(TerminalBackend):
    """WezTerm terminal backend."""

    @property
    def terminal_type(self) -> TerminalType:
        return TerminalType.WEZTERM

    @property
    def config_path(self) -> Path | None:
        return Path.home() / ".wezterm.lua"

    def is_installed(self) -> bool:
        return shutil.which("wezterm") is not None

    def get_version(self) -> str:
        try:
            result = subprocess.run(["wezterm", "--version"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def set_profile(self, profile: str) -> bool:
        return False  # Would require Lua config changes

    def set_title(self, title: str) -> bool:
        print(f"\033]0;{title}\a", end="", flush=True)
        return True

    def get_features(self) -> list[str]:
        return ["tab_title", "multiplexing", "lua_config", "workspaces"]


class GhosttyBackend(TerminalBackend):
    """Ghostty terminal backend."""

    @property
    def terminal_type(self) -> TerminalType:
        return TerminalType.GHOSTTY

    @property
    def config_path(self) -> Path | None:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "ghostty" / "config"

    def is_installed(self) -> bool:
        return shutil.which("ghostty") is not None

    def get_version(self) -> str:
        try:
            result = subprocess.run(["ghostty", "--version"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def set_profile(self, profile: str) -> bool:
        return False

    def set_title(self, title: str) -> bool:
        print(f"\033]0;{title}\a", end="", flush=True)
        return True

    def get_features(self) -> list[str]:
        return ["tab_title", "themes", "native_ui"]


# Registry of all backends
BACKENDS: dict[TerminalType, type[TerminalBackend]] = {
    TerminalType.ITERM2: ITerm2Backend,
    TerminalType.KITTY: KittyBackend,
    TerminalType.ALACRITTY: AlacrittyBackend,
    TerminalType.WEZTERM: WezTermBackend,
    TerminalType.GHOSTTY: GhosttyBackend,
}


def detect_current_terminal() -> TerminalType:
    """Detect the current terminal emulator."""
    term_program = os.environ.get("TERM_PROGRAM", "")
    term = os.environ.get("TERM", "")

    if term_program == "iTerm.app" or os.environ.get("ITERM_SESSION_ID"):
        return TerminalType.ITERM2
    if term_program == "Apple_Terminal":
        return TerminalType.TERMINAL
    if os.environ.get("KITTY_WINDOW_ID"):
        return TerminalType.KITTY
    if term_program == "Alacritty":
        return TerminalType.ALACRITTY
    if os.environ.get("WEZTERM_PANE"):
        return TerminalType.WEZTERM
    if term_program == "Hyper":
        return TerminalType.HYPER
    if os.environ.get("WARP_IS_LOCAL_SHELL"):
        return TerminalType.WARP
    if os.environ.get("GHOSTTY_RESOURCES_DIR"):
        return TerminalType.GHOSTTY

    return TerminalType.UNKNOWN


def get_backend(terminal_type: TerminalType) -> TerminalBackend | None:
    """Get backend for terminal type."""
    backend_class = BACKENDS.get(terminal_type)
    return backend_class() if backend_class else None


def get_all_terminal_info() -> list[TerminalInfo]:
    """Get info about all supported terminals."""
    current = detect_current_terminal()
    terminals = []

    for terminal_type, backend_class in BACKENDS.items():
        backend = backend_class()
        terminals.append(
            TerminalInfo(
                type=terminal_type,
                name=terminal_type.value,
                version=backend.get_version() if backend.is_installed() else "",
                config_path=backend.config_path,
                is_active=terminal_type == current,
                features=backend.get_features() if backend.is_installed() else [],
            )
        )

    return terminals


# =============================================================================
# CLI Commands
# =============================================================================


@app.command("detect")
def terminals_detect() -> None:
    """Detect the current terminal emulator."""
    current = detect_current_terminal()

    console.print("[bold cyan]Terminal Detection[/]\n")

    if current == TerminalType.UNKNOWN:
        console.print("[yellow]Could not detect terminal emulator.[/]")
        console.print("\nEnvironment hints:")
        console.print(f"  TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'not set')}")
        console.print(f"  TERM: {os.environ.get('TERM', 'not set')}")
    else:
        backend = get_backend(current)
        if backend:
            console.print(f"[green]✓[/] Detected: [bold]{current.value}[/]")
            version = backend.get_version()
            if version:
                console.print(f"  Version: {version}")
            if backend.config_path and backend.config_path.exists():
                console.print(f"  Config: {backend.config_path}")
            console.print(f"  Features: {', '.join(backend.get_features())}")


@app.command("list")
def terminals_list() -> None:
    """List all supported terminal emulators."""
    terminals = get_all_terminal_info()

    table = Table(title="Supported Terminals", border_style="cyan")
    table.add_column("Terminal", style="bold")
    table.add_column("Installed")
    table.add_column("Version")
    table.add_column("Active", justify="center")
    table.add_column("Features")

    for term in terminals:
        installed = "[green]✓[/]" if term.version else "[dim]✗[/]"
        active = "[green]●[/]" if term.is_active else ""
        features = ", ".join(term.features[:3]) + ("..." if len(term.features) > 3 else "")

        table.add_row(
            term.name,
            installed,
            term.version or "-",
            active,
            features or "-",
        )

    console.print(table)


@app.command("features")
def terminals_features(
    terminal: str = typer.Argument(None, help="Terminal to show features for."),
) -> None:
    """Show features for a terminal emulator."""
    if terminal:
        try:
            term_type = TerminalType(terminal.lower())
        except ValueError:
            console.print(f"[red]Unknown terminal: {terminal}[/]")
            raise typer.Exit(1)
        backends = [(term_type, BACKENDS.get(term_type))]
    else:
        backends = list(BACKENDS.items())

    for term_type, backend_class in backends:
        if not backend_class:
            continue
        backend = backend_class()
        features = backend.get_features()

        content = []
        for feature in features:
            content.append(f"  [green]✓[/] {feature}")

        if backend.config_path:
            content.append(f"\n  [bold]Config:[/] {backend.config_path}")

        console.print(Panel(
            "\n".join(content) if content else "[dim]No features detected[/]",
            title=f"{term_type.value} Features",
            border_style="cyan",
        ))


@app.command("config")
def terminals_config(
    terminal: str = typer.Argument(None, help="Terminal to show config for."),
) -> None:
    """Show configuration file location for a terminal."""
    if terminal:
        try:
            term_type = TerminalType(terminal.lower())
        except ValueError:
            console.print(f"[red]Unknown terminal: {terminal}[/]")
            raise typer.Exit(1)
    else:
        term_type = detect_current_terminal()

    backend = get_backend(term_type)
    if not backend:
        console.print(f"[yellow]No backend for: {term_type.value}[/]")
        return

    config_path = backend.config_path
    if config_path:
        if config_path.exists():
            console.print(f"[green]✓[/] Config: {config_path}")
            console.print(f"  Size: {config_path.stat().st_size} bytes")
        else:
            console.print(f"[yellow]⚠[/] Config path: {config_path}")
            console.print("  [dim]File does not exist yet[/]")
    else:
        console.print(f"[yellow]No known config path for {term_type.value}[/]")


@app.command("title")
def terminals_title(
    title: str = typer.Argument(..., help="Title to set."),
) -> None:
    """Set the terminal/tab title."""
    current = detect_current_terminal()
    backend = get_backend(current)

    if backend:
        if backend.set_title(title):
            console.print(f"[green]✓[/] Set title: {title}")
        else:
            console.print("[red]Failed to set title[/]")
    else:
        # Fallback to basic ANSI
        print(f"\033]0;{title}\a", end="", flush=True)
        console.print(f"[green]✓[/] Set title (generic): {title}")


@app.command("profile")
def terminals_profile(
    profile: str = typer.Argument(..., help="Profile name to switch to."),
) -> None:
    """Switch terminal profile (iTerm2 only)."""
    current = detect_current_terminal()
    backend = get_backend(current)

    if not backend:
        console.print(f"[yellow]No backend for: {current.value}[/]")
        return

    if "profiles" not in backend.get_features():
        console.print(f"[yellow]{current.value} does not support runtime profiles.[/]")
        return

    if backend.set_profile(profile):
        console.print(f"[green]✓[/] Switched to profile: {profile}")
    else:
        console.print("[red]Failed to switch profile[/]")


@app.command("compare")
def terminals_compare() -> None:
    """Compare features across terminal emulators."""
    all_features = set()
    terminals = {}

    for term_type, backend_class in BACKENDS.items():
        backend = backend_class()
        features = backend.get_features()
        terminals[term_type.value] = set(features)
        all_features.update(features)

    table = Table(title="Terminal Feature Comparison", border_style="cyan")
    table.add_column("Feature", style="bold")
    for term_name in terminals:
        table.add_column(term_name, justify="center")

    for feature in sorted(all_features):
        row = [feature]
        for term_name, term_features in terminals.items():
            row.append("[green]✓[/]" if feature in term_features else "[dim]✗[/]")
        table.add_row(*row)

    console.print(table)
