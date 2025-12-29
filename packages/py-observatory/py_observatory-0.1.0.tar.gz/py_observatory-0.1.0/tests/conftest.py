"""Pytest configuration and fixtures."""

import pytest
from py_observatory import Observatory, ObservatoryConfig


@pytest.fixture
def observatory():
    """Create a test Observatory instance."""
    config = ObservatoryConfig(
        enabled=True,
        app_name="test",
    )
    return Observatory(config)


@pytest.fixture
def disabled_observatory():
    """Create a disabled Observatory instance."""
    config = ObservatoryConfig(enabled=False)
    return Observatory(config)
