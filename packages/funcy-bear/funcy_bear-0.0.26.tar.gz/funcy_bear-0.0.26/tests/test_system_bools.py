"""Tests for system_bools module with mocking for system independence."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from unittest.mock import MagicMock, patch

from funcy_bear import system_bools


class TestPythonVersion:
    """Test get_python_version function."""

    def test_get_python_version_format(self) -> None:
        """Test Python version returns in correct format."""
        version: str = system_bools.get_python_version()
        assert isinstance(version, str)
        parts: list[str] = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


class TestGitRepo:
    """Test is_git_repo function."""

    @patch("funcy_bear.system_bools.get_cwd")
    def test_is_git_repo_true(self, mock_cwd: MagicMock, tmp_path: Path) -> None:
        """Test is_git_repo returns True when .git exists."""
        git_dir: Path = tmp_path / ".git"
        git_dir.mkdir()
        mock_cwd.return_value = tmp_path

        assert system_bools.is_git_repo() is True

    @patch("funcy_bear.system_bools.get_cwd")
    def test_is_git_repo_false(self, mock_cwd, tmp_path: Path) -> None:
        """Test is_git_repo returns False when .git doesn't exist."""
        mock_cwd.return_value = tmp_path

        assert system_bools.is_git_repo() is False

    @patch("funcy_bear.system_bools.get_cwd")
    def test_is_git_repo_file_not_dir(self, mock_cwd, tmp_path: Path) -> None:
        """Test is_git_repo returns False if .git is a file."""
        git_file = tmp_path / ".git"
        git_file.touch()
        mock_cwd.return_value = tmp_path

        assert system_bools.is_git_repo() is False


class TestVirtualEnv:
    """Test virtual environment functions."""

    @patch("funcy_bear.system_bools.getenv")
    def test_has_venv_true(self, mock_getenv) -> None:
        """Test has_venv returns True when VIRTUAL_ENV is set."""
        mock_getenv.return_value = "/path/to/venv"

        assert system_bools.has_venv() is True
        mock_getenv.assert_called_with("VIRTUAL_ENV")

    @patch("funcy_bear.system_bools.getenv")
    def test_has_venv_false(self, mock_getenv) -> None:
        """Test has_venv returns False when VIRTUAL_ENV is not set."""
        mock_getenv.return_value = None

        assert system_bools.has_venv() is False

    @patch("funcy_bear.system_bools.getenv")
    def test_venv_path_exists(self, mock_getenv) -> None:
        """Test venv_path returns Path when VIRTUAL_ENV is set."""
        mock_getenv.return_value = "/path/to/venv"

        result: Path | None = system_bools.venv_path()
        assert result is not None
        assert result == Path("/path/to/venv")

    @patch("funcy_bear.system_bools.getenv")
    def test_venv_path_none(self, mock_getenv) -> None:
        """Test venv_path returns None when VIRTUAL_ENV is not set."""
        mock_getenv.return_value = None

        assert system_bools.venv_path() is None


class TestUsername:
    """Test get_username function."""

    @patch("funcy_bear.system_bools.getenv")
    def test_get_username_user(self, mock_getenv) -> None:
        """Test get_username returns USER env var."""
        mock_getenv.side_effect = lambda x: "bear" if x == "USER" else None

        assert system_bools.get_username() == "bear"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_username_username(self, mock_getenv) -> None:
        """Test get_username falls back to USERNAME env var."""
        mock_getenv.side_effect = lambda x: "bear" if x == "USERNAME" else None

        assert system_bools.get_username() == "bear"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_username_none(self, mock_getenv) -> None:
        """Test get_username returns None when no username found."""
        mock_getenv.return_value = None

        assert system_bools.get_username() is None


class TestTerminal:
    """Test get_terminal function."""

    @patch("funcy_bear.system_bools.getenv")
    def test_get_terminal_term_program(self, mock_getenv) -> None:
        """Test get_terminal returns TERM_PROGRAM."""
        mock_getenv.side_effect = lambda x: "iTerm.app" if x == "TERM_PROGRAM" else None

        assert system_bools.get_terminal() == "iTerm.app"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_terminal_fallback(self, mock_getenv) -> None:
        """Test get_terminal falls back through options."""

        def side_effect(x) -> None | Literal["xterm-256color"]:
            if x == "TERM":
                return "xterm-256color"
            return None

        mock_getenv.side_effect = side_effect

        assert system_bools.get_terminal() == "xterm-256color"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_terminal_none(self, mock_getenv) -> None:
        """Test get_terminal returns None when nothing found."""
        mock_getenv.return_value = None

        assert system_bools.get_terminal() is None


