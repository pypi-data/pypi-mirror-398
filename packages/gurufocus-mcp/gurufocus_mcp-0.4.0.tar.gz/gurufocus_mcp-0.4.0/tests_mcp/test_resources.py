"""Tests for MCP resources."""

import pytest
from fastmcp.client import Client

from gurufocus_mcp.config import MCPServerSettings
from gurufocus_mcp.server import create_server


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch):
    """Create a test server."""
    monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")
    settings = MCPServerSettings(api_token="test-token")
    return create_server(settings)


@pytest.fixture
async def client(server):
    """Create a client connected to the test server."""
    async with Client(server) as client:
        yield client


class TestResourceRegistration:
    """Tests for resource registration."""

    def test_no_static_resources(self, server) -> None:
        """Test that no static resources are registered."""
        resource_count = len(server._resource_manager._resources)
        assert resource_count == 0

    def test_no_resource_templates(self, server) -> None:
        """Test that no resource templates are registered."""
        template_count = len(server._resource_manager._templates)
        assert template_count == 0


class TestResourceDiscovery:
    """Tests for resource discovery via MCP protocol."""

    @pytest.mark.asyncio
    async def test_list_resources_returns_empty(self, client: Client) -> None:
        """Test that list_resources returns no resources."""
        resources = await client.list_resources()
        assert len(resources) == 0

    @pytest.mark.asyncio
    async def test_no_resource_templates_via_protocol(self, client: Client) -> None:
        """Test that no resource templates are returned via protocol."""
        templates = await client.list_resource_templates()
        assert len(templates) == 0


class TestResourceErrorHandling:
    """Tests for resource error handling."""

    @pytest.mark.asyncio
    async def test_invalid_resource_uri_raises_error(self, client: Client) -> None:
        """Test that invalid resource URI raises an error."""
        with pytest.raises(Exception, match="Unknown resource"):
            await client.read_resource("gurufocus://invalid/resource")
