"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_path() -> Path:
    """Provide path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"
