"""Tests for output formatting utilities."""

import json

from gurufocus_mcp.formatting import (
    format_output,
    toon_decode,
    toon_encode,
)


class TestFormatOutput:
    """Tests for format_output function."""

    def test_json_format_returns_dict(self) -> None:
        """Test that JSON format returns the original dictionary."""
        data = {"symbol": "AAPL", "price": 150.0}
        result = format_output(data, format="json")
        assert result == data
        assert isinstance(result, dict)

    def test_toon_format_returns_string(self) -> None:
        """Test that TOON format returns a string."""
        data = {"symbol": "AAPL", "price": 150.0}
        result = format_output(data, format="toon")
        assert isinstance(result, str)

    def test_default_format_is_toon(self) -> None:
        """Test that default format is TOON."""
        data = {"symbol": "AAPL", "price": 150.0}
        result = format_output(data)
        assert isinstance(result, str)

    def test_json_preserves_nested_data(self) -> None:
        """Test that JSON format preserves nested structures."""
        data = {
            "symbol": "AAPL",
            "metrics": {"pe_ratio": 25.5, "market_cap": 2500000000000},
            "tags": ["tech", "large-cap"],
        }
        result = format_output(data, format="json")
        assert result == data
        assert result["metrics"]["pe_ratio"] == 25.5
        assert result["tags"] == ["tech", "large-cap"]


class TestToonEncoding:
    """Tests for TOON encoding/decoding."""

    def test_encode_simple_dict(self) -> None:
        """Test encoding a simple dictionary."""
        data = {"name": "Alice", "age": 30}
        encoded = toon_encode(data)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_encode_decode_roundtrip_simple(self) -> None:
        """Test that encoding and decoding produces original data."""
        original = {"symbol": "AAPL", "price": 150.50, "name": "Apple Inc."}
        encoded = toon_encode(original)
        decoded = toon_decode(encoded)
        assert decoded == original

    def test_encode_decode_roundtrip_nested(self) -> None:
        """Test roundtrip with nested structures."""
        original = {
            "symbol": "AAPL",
            "price": 150.50,
            "metrics": {
                "pe_ratio": 25.5,
                "market_cap": 2500000000000,
            },
        }
        encoded = toon_encode(original)
        decoded = toon_decode(encoded)
        assert decoded == original

    def test_encode_list(self) -> None:
        """Test encoding a list."""
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        encoded = toon_encode(data)
        decoded = toon_decode(encoded)
        assert decoded == data

    def test_encode_with_null_values(self) -> None:
        """Test encoding data with null values."""
        data = {"symbol": "AAPL", "value": None, "name": "Apple"}
        encoded = toon_encode(data)
        decoded = toon_decode(encoded)
        assert decoded == data

    def test_toon_is_smaller_than_json(self) -> None:
        """Test that TOON output is smaller than JSON."""
        # Sample financial data similar to what the API returns
        data = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "price": {"current": 150.50, "change": 2.5, "change_percent": 1.69},
            "valuation": {
                "pe_ratio": 25.5,
                "pb_ratio": 45.2,
                "ps_ratio": 7.8,
                "market_cap": 2500000000000,
            },
            "gf_score": {"score": 85, "rank": "Good"},
        }

        json_output = json.dumps(data)
        toon_output = toon_encode(data)

        # TOON should be smaller (not asserting exact percentage as it varies)
        assert len(toon_output) < len(json_output)


class TestFormatOutputComplexTypes:
    """Tests for format_output with complex data types."""

    def test_format_output_handles_complex_types(self) -> None:
        """Test format_output with various data types."""
        data = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        # Should not raise for either format
        json_result = format_output(data, format="json")
        toon_result = format_output(data, format="toon")

        assert json_result == data
        assert isinstance(toon_result, str)
