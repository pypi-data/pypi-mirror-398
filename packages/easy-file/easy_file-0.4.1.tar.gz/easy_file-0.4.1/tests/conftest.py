"""Pytest configuration and shared fixtures."""

import pathlib
import tempfile
from collections.abc import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[pathlib.Path, None, None]:
    """Create a temporary directory for testing.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
def sample_json_data() -> dict[str, object]:
    """Sample JSON data for testing.

    Returns:
        Dictionary with sample data
    """
    return {
        "name": "test",
        "value": 42,
        "nested": {"key": "value"},
        "list": [1, 2, 3],
    }


@pytest.fixture
def sample_yaml_data() -> dict[str, object]:
    """Sample YAML data for testing.

    Returns:
        Dictionary with sample data
    """
    return {
        "name": "test",
        "value": 42,
        "nested": {"key": "value"},
        "list": [1, 2, 3],
    }
