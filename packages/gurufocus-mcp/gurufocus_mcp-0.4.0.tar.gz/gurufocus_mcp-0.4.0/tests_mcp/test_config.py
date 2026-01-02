"""Tests for MCP server configuration."""

import pytest

from gurufocus_mcp.config import MCPServerSettings, get_settings


class TestMCPServerSettings:
    """Tests for MCPServerSettings."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = MCPServerSettings(api_token="test-token")

        assert settings.api_token == "test-token"
        assert settings.api_base_url == "https://api.gurufocus.com/public/user"
        assert settings.api_timeout == 30.0
        assert settings.api_max_retries == 3
        assert settings.cache_enabled is True
        assert settings.cache_dir == ".cache/gurufocus-mcp"
        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_rpm == 30.0
        assert settings.rate_limit_daily == 0
        assert settings.log_level == "INFO"
        assert settings.server_name == "gurufocus-mcp"
        assert settings.server_version == "0.1.0"

    def test_custom_values(self) -> None:
        """Test that custom values can be set."""
        settings = MCPServerSettings(
            api_token="custom-token",
            api_base_url="https://custom.api.com",
            api_timeout=60.0,
            api_max_retries=5,
            cache_enabled=False,
            cache_dir="/custom/cache",
            rate_limit_enabled=False,
            rate_limit_rpm=60.0,
            rate_limit_daily=1000,
            log_level="DEBUG",
            server_name="custom-server",
            server_version="1.0.0",
        )

        assert settings.api_token == "custom-token"
        assert settings.api_base_url == "https://custom.api.com"
        assert settings.api_timeout == 60.0
        assert settings.api_max_retries == 5
        assert settings.cache_enabled is False
        assert settings.cache_dir == "/custom/cache"
        assert settings.rate_limit_enabled is False
        assert settings.rate_limit_rpm == 60.0
        assert settings.rate_limit_daily == 1000
        assert settings.log_level == "DEBUG"
        assert settings.server_name == "custom-server"
        assert settings.server_version == "1.0.0"

    def test_validate_api_token_with_valid_token(self) -> None:
        """Test that valid API token passes validation."""
        settings = MCPServerSettings(api_token="valid-token")
        assert settings.validate_api_token() is True

    def test_validate_api_token_with_empty_token(self) -> None:
        """Test that empty API token fails validation."""
        settings = MCPServerSettings(api_token="")
        assert settings.validate_api_token() is False

    def test_validate_api_token_with_whitespace_only(self) -> None:
        """Test that whitespace-only API token fails validation."""
        settings = MCPServerSettings(api_token="   ")
        assert settings.validate_api_token() is False

    def test_from_environment_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings can be loaded from environment variables."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "env-token")
        monkeypatch.setenv("GURUFOCUS_API_TIMEOUT", "45.0")
        monkeypatch.setenv("GURUFOCUS_CACHE_ENABLED", "false")
        monkeypatch.setenv("GURUFOCUS_LOG_LEVEL", "WARNING")

        settings = MCPServerSettings()

        assert settings.api_token == "env-token"
        assert settings.api_timeout == 45.0
        assert settings.cache_enabled is False
        assert settings.log_level == "WARNING"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_settings returns a settings instance."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings = get_settings()

        assert isinstance(settings, MCPServerSettings)
        assert settings.api_token == "test-token"

    def test_returns_new_instance_each_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_settings returns a new instance each call."""
        monkeypatch.setenv("GURUFOCUS_API_TOKEN", "test-token")

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is not settings2
