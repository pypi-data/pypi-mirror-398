from __future__ import annotations

from enum import IntEnum
from typing import Literal, NamedTuple

try:
    from ._version import __commit_id__, __version__, __version_tuple__
except (ImportError, ModuleNotFoundError):
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)
    __commit_id__ = "unknown"

PACKAGE_NAME: Literal["funcy-bear"] = "funcy-bear"
PROJECT: Literal["funcy_bear"] = "funcy_bear"
PROJECT_UPPER: Literal["FUNCY_BEAR"] = "FUNCY_BEAR"
ENV_VARIABLE: Literal["FUNCY_BEAR_ENV"] = "FUNCY_BEAR_ENV"
type BumpType = Literal["major", "minor", "patch"]


class VersionParts(IntEnum):  # pragma: no cover
    """Enumeration for version parts."""

    MAJOR = 0
    MINOR = 1
    PATCH = 2

    @classmethod
    def choices(cls) -> list[str]:
        """Return a list of valid version parts."""
        return [part.name.lower() for part in cls]

    @classmethod
    def parts(cls) -> int:
        """Return the total number of version parts."""
        return len(cls.choices())


class Version(NamedTuple):  # pragma: no cover
    """Model to represent a version string."""

    major: int
    minor: int
    patch: int

    def new_version(self, bump_type: str) -> Version:
        """Return a new version string based on the bump type."""
        bump_part: VersionParts = VersionParts[bump_type.upper()]
        match bump_part:
            case VersionParts.MAJOR:
                return Version(major=self.major + 1, minor=0, patch=0)
            case VersionParts.MINOR:
                return Version(major=self.major, minor=self.minor + 1, patch=0)
            case VersionParts.PATCH:
                return Version(major=self.major, minor=self.minor, patch=self.patch + 1)
            case _:
                raise ValueError(f"Invalid bump type: {bump_type}")

    def __repr__(self) -> str:
        """Return a string representation of the Version instance."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        """Return a string representation of the Version instance."""
        return self.__repr__()


VALID_BUMP_TYPES: list[str] = VersionParts.choices()  # pragma: no cover
ALL_PARTS: int = VersionParts.parts()  # pragma: no cover


class _Package(NamedTuple):
    """Dataclass to store package information."""

    name: str
    """Package name."""
    version: str = "0.0.0"
    """Package version."""
    description: str = "No description available."
    """Package description."""

    def __str__(self) -> str:
        """String representation of the package information."""
        return f"{self.name} v{self.version}: {self.description}"


def _get_version(dist: str) -> str:
    """Get version of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A version number.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(dist)
    except PackageNotFoundError:
        return "0.0.0"


def _get_description(dist: str) -> str:
    """Get description of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A description string.
    """
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        return distribution(dist).metadata.get("summary", "No description available.")
    except PackageNotFoundError:
        return "No description available."


class _ProjectMetadata(NamedTuple):
    """Dataclass to store the current project metadata."""

    version: str = __version__ if __version__ != "0.0.0" else _get_version(PACKAGE_NAME)
    version_tuple: Version = Version(*__version_tuple__)
    commit_id: str = __commit_id__
    commands: str = f"{PROJECT}._internal._cmds"

    @property
    def cmds(self) -> str:
        """Get the commands module path."""
        return self.commands

    @property
    def full_version(self) -> str:
        """Get the full version string."""
        return f"{self.name} v{self.version}"

    @property
    def description(self) -> str:
        """Get the project description from the distribution metadata."""
        return _get_description(self.name)

    @property
    def name(self) -> Literal["funcy-bear"]:
        """Get the package distribution name."""
        return PACKAGE_NAME

    @property
    def name_upper(self) -> Literal["FUNCY_BEAR"]:
        """Get the project name in uppercase with underscores."""
        return PROJECT_UPPER

    @property
    def project_name(self) -> Literal["funcy_bear"]:
        """Get the project name."""
        return PROJECT

    @property
    def env_variable(self) -> Literal["FUNCY_BEAR_ENV"]:
        """Get the environment variable name for the project.

        Used to check if the project is running in a specific environment.
        """
        return ENV_VARIABLE

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"


METADATA = _ProjectMetadata()


__all__ = ["METADATA", "VALID_BUMP_TYPES", "BumpType", "Version", "_Package", "_get_description", "_get_version"]

# ruff: noqa: PLC0415
