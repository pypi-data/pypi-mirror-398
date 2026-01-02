"""Tests for error handling module."""

import pytest

from gurufocus_api.exceptions import (
    APIError,
    AuthenticationError,
    InvalidSymbolError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from gurufocus_mcp.errors import (
    MCPError,
    handle_api_error,
    safe_float,
    safe_get,
    safe_int,
    validate_symbol,
    validate_symbols,
    with_error_handling,
)


class TestMCPError:
    """Tests for MCPError class."""

    def test_to_dict_basic(self) -> None:
        """Test basic error to dict conversion."""
        error = MCPError(
            error_type="test_error",
            message="Test message",
        )
        result = error.to_dict()

        assert result["error"] is True
        assert result["error_type"] == "test_error"
        assert result["message"] == "Test message"
        assert "details" not in result
        assert "suggestions" not in result

    def test_to_dict_with_details(self) -> None:
        """Test error with details."""
        error = MCPError(
            error_type="test_error",
            message="Test message",
            details={"key": "value"},
        )
        result = error.to_dict()

        assert result["details"] == {"key": "value"}

    def test_to_dict_with_suggestions(self) -> None:
        """Test error with suggestions."""
        error = MCPError(
            error_type="test_error",
            message="Test message",
            suggestions=["Suggestion 1", "Suggestion 2"],
        )
        result = error.to_dict()

        assert result["suggestions"] == ["Suggestion 1", "Suggestion 2"]


class TestHandleApiError:
    """Tests for handle_api_error function."""

    def test_invalid_symbol_error(self) -> None:
        """Test handling InvalidSymbolError."""
        error = InvalidSymbolError("INVALID")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "invalid_symbol"
        assert "INVALID" in result["message"]
        assert result["details"]["symbol"] == "INVALID"
        assert len(result["suggestions"]) > 0

    def test_authentication_error(self) -> None:
        """Test handling AuthenticationError."""
        error = AuthenticationError("Invalid token")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "authentication_error"
        assert "authentication" in result["message"].lower()

    def test_rate_limit_error(self) -> None:
        """Test handling RateLimitError."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "rate_limit"
        assert result["details"]["retry_after"] == 60
        assert "60" in result["message"]

    def test_rate_limit_error_no_retry(self) -> None:
        """Test handling RateLimitError without retry_after."""
        error = RateLimitError("Rate limit exceeded")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "rate_limit"

    def test_not_found_error(self) -> None:
        """Test handling NotFoundError."""
        error = NotFoundError("Resource not found")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "not_found"

    def test_network_error(self) -> None:
        """Test handling NetworkError."""
        error = NetworkError("Connection failed")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "network_error"
        assert "network" in result["message"].lower()

    def test_validation_error(self) -> None:
        """Test handling ValidationError."""
        error = ValidationError("Invalid response format")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "validation_error"

    def test_api_error(self) -> None:
        """Test handling APIError."""
        error = APIError("Server error", status_code=500)
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "api_error"
        assert result["details"]["status_code"] == 500

    def test_timeout_error(self) -> None:
        """Test handling asyncio.TimeoutError."""
        error = TimeoutError()
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "timeout"
        assert "timed out" in result["message"].lower()

    def test_unexpected_error(self) -> None:
        """Test handling unexpected errors."""
        error = ValueError("Unexpected error")
        result = handle_api_error(error)

        assert result["error"] is True
        assert result["error_type"] == "unexpected_error"
        assert result["details"]["error_class"] == "ValueError"


class TestWithErrorHandling:
    """Tests for with_error_handling decorator."""

    @pytest.mark.asyncio
    async def test_successful_function(self) -> None:
        """Test decorator passes through successful results."""

        @with_error_handling
        async def success_func() -> dict:
            return {"result": "success"}

        result = await success_func()
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_function_with_error(self) -> None:
        """Test decorator catches errors."""

        @with_error_handling
        async def error_func() -> dict:
            raise InvalidSymbolError("BAD")

        result = await error_func()
        assert result["error"] is True
        assert result["error_type"] == "invalid_symbol"

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self) -> None:
        """Test decorator preserves function metadata."""

        @with_error_handling
        async def documented_func() -> dict:
            """This is a docstring."""
            return {}

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring."


class TestValidateSymbol:
    """Tests for validate_symbol function."""

    def test_valid_symbol(self) -> None:
        """Test valid symbol normalization."""
        assert validate_symbol("aapl") == "AAPL"
        assert validate_symbol("MSFT") == "MSFT"
        assert validate_symbol("  googl  ") == "GOOGL"

    def test_symbol_with_exchange(self) -> None:
        """Test symbol with exchange suffix."""
        assert validate_symbol("BMW.DE") == "BMW.DE"
        assert validate_symbol("0700.HK") == "0700.HK"

    def test_empty_symbol(self) -> None:
        """Test empty symbol returns None."""
        assert validate_symbol("") is None
        assert validate_symbol("   ") is None

    def test_none_symbol(self) -> None:
        """Test None-like inputs."""
        # Empty string is the closest we can test
        assert validate_symbol("") is None

    def test_too_long_symbol(self) -> None:
        """Test symbol that exceeds max length."""
        assert validate_symbol("A" * 20) is None


class TestValidateSymbols:
    """Tests for validate_symbols function."""

    def test_all_valid(self) -> None:
        """Test list of all valid symbols."""
        valid, invalid = validate_symbols(["AAPL", "MSFT", "GOOGL"])
        assert valid == ["AAPL", "MSFT", "GOOGL"]
        assert invalid == []

    def test_some_invalid(self) -> None:
        """Test list with some invalid symbols."""
        valid, invalid = validate_symbols(["AAPL", "", "GOOGL"])
        assert valid == ["AAPL", "GOOGL"]
        assert invalid == [""]

    def test_max_count(self) -> None:
        """Test max count limit."""
        symbols = ["A", "B", "C", "D", "E"]
        valid, _invalid = validate_symbols(symbols, max_count=3)
        assert len(valid) == 3
        assert valid == ["A", "B", "C"]

    def test_empty_list(self) -> None:
        """Test empty input list."""
        valid, invalid = validate_symbols([])
        assert valid == []
        assert invalid == []


class TestSafeGet:
    """Tests for safe_get function."""

    def test_simple_key(self) -> None:
        """Test getting simple key."""
        data = {"key": "value"}
        assert safe_get(data, "key") == "value"

    def test_nested_keys(self) -> None:
        """Test getting nested keys."""
        data = {"level1": {"level2": {"level3": "value"}}}
        assert safe_get(data, "level1", "level2", "level3") == "value"

    def test_missing_key(self) -> None:
        """Test missing key returns default."""
        data = {"key": "value"}
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", default="default") == "default"

    def test_none_data(self) -> None:
        """Test None data returns default."""
        assert safe_get(None, "key") is None
        assert safe_get(None, "key", default="default") == "default"

    def test_intermediate_none(self) -> None:
        """Test None at intermediate level."""
        data = {"level1": None}
        assert safe_get(data, "level1", "level2") is None


class TestSafeFloat:
    """Tests for safe_float function."""

    def test_valid_float(self) -> None:
        """Test valid float conversion."""
        assert safe_float(3.14) == 3.14
        assert safe_float("3.14") == 3.14
        assert safe_float(42) == 42.0

    def test_none_value(self) -> None:
        """Test None returns default."""
        assert safe_float(None) is None
        assert safe_float(None, default=0.0) == 0.0

    def test_invalid_value(self) -> None:
        """Test invalid value returns default."""
        assert safe_float("not a number") is None
        assert safe_float("not a number", default=-1.0) == -1.0


class TestSafeInt:
    """Tests for safe_int function."""

    def test_valid_int(self) -> None:
        """Test valid int conversion."""
        assert safe_int(42) == 42
        assert safe_int("42") == 42
        assert safe_int(3.7) == 3

    def test_none_value(self) -> None:
        """Test None returns default."""
        assert safe_int(None) is None
        assert safe_int(None, default=0) == 0

    def test_invalid_value(self) -> None:
        """Test invalid value returns default."""
        assert safe_int("not a number") is None
        assert safe_int("not a number", default=-1) == -1
