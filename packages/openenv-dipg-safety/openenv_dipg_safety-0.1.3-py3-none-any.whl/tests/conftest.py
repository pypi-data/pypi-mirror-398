# tests/conftest.py
"""
Pytest configuration for the test suite.
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Force anyio to only use asyncio backend."""
    return "asyncio"
