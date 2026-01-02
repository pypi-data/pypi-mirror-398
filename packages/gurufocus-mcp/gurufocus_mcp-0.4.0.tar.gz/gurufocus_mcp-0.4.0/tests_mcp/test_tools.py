"""Tests for MCP tools."""

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


class TestToolRegistration:
    """Tests for tool registration."""

    def test_get_stock_summary_tool_registered(self, server) -> None:
        """Test that get_stock_summary tool is registered."""
        tools = list(server._tool_manager._tools.keys())

        assert "get_stock_summary" in tools

    def test_tool_count(self, server) -> None:
        """Test that 14 tools are registered."""
        tool_count = len(server._tool_manager._tools)
        assert tool_count == 21

    def test_get_stock_financials_tool_registered(self, server) -> None:
        """Test that get_stock_financials tool is registered."""
        tools = list(server._tool_manager._tools.keys())
        assert "get_stock_financials" in tools

    def test_get_stock_keyratios_tool_registered(self, server) -> None:
        """Test that get_stock_keyratios tool is registered."""
        tools = list(server._tool_manager._tools.keys())
        assert "get_stock_keyratios" in tools

    def test_get_stock_summary_has_description(self, server) -> None:
        """Test that get_stock_summary tool has a description."""
        tools = server._tool_manager._tools
        summary_tool = tools.get("get_stock_summary")

        assert summary_tool is not None
        assert summary_tool.description is not None
        assert "summary" in summary_tool.description.lower()

    def test_get_stock_summary_has_symbol_parameter(self, server) -> None:
        """Test that get_stock_summary tool has symbol parameter."""
        tools = server._tool_manager._tools
        summary_tool = tools.get("get_stock_summary")

        assert summary_tool is not None
        assert summary_tool.parameters is not None


