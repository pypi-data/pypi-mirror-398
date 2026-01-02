"""Integration tests for GuruFocus MCP server.

These tests verify end-to-end functionality including:
- MCP protocol compliance
- Resource discovery
- Tool discovery and invocation
- Response format validation
"""

import pytest
from fastmcp.client import Client

from gurufocus_mcp.config import MCPServerSettings
from gurufocus_mcp.server import create_server


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch):
    """Create a test server instance."""
    monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")
    settings = MCPServerSettings(api_token="test-token")
    return create_server(settings)


@pytest.fixture
async def client(server):
    """Create a client connected to the test server."""
    async with Client(server) as client:
        yield client


class TestMCPProtocolCompliance:
    """Tests for MCP protocol compliance."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, client: Client) -> None:
        """Test that server initializes correctly via MCP protocol."""
        assert client.is_connected()

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_stock_tools(self, client: Client) -> None:
        """Test that list_tools returns all stock tools."""
        tools = await client.list_tools()

        assert len(tools) == 21
        tool_names = [t.name for t in tools]
        assert "get_stock_summary" in tool_names
        assert "get_stock_quote" in tool_names
        assert "get_stock_dividend" in tool_names
        assert "get_stock_current_dividend" in tool_names
        assert "get_stock_financials" in tool_names
        assert "get_stock_keyratios" in tool_names
        assert "get_qgarp_analysis" in tool_names
        assert "get_stock_gurus" in tool_names
        assert "get_stock_executives" in tool_names
        assert "get_stock_trades_history" in tool_names
        assert "get_stock_price_ohlc" in tool_names
        assert "get_stock_volume" in tool_names
        assert "get_stock_unadjusted_price" in tool_names

    @pytest.mark.asyncio
    async def test_no_resource_templates(self, client: Client) -> None:
        """Test that no resource templates are registered (summary is now a tool)."""
        templates = await client.list_resource_templates()

        assert len(templates) == 0

    @pytest.mark.asyncio
    async def test_list_resources_returns_empty(self, client: Client) -> None:
        """Test that list_resources returns no resources."""
        resources = await client.list_resources()
        assert len(resources) == 0

    @pytest.mark.asyncio
    async def test_prompts_registered(self, client: Client) -> None:
        """Test that prompts are registered."""
        prompts = await client.list_prompts()
        assert len(prompts) == 2
        prompt_names = [p.name for p in prompts]
        assert "qgarp_scorecard" in prompt_names
        assert "execution_risk_analysis" in prompt_names


class TestToolFormats:
    """Tests for tool format validation."""

    @pytest.mark.asyncio
    async def test_get_stock_summary_tool_has_description(self, client: Client) -> None:
        """Test that get_stock_summary tool has a description."""
        tools = await client.list_tools()

        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        assert summary_tool.description is not None
        assert "summary" in summary_tool.description.lower()

    @pytest.mark.asyncio
    async def test_get_stock_summary_tool_has_symbol_parameter(self, client: Client) -> None:
        """Test that get_stock_summary tool has symbol parameter."""
        tools = await client.list_tools()

        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        assert summary_tool.inputSchema is not None
        assert "symbol" in summary_tool.inputSchema.get("properties", {})


class TestServerMetadata:
    """Tests for server metadata and configuration."""

    @pytest.mark.asyncio
    async def test_server_has_name(self, client: Client) -> None:
        """Test that server reports its name."""
        result = client.initialize_result
        assert result is not None
        assert result.serverInfo is not None
        assert result.serverInfo.name is not None
        assert "gurufocus" in result.serverInfo.name.lower()

    @pytest.mark.asyncio
    async def test_server_reports_capabilities(self, client: Client) -> None:
        """Test that server reports its capabilities."""
        result = client.initialize_result
        assert result is not None
        assert result.capabilities is not None

        # Should have resources capability
        assert result.capabilities.resources is not None

    @pytest.mark.asyncio
    async def test_server_reports_tools_capability(self, client: Client) -> None:
        """Test that server reports tools capability."""
        result = client.initialize_result
        assert result is not None
        assert result.capabilities is not None

        # Should have tools capability
        assert result.capabilities.tools is not None


class TestErrorHandlingIntegration:
    """Tests for error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_resource_uri(self, client: Client) -> None:
        """Test handling of invalid resource URI."""
        raised = False
        try:
            await client.read_resource("gurufocus://invalid/resource/path")
        except Exception:
            raised = True

        assert raised, "Expected error for invalid resource URI"

    @pytest.mark.asyncio
    async def test_tool_with_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that tool raises ToolError for invalid symbol."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "!!invalid!!"})

        # Verify the error message contains relevant information
        error_msg = str(exc_info.value).lower()
        assert "authentication" in error_msg or "invalid" in error_msg or "error" in error_msg
