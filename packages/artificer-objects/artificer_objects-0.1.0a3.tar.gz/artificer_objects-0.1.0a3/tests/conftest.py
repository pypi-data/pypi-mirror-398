"""Pytest fixtures for artificer-objects tests."""

import tempfile
from pathlib import Path

import pytest

from artificer.objects import Object


@pytest.fixture(autouse=True)
def reset_object_registry():
    """Reset the Object registry before each test."""
    Object._registry = {}
    Object._default_type = None
    Object._mcp_tools_registered = False
    yield
    Object._registry = {}
    Object._default_type = None
    Object._mcp_tools_registered = False


@pytest.fixture
def tmp_path_factory_custom():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
