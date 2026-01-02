"""Pytest configuration and fixtures for NeonLink tests."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from neonlink import ConfigBuilder, NeonLinkClient


@pytest.fixture
def config():
    """Create a test configuration."""
    return (
        ConfigBuilder()
        .with_service_name("test-service")
        .with_address("localhost:9090")
        .build()
    )


@pytest_asyncio.fixture
async def mock_client(config):
    """Create a mock NeonLink client."""
    client = NeonLinkClient(config)
    client._stub = AsyncMock()
    client._channel = MagicMock()
    client._connected = True
    return client
