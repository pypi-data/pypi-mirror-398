"""A set of helpful constants used throughout the Bear Dereth and beyond!"""

from pathlib import Path

from .exit_code import ExitCode
from .file_size import (
    FILE_SIZES,
    GIGABYTES,
    KILOBYTES,
    MEGABYTES,
    TERABYTES,
    Gigabytes,
    Kilobytes,
    Megabytes,
    Terabytes,
)
from .http_status import SERVER_ERROR, SERVER_OK, HTTPStatusCode
from .py_chars import (
    AS_STR,
    AUTO_STR,
    CLASS_STR,
    CLASS_VAR_STR,
    DEF_STR,
    ELIF_STR,
    EXCEPT_STR,
    FINALLY_STR,
    FOR_STR,
    IF_STR,
    IN_STR,
    LITERAL_STR,
    TRY_STR,
    TYPE_CHECKING_STR,
    WITH_STR,
)


def get_config_path() -> Path:
    """Get the path to the configuration directory based on the operating system."""
    import os  # noqa: PLC0415

    if "XDG_CONFIG_HOME" in os.environ:
        return Path(os.environ["XDG_CONFIG_HOME"])
    if "APPDATA" in os.environ:
        return Path(os.environ["APPDATA"])
    return Path.home() / ".config"


PATH_TO_DOWNLOADS: Path = Path.home() / "Downloads"
"""Path to the Downloads folder."""
PATH_TO_PICTURES: Path = Path.home() / "Pictures"
"""Path to the Pictures folder."""
PATH_TO_DOCUMENTS: Path = Path.home() / "Documents"
"""Path to the Documents folder."""
PATH_TO_HOME: Path = Path.home()
"""Path to the user's home directory."""
PATH_TO_CONFIG: Path = get_config_path()
"""Path to the configuration directory based on the operating system."""


VIDEO_EXTS: list[str] = [".mp4", ".mov", ".avi", ".mkv"]
"""Extensions for video files."""
IMAGE_EXTS: list[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
"""Extensions for image files."""
FILE_EXTS: list[str] = IMAGE_EXTS + VIDEO_EXTS
"""Extensions for both image and video files."""


__all__ = [
    "AS_STR",
    "AUTO_STR",
    "CLASS_STR",
    "CLASS_VAR_STR",
    "DEF_STR",
    "ELIF_STR",
    "EXCEPT_STR",
    "FILE_EXTS",
    "FILE_SIZES",
    "FINALLY_STR",
    "FOR_STR",
    "GIGABYTES",
    "IF_STR",
    "IMAGE_EXTS",
    "IN_STR",
    "KILOBYTES",
    "LITERAL_STR",
    "MEGABYTES",
    "PATH_TO_CONFIG",
    "PATH_TO_DOCUMENTS",
    "PATH_TO_DOWNLOADS",
    "PATH_TO_HOME",
    "PATH_TO_PICTURES",
    "SERVER_ERROR",
    "SERVER_OK",
    "TERABYTES",
    "TRY_STR",
    "TYPE_CHECKING_STR",
    "VIDEO_EXTS",
    "WITH_STR",
    "ExitCode",
    "Gigabytes",
    "HTTPStatusCode",
    "Kilobytes",
    "Megabytes",
    "Terabytes",
]
