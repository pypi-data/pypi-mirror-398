"""Pytest configuration and fixtures for MCP server tests."""

import pytest


@pytest.fixture
def mock_api_token() -> str:
    """Return a mock API token for testing."""
    return "test-api-token-12345"


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch, mock_api_token: str) -> None:
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("GURUFOCUS_API_TOKEN", mock_api_token)
    monkeypatch.setenv("GURUFOCUS_LOG_LEVEL", "DEBUG")
