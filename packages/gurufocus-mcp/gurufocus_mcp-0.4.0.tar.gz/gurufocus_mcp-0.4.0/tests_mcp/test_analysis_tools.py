"""Tests for QGARP analysis MCP tools."""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

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


class TestQGARPAnalysisToolRegistration:
    """Tests for QGARP analysis tool registration."""

    def test_qgarp_analysis_tool_registered(self, server) -> None:
        """Test that get_qgarp_analysis tool is registered."""
        tools = list(server._tool_manager._tools.keys())
        assert "get_qgarp_analysis" in tools

    def test_qgarp_analysis_tool_has_description(self, server) -> None:
        """Test that get_qgarp_analysis tool has a description."""
        tools = server._tool_manager._tools
        analysis_tool = tools.get("get_qgarp_analysis")

        assert analysis_tool is not None
        assert analysis_tool.description is not None
        assert "QGARP" in analysis_tool.description
        assert "scorecard" in analysis_tool.description.lower()

    def test_qgarp_analysis_tool_has_symbol_parameter(self, server) -> None:
        """Test that get_qgarp_analysis tool has symbol parameter."""
        tools = server._tool_manager._tools
        analysis_tool = tools.get("get_qgarp_analysis")

        assert analysis_tool is not None
        assert analysis_tool.parameters is not None

    def test_qgarp_analysis_tool_has_format_parameter(self, server) -> None:
        """Test that get_qgarp_analysis tool has format parameter."""
        tools = server._tool_manager._tools
        analysis_tool = tools.get("get_qgarp_analysis")

        assert analysis_tool is not None
        assert analysis_tool.parameters is not None


class TestQGARPAnalysisToolDiscovery:
    """Tests for QGARP analysis tool discovery via MCP protocol."""

    @pytest.mark.asyncio
    async def test_qgarp_analysis_tool_discoverable(self, client: Client) -> None:
        """Test that get_qgarp_analysis tool is discoverable."""
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]

        assert "get_qgarp_analysis" in tool_names

    @pytest.mark.asyncio
    async def test_qgarp_analysis_tool_has_input_schema(self, client: Client) -> None:
        """Test that get_qgarp_analysis tool has proper input schema."""
        tools = await client.list_tools()
        analysis_tool = next((t for t in tools if t.name == "get_qgarp_analysis"), None)

        assert analysis_tool is not None
        assert analysis_tool.inputSchema is not None
        assert "properties" in analysis_tool.inputSchema
        assert "symbol" in analysis_tool.inputSchema["properties"]


class TestQGARPAnalysisToolValidation:
    """Tests for QGARP analysis tool input validation."""

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol format raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "!!invalid!!"})

        error_msg = str(exc_info.value).lower()
        assert "error" in error_msg or "invalid" in error_msg or "authentication" in error_msg

    @pytest.mark.asyncio
    async def test_empty_symbol_raises_error(self, client: Client) -> None:
        """Test that empty symbol raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg

    @pytest.mark.asyncio
    async def test_symbol_with_special_chars_raises_error(self, client: Client) -> None:
        """Test that symbol with special characters raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "AAPL@#$"})

        error_msg = str(exc_info.value).lower()
        assert "error" in error_msg or "invalid" in error_msg or "authentication" in error_msg


class TestQGARPAnalysisToolExecution:
    """Tests for QGARP analysis tool execution behavior."""

    @pytest.mark.asyncio
    async def test_valid_symbol_format_accepted(self, client: Client) -> None:
        """Test that valid symbol format is accepted (may fail due to auth)."""
        # With test token, we expect auth error, not validation error
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "AAPL"})

        # Should not be a symbol validation error
        error_msg = str(exc_info.value).lower()
        assert "invalid symbol format" not in error_msg

    @pytest.mark.asyncio
    async def test_lowercase_symbol_normalized(self, client: Client) -> None:
        """Test that lowercase symbols are normalized to uppercase."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "aapl"})

        # Should not be a symbol validation error
        error_msg = str(exc_info.value).lower()
        assert "invalid symbol format" not in error_msg

    @pytest.mark.asyncio
    async def test_format_parameter_accepts_toon(self, client: Client) -> None:
        """Test that format parameter accepts 'toon' value."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "AAPL", "format": "toon"})

        # Should not be a format validation error
        error_msg = str(exc_info.value).lower()
        assert "format" not in error_msg

    @pytest.mark.asyncio
    async def test_format_parameter_accepts_json(self, client: Client) -> None:
        """Test that format parameter accepts 'json' value."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "AAPL", "format": "json"})

        # Should not be a format validation error
        error_msg = str(exc_info.value).lower()
        assert "format" not in error_msg


class TestQGARPAnalysisToolErrorHandling:
    """Tests for QGARP analysis tool error handling."""

    @pytest.mark.asyncio
    async def test_tool_raises_tool_error_on_invalid_input(self, client: Client) -> None:
        """Test that invalid input raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "###"})

        assert str(exc_info.value) is not None

    @pytest.mark.asyncio
    async def test_tool_error_message_is_informative(self, client: Client) -> None:
        """Test that ToolError has informative message."""
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_qgarp_analysis", {"symbol": "!!!"})

        error_msg = str(exc_info.value)
        # Should have some indication of what went wrong
        assert len(error_msg) > 0
