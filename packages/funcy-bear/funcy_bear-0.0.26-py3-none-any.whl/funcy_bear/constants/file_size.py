"""Constants for file size conversions."""

from typing import Final, Literal

KILOBYTES: Final = 1024
"""Number of bytes in a kilobyte."""
MEGABYTES: Final = KILOBYTES * 1024
"""Number of bytes in a megabyte."""
GIGABYTES: Final = MEGABYTES * 1024
"""Number of bytes in a gigabyte."""
TERABYTES: Final = GIGABYTES * 1024
"""Number of bytes in a terabyte."""

SizeChoice = Literal["bytes", "kilobytes", "megabytes", "gigabytes", "terabytes"]

FILE_SIZES: dict[str, int] = {
    "bytes": 1,
    "kilobytes": KILOBYTES,
    "megabytes": MEGABYTES,
    "gigabytes": GIGABYTES,
    "terabytes": TERABYTES,
}


class FileSize(int):
    """A converter for file sizes to bytes."""

    size: SizeChoice = "bytes"

    def __new__(cls, n: int) -> int:
        """Convert n in the specified size to bytes."""
        return super().__new__(cls, n * FILE_SIZES[cls.size])


class Bytes(FileSize):
    """Convert n in bytes to bytes (identity function)."""

    size = "bytes"


class Kilobytes(FileSize):
    """Convert n in kilobytes to bytes."""

    size = "kilobytes"


class Megabytes(FileSize):
    """Convert n in megabytes to bytes."""

    size = "megabytes"


class Gigabytes(FileSize):
    """Convert n in gigabytes to bytes."""

    size = "gigabytes"


class Terabytes(FileSize):
    """Convert n in terabytes to bytes."""

    size = "terabytes"


if __name__ == "__main__":
    # Example usage
    print(Kilobytes(5))