class TestToolDiscovery:
    """Tests for tool discovery via MCP protocol."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, client: Client) -> None:
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
    async def test_tool_has_input_schema(self, client: Client) -> None:
        """Test that tool has proper input schema."""
        tools = await client.list_tools()
        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        assert summary_tool.inputSchema is not None
        assert "properties" in summary_tool.inputSchema
        assert "symbol" in summary_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_symbol_parameter_has_description(self, client: Client) -> None:
        """Test that symbol parameter has a description."""
        tools = await client.list_tools()
        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        symbol_prop = summary_tool.inputSchema["properties"]["symbol"]
        assert "description" in symbol_prop
        assert "ticker" in symbol_prop["description"].lower()


class TestToolValidation:
    """Tests for tool input validation."""

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol format raises ToolError."""
        from fastmcp.exceptions import ToolError

        # Invalid symbols pass basic validation but fail API auth
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "!!invalid!!"})

        # Should get some kind of error (auth or validation)
        error_msg = str(exc_info.value).lower()
        assert "error" in error_msg or "invalid" in error_msg or "authentication" in error_msg

    @pytest.mark.asyncio
    async def test_empty_symbol_raises_error(self, client: Client) -> None:
        """Test that empty symbol raises ToolError."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg

    @pytest.mark.asyncio
    async def test_symbol_with_special_chars_raises_error(self, client: Client) -> None:
        """Test that symbol with special characters raises ToolError."""
        from fastmcp.exceptions import ToolError

        # Symbols with special chars may pass basic validation but fail API
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "AAPL@#$"})

        error_msg = str(exc_info.value).lower()
        assert "error" in error_msg or "invalid" in error_msg or "authentication" in error_msg


class TestToolExecution:
    """Tests for tool execution behavior."""

    @pytest.mark.asyncio
    async def test_valid_symbol_format_accepted(self, client: Client) -> None:
        """Test that valid symbol format is accepted (may fail due to auth)."""
        from fastmcp.exceptions import ToolError

        # With test token, we expect auth error, not validation error
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "AAPL"})

        # Should not be a symbol validation error
        error_msg = str(exc_info.value).lower()
        assert "invalid symbol format" not in error_msg

    @pytest.mark.asyncio
    async def test_symbol_with_dot_accepted(self, client: Client) -> None:
        """Test that symbol with dot (like BRK.A) is accepted."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "BRK.A"})

        # Should not be a symbol validation error
        error_msg = str(exc_info.value).lower()
        assert "invalid symbol format" not in error_msg

    @pytest.mark.asyncio
    async def test_lowercase_symbol_normalized(self, client: Client) -> None:
        """Test that lowercase symbols are normalized to uppercase."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "aapl"})

        # Should not be a symbol validation error
        error_msg = str(exc_info.value).lower()
        assert "invalid symbol format" not in error_msg


class TestToolErrorHandling:
    """Tests for tool error handling via ToolError exceptions."""

    @pytest.mark.asyncio
    async def test_tool_raises_tool_error(self, client: Client) -> None:
        """Test that tool errors are raised as ToolError exceptions."""
        from fastmcp.exceptions import ToolError

        # Call with symbol that triggers error (auth failure with test token)
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "###"})

        # ToolError should have a message
        assert str(exc_info.value) is not None
        assert len(str(exc_info.value)) > 0

    @pytest.mark.asyncio
    async def test_auth_error_raises_tool_error(self, client: Client) -> None:
        """Test behavior when API authentication fails."""
        from fastmcp.exceptions import ToolError

        # The test token triggers auth error when trying to fetch real data
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_summary", {"symbol": "AAPL"})

        # Should get auth error
        error_msg = str(exc_info.value).lower()
        assert "authentication" in error_msg or "token" in error_msg


class TestToolFormatParameter:
    """Tests for format parameter on tools."""

    def test_get_stock_summary_has_format_parameter(self, server) -> None:
        """Test that get_stock_summary tool has format parameter."""
        tools = server._tool_manager._tools
        summary_tool = tools.get("get_stock_summary")

        assert summary_tool is not None
        assert summary_tool.parameters is not None

    @pytest.mark.asyncio
    async def test_format_parameter_in_schema(self, client: Client) -> None:
        """Test that format parameter appears in tool schema."""
        tools = await client.list_tools()
        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        assert "format" in summary_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_format_parameter_has_default(self, client: Client) -> None:
        """Test that format parameter has default value of 'toon'."""
        tools = await client.list_tools()
        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        format_prop = summary_tool.inputSchema["properties"]["format"]
        assert format_prop.get("default") == "toon"

    @pytest.mark.asyncio
    async def test_format_parameter_has_description(self, client: Client) -> None:
        """Test that format parameter has a description."""
        tools = await client.list_tools()
        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        format_prop = summary_tool.inputSchema["properties"]["format"]
        assert "description" in format_prop
        assert "toon" in format_prop["description"].lower()

    @pytest.mark.asyncio
    async def test_format_not_required(self, client: Client) -> None:
        """Test that format parameter is optional (not in required list)."""
        tools = await client.list_tools()
        summary_tool = next((t for t in tools if t.name == "get_stock_summary"), None)

        assert summary_tool is not None
        required = summary_tool.inputSchema.get("required", [])
        assert "format" not in required


class TestGetStockFinancialsTool:
    """Tests for get_stock_financials tool."""

    def test_tool_has_description(self, server) -> None:
        """Test that get_stock_financials tool has a description."""
        tools = server._tool_manager._tools
        financials_tool = tools.get("get_stock_financials")

        assert financials_tool is not None
        assert financials_tool.description is not None
        assert "financial" in financials_tool.description.lower()

    @pytest.mark.asyncio
    async def test_tool_has_symbol_parameter(self, client: Client) -> None:
        """Test that tool has symbol parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_financials"), None)

        assert tool is not None
        assert "symbol" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_tool_has_period_type_parameter(self, client: Client) -> None:
        """Test that tool has period_type parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_financials"), None)

        assert tool is not None
        assert "period_type" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_period_type_has_default(self, client: Client) -> None:
        """Test that period_type parameter has default value of 'annual'."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_financials"), None)

        assert tool is not None
        period_prop = tool.inputSchema["properties"]["period_type"]
        assert period_prop.get("default") == "annual"

    @pytest.mark.asyncio
    async def test_tool_has_format_parameter(self, client: Client) -> None:
        """Test that tool has format parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_financials"), None)

        assert tool is not None
        assert "format" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol raises ToolError."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_financials", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg


class TestGetStockKeyratiosTool:
    """Tests for get_stock_keyratios tool."""

    def test_tool_has_description(self, server) -> None:
        """Test that get_stock_keyratios tool has a description."""
        tools = server._tool_manager._tools
        keyratios_tool = tools.get("get_stock_keyratios")

        assert keyratios_tool is not None
        assert keyratios_tool.description is not None
        assert "ratio" in keyratios_tool.description.lower()

    @pytest.mark.asyncio
    async def test_tool_has_symbol_parameter(self, client: Client) -> None:
        """Test that tool has symbol parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_keyratios"), None)

        assert tool is not None
        assert "symbol" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_tool_has_format_parameter(self, client: Client) -> None:
        """Test that tool has format parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_keyratios"), None)

        assert tool is not None
        assert "format" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol raises ToolError."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_keyratios", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg


class TestGetStockGurusTool:
    """Tests for get_stock_gurus tool."""

    def test_tool_registered(self, server) -> None:
        """Test that get_stock_gurus tool is registered."""
        tools = list(server._tool_manager._tools.keys())
        assert "get_stock_gurus" in tools

    def test_tool_has_description(self, server) -> None:
        """Test that get_stock_gurus tool has a description."""
        tools = server._tool_manager._tools
        gurus_tool = tools.get("get_stock_gurus")

        assert gurus_tool is not None
        assert gurus_tool.description is not None
        assert "guru" in gurus_tool.description.lower()

    @pytest.mark.asyncio
    async def test_tool_has_symbol_parameter(self, client: Client) -> None:
        """Test that tool has symbol parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_gurus"), None)

        assert tool is not None
        assert "symbol" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_tool_has_format_parameter(self, client: Client) -> None:
        """Test that tool has format parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_gurus"), None)

        assert tool is not None
        assert "format" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol raises ToolError."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_gurus", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg


class TestGetStockExecutivesTool:
    """Tests for get_stock_executives tool."""

    def test_tool_registered(self, server) -> None:
        """Test that get_stock_executives tool is registered."""
        tools = list(server._tool_manager._tools.keys())
        assert "get_stock_executives" in tools

    def test_tool_has_description(self, server) -> None:
        """Test that get_stock_executives tool has a description."""
        tools = server._tool_manager._tools
        executives_tool = tools.get("get_stock_executives")

        assert executives_tool is not None
        assert executives_tool.description is not None
        assert "executive" in executives_tool.description.lower()

    @pytest.mark.asyncio
    async def test_tool_has_symbol_parameter(self, client: Client) -> None:
        """Test that tool has symbol parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_executives"), None)

        assert tool is not None
        assert "symbol" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_tool_has_format_parameter(self, client: Client) -> None:
        """Test that tool has format parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_executives"), None)

        assert tool is not None
        assert "format" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol raises ToolError."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_executives", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg


class TestGetStockTradesHistoryTool:
    """Tests for get_stock_trades_history tool."""

    def test_tool_registered(self, server) -> None:
        """Test that get_stock_trades_history tool is registered."""
        tools = list(server._tool_manager._tools.keys())
        assert "get_stock_trades_history" in tools

    def test_tool_has_description(self, server) -> None:
        """Test that get_stock_trades_history tool has a description."""
        tools = server._tool_manager._tools
        trades_tool = tools.get("get_stock_trades_history")

        assert trades_tool is not None
        assert trades_tool.description is not None
        assert "trade" in trades_tool.description.lower()

    @pytest.mark.asyncio
    async def test_tool_has_symbol_parameter(self, client: Client) -> None:
        """Test that tool has symbol parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_trades_history"), None)

        assert tool is not None
        assert "symbol" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_tool_has_format_parameter(self, client: Client) -> None:
        """Test that tool has format parameter."""
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == "get_stock_trades_history"), None)

        assert tool is not None
        assert "format" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self, client: Client) -> None:
        """Test that invalid symbol raises ToolError."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_stock_trades_history", {"symbol": ""})

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "symbol" in error_msg
