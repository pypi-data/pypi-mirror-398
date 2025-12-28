import pytest
from fastmcp.client import Client

from gworkspace import mcp


@pytest.fixture
async def client():
    """Provide an MCP client connected to the server for testing."""
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client
