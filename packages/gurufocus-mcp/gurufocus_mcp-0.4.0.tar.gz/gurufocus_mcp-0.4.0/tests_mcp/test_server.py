"""Tests for MCP server."""

from unittest.mock import patch

import pytest

from gurufocus_mcp.config import MCPServerSettings
from gurufocus_mcp.server import create_server


class TestCreateServer:
    """Tests for create_server function."""

    def test_creates_fastmcp_server(self) -> None:
        """Test that create_server returns a FastMCP instance."""
        settings = MCPServerSettings(api_token="test-token")
        server = create_server(settings)

        assert server is not None
        assert server.name == "gurufocus-mcp"

    def test_uses_custom_settings(self) -> None:
        """Test that create_server uses custom settings."""
        settings = MCPServerSettings(
            api_token="test-token",
            server_name="custom-server",
            server_version="2.0.0",
        )
        server = create_server(settings)

        assert server.name == "custom-server"

    def test_loads_settings_from_env_if_not_provided(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that create_server loads settings from environment if not provided."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "env-token")
        monkeypatch.setenv("GURUFOCUS_SERVER_NAME", "env-server")

        server = create_server()

        assert server.name == "env-server"


class TestServerResources:
    """Tests for server resources registration."""

    def test_server_has_resources_registered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that server has resources registered."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings = MCPServerSettings(api_token="test-token")
        server = create_server(settings)

        assert hasattr(server, "_resource_manager")

    def test_server_no_resource_templates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that server has no resource templates (summary is now a tool)."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings = MCPServerSettings(api_token="test-token")
        server = create_server(settings)

        template_count = len(server._resource_manager._templates)
        assert template_count == 0

    def test_server_no_static_resources(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that server has no static resources."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings = MCPServerSettings(api_token="test-token")
        server = create_server(settings)

        resource_count = len(server._resource_manager._resources)
        assert resource_count == 0

    def test_server_has_get_stock_summary_tool(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that server has get_stock_summary tool registered."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings = MCPServerSettings(api_token="test-token")
        server = create_server(settings)

        tool_names = list(server._tool_manager._tools.keys())
        assert "get_stock_summary" in tool_names

    def test_server_tool_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that server has exactly 14 tools registered."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings = MCPServerSettings(api_token="test-token")
        server = create_server(settings)

        tool_count = len(server._tool_manager._tools)
        assert tool_count == 21


class TestServerMain:
    """Tests for the server main entry point."""

    def test_main_exits_without_api_token(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that main exits with error if API token not set."""
        monkeypatch.delenv("GURUFOCUS_API_TOKEN", raising=False)

        from gurufocus_mcp import config

        def mock_get_settings() -> MCPServerSettings:
            return MCPServerSettings(api_token="")

        monkeypatch.setattr(config, "get_settings", mock_get_settings)

        import gurufocus_mcp.server as server_module

        monkeypatch.setattr(server_module, "get_settings", mock_get_settings)

        with pytest.raises(SystemExit) as exc_info:
            server_module.main()

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "GURUFOCUS_API_TOKEN" in captured.err

    def test_main_runs_server_with_valid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that main runs the server if API token is set."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        import gurufocus_mcp.server as server_module

        with patch.object(server_module.mcp, "run") as mock_run:
            server_module.main()
            mock_run.assert_called_once()


class TestModuleImports:
    """Tests for module-level imports and exports."""

    def test_main_module_exports(self) -> None:
        """Test that main module exports expected objects."""
        from gurufocus_mcp import (
            MCPServerSettings,
            __version__,
            create_server,
            get_settings,
            main,
            mcp,
        )

        assert __version__ == "0.1.0"
        assert callable(create_server)
        assert callable(get_settings)
        assert callable(main)
        assert mcp is not None
        assert MCPServerSettings is not None

    def test_can_import_main_module(self) -> None:
        """Test that __main__ module can be imported."""
        import gurufocus_mcp.__main__  # noqa: F401
