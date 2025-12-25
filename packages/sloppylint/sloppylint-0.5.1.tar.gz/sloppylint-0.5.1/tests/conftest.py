"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fixture_path() -> Path:
    """Return the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_python_file(tmp_path: Path):
    """Factory for creating temporary Python files."""

    def _create(content: str, name: str = "test.py") -> Path:
        file = tmp_path / name
        file.write_text(content)
        return file

    return _create
