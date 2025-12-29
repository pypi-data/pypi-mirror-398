"""Configuration for the pytest test suite."""

from os import environ
from pathlib import Path  # noqa: TC003

import pytest

from funcy_bear import METADATA

environ[f"{METADATA.env_variable}"] = "test"


@pytest.fixture
def temp_file_with_text(tmp_path: Path) -> Path:
    """Create a temporary file for testing."""
    file: Path = tmp_path / "test_file.txt"
    file.write_text("Hello, World!")
    return file


@pytest.fixture
def nonexistent_file(tmp_path: Path) -> Path:
    """Path to a file that doesn't exist."""
    return tmp_path / "nonexistent.txt"
