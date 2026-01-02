"""iTerm2 terminal integration.

Provides profile switching, title setting, and user variables via escape sequences.
Ported from zsh/iterm2-integration.zsh.
"""

import base64
import os
import sys
from dataclasses import dataclass
from typing import Optional

from aiterm.context.detector import ContextInfo


@dataclass
class ITerm2State:
    """Tracks current iTerm2 state to avoid redundant updates."""

    current_profile: str = ""
    current_title: str = ""


# Global state (simulates zsh typeset -g)
_state = ITerm2State()


def is_iterm2() -> bool:
    """Check if running in iTerm2."""
    return os.environ.get("TERM_PROGRAM") == "iTerm.app"


def _write_escape(sequence: str) -> None:
    """Write an escape sequence to stdout."""
    sys.stdout.write(sequence)
    sys.stdout.flush()


def switch_profile(profile: str) -> bool:
    """Switch iTerm2 profile.

    Args:
        profile: Name of the iTerm2 profile to switch to.

    Returns:
        True if profile was switched, False if already set or not in iTerm2.
    """
    if not is_iterm2():
        return False

    if _state.current_profile == profile:
        return False

    _state.current_profile = profile
    _write_escape(f"\033]1337;SetProfile={profile}\007")
    return True


def set_title(title: str) -> bool:
    """Set the terminal window/tab title.

    Args:
        title: The title to set.

    Returns:
        True if title was set, False if already set or not in iTerm2.
    """
    if not is_iterm2():
        return False

    if _state.current_title == title:
        return False

    _state.current_title = title
    _write_escape(f"\033]2;{title}\007")  # OSC 2 - Window title
    return True


def set_user_var(name: str, value: str) -> None:
    """Set an iTerm2 user variable (for status bar).

    Args:
        name: Variable name.
        value: Variable value.
    """
    if not is_iterm2():
        return

    encoded = base64.b64encode(value.encode()).decode()
    _write_escape(f"\033]1337;SetUserVar={name}={encoded}\007")


def set_status_vars(icon: str, name: str, branch: str, profile: str) -> None:
    """Set all context variables for the iTerm2 status bar.

    Args:
        icon: Context icon emoji.
        name: Project/context name.
        branch: Git branch name.
        profile: iTerm2 profile name.
    """
    set_user_var("ctxIcon", icon)
    set_user_var("ctxName", name)
    set_user_var("ctxBranch", branch or "")
    set_user_var("ctxProfile", profile)


def apply_context(context: ContextInfo) -> None:
    """Apply a context to iTerm2 (profile, title, and status bar).

    Args:
        context: The context info to apply.
    """
    switch_profile(context.profile)
    set_title(context.title)
    set_status_vars(
        context.icon,
        context.name,
        context.branch or "",
        context.profile,
    )


# Session management (for focus mode)
_pre_session_profile: Optional[str] = None


def session_start(session_name: str = "Focus") -> None:
    """Start a focus session.

    Saves the current profile and switches to Focus mode.

    Args:
        session_name: Name to display in the title.
    """
    global _pre_session_profile

    _pre_session_profile = _state.current_profile
    switch_profile("Focus")
    set_title(f"🎯 {session_name}")


def session_end() -> bool:
    """End a focus session.

    Restores the previous profile.

    Returns:
        True if session was ended, False if no session was active.
    """
    global _pre_session_profile

    if _pre_session_profile is None:
        return False

    switch_profile(_pre_session_profile)
    _pre_session_profile = None
    return True


def get_current_state() -> ITerm2State:
    """Get the current iTerm2 state."""
    return _state


def reset_state() -> None:
    """Reset the state (useful for testing)."""
    global _state, _pre_session_profile
    _state = ITerm2State()
    _pre_session_profile = None
