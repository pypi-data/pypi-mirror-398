"""
Pytest configuration for MCP Readiness Scanner tests.

This configuration file ensures pytest-asyncio is properly loaded
and configured for async test support.
"""

import pytest

# Explicitly configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"