class TestEditor:
    """Test get_editor function."""

    @patch("funcy_bear.system_bools.getenv")
    def test_get_editor_editor(self, mock_getenv) -> None:
        """Test get_editor returns EDITOR env var."""
        mock_getenv.side_effect = lambda x: "vim" if x == "EDITOR" else None

        assert system_bools.get_editor() == "vim"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_editor_visual(self, mock_getenv) -> None:
        """Test get_editor falls back to VISUAL."""
        mock_getenv.side_effect = lambda x: "emacs" if x == "VISUAL" else None

        assert system_bools.get_editor() == "emacs"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_editor_none(self, mock_getenv) -> None:
        """Test get_editor returns None when nothing found."""
        mock_getenv.return_value = None

        assert system_bools.get_editor() is None


class TestShell:
    """Test get_shell function."""

    @patch("funcy_bear.system_bools.getenv")
    def test_get_shell_shell(self, mock_getenv) -> None:
        """Test get_shell returns SHELL env var."""
        mock_getenv.side_effect = lambda x: "/bin/zsh" if x == "SHELL" else None

        assert system_bools.get_shell() == "/bin/zsh"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_shell_comspec(self, mock_getenv) -> None:
        """Test get_shell falls back to COMSPEC."""
        mock_getenv.side_effect = lambda x: "cmd.exe" if x == "COMSPEC" else None

        assert system_bools.get_shell() == "cmd.exe"

    @patch("funcy_bear.system_bools.getenv")
    def test_get_shell_none(self, mock_getenv) -> None:
        """Test get_shell returns None when nothing found."""
        mock_getenv.return_value = None

        assert system_bools.get_shell() is None


class TestNix:
    """Test has_nix function."""

    @patch("funcy_bear.system_bools.Path")
    def test_has_nix_true(self, mock_path) -> None:
        """Test has_nix returns True when both paths exist."""
        mock_nix = mock_path.return_value
        mock_nix.exists.return_value = True

        assert system_bools.has_nix() is True

    @patch("funcy_bear.system_bools.Path")
    def test_has_nix_false(self, mock_path) -> None:
        """Test has_nix returns False when paths don't exist."""
        mock_nix = mock_path.return_value
        mock_nix.exists.return_value = False

        assert system_bools.has_nix() is False


class TestHomebrew:
    """Test has_homebrew function."""

    @patch("funcy_bear.system_bools.Path")
    def test_has_homebrew_local(self, mock_path) -> None:
        """Test has_homebrew finds in /usr/local."""
        mock_path_obj = mock_path.return_value
        mock_path_obj.exists.side_effect = [True, False]

        assert system_bools.has_homebrew() is True

    @patch("funcy_bear.system_bools.Path")
    def test_has_homebrew_opt(self, mock_path) -> None:
        """Test has_homebrew finds in /opt/homebrew."""
        mock_path_obj = mock_path.return_value
        mock_path_obj.exists.side_effect = [False, True]

        assert system_bools.has_homebrew() is True

    @patch("funcy_bear.system_bools.Path")
    def test_has_homebrew_false(self, mock_path) -> None:
        """Test has_homebrew returns False when not found."""
        mock_path_obj = mock_path.return_value
        mock_path_obj.exists.return_value = False

        assert system_bools.has_homebrew() is False


class TestUV:
    """Test has_uv function."""

    @patch("funcy_bear.system_bools.get_username")
    @patch("funcy_bear.system_bools.Path")
    def test_has_uv_user_path(self, mock_path, mock_username) -> None:
        """Test has_uv finds in user-specific path."""
        mock_username.return_value = "bear"
        mock_path_obj = mock_path.return_value
        mock_path_obj.exists.return_value = True

        assert system_bools.has_uv() is True

    @patch("funcy_bear.system_bools.get_username")
    @patch("funcy_bear.system_bools.Path")
    def test_has_uv_common_paths(self, mock_path, mock_username) -> None:
        """Test has_uv finds in common paths."""
        mock_username.return_value = "bear"
        mock_path_obj = mock_path.return_value
        mock_path_obj.exists.side_effect = [False, True]

        assert system_bools.has_uv() is True

    @patch("funcy_bear.system_bools.get_username")
    @patch("funcy_bear.system_bools.Path")
    def test_has_uv_false(self, mock_path, mock_username) -> None:
        """Test has_uv returns False when not found."""
        mock_username.return_value = "bear"
        mock_path_obj = mock_path.return_value
        mock_path_obj.exists.return_value = False

        assert system_bools.has_uv() is False


class TestPaths:
    """Test path-related functions."""

    def test_get_home(self) -> None:
        """Test get_home returns a Path."""
        home = system_bools.get_home()
        assert isinstance(home, Path)
        assert home.exists()

    def test_get_cwd(self) -> None:
        """Test get_current_dir returns a Path."""
        cwd: Path = system_bools.get_cwd()
        assert isinstance(cwd, Path)
        assert cwd.exists()
