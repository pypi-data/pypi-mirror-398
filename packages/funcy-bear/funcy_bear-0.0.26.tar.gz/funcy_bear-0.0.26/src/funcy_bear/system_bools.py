"""Functions to get system-related boolean values and environment information."""

from typing import TYPE_CHECKING

from lazy_bear import lazy

if TYPE_CHECKING:
    from os import getenv
    from pathlib import Path
    import sys
else:
    getenv = lazy("os", "getenv")
    Path = lazy("pathlib", "Path")
    sys = lazy("sys")


def get_python_version() -> str:
    """Get the current Python version as a string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def is_git_repo() -> bool:
    """Check if the current directory is inside a Git repository."""
    git_path: Path = get_cwd() / ".git"
    return git_path.exists() and git_path.is_dir()


def has_venv() -> bool:
    """Check if the current Python environment is a virtual environment."""
    return getenv("VIRTUAL_ENV") is not None


def venv_path() -> Path | None:
    """Get the path to the current virtual environment, if any."""
    venv: str | None = getenv("VIRTUAL_ENV")
    return None if venv is None else Path(venv)


def get_username() -> str | None:
    """Get the current user's username."""
    return getenv("USER") or getenv("USERNAME") or None


def get_terminal() -> str | None:
    """Get the terminal emulator."""
    return getenv("TERM_PROGRAM") or getenv("TERMINAL_EMULATOR") or getenv("COLORTERM") or getenv("TERM") or None


def get_editor() -> str | None:
    """Get the user's preferred text editor."""
    return getenv("EDITOR") or getenv("VISUAL") or None


def get_shell() -> str | None:
    """Get the user's preferred shell."""
    return getenv("SHELL") or getenv("COMSPEC") or None


def has_nix() -> bool:
    """Check if Nix is installed."""
    return Path("/nix").exists() and Path("/run/current-system").exists()


def has_homebrew() -> bool:
    """Check if Homebrew is installed."""
    return Path("/usr/local/bin/brew").exists() or Path("/opt/homebrew/bin/brew").exists()


def has_uv() -> bool:
    """Check if uv is installed."""
    user: str | None = get_username()
    if user:
        user_path = Path(f"/etc/profiles/per-user/{user}/bin/uv")
        if user_path.exists():
            return True
    return Path("/usr/local/bin/uv").exists() or Path("/opt/homebrew/bin/uv").exists() or Path("/usr/bin/uv").exists()


def get_home() -> Path:
    """Get the user's home directory."""
    return Path.home()


def get_cwd() -> Path:
    """Get the current working directory."""
    return Path.cwd()


__all__ = [
    "get_cwd",
    "get_editor",
    "get_home",
    "get_python_version",
    "get_shell",
    "get_terminal",
    "get_username",
    "has_homebrew",
    "has_nix",
    "has_uv",
]
