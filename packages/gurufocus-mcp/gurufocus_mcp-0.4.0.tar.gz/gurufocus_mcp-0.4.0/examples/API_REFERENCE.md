# GuruFocus MCP Server API Reference

Reference for resources available in the GuruFocus MCP server.

## Resources

The server exposes financial data as read-only MCP resources. Resources follow RESTful design principles - they are data endpoints that can be read, not actions to invoke.

---

### gurufocus://schema/stock-summary

Get the JSON Schema for the stock summary response.

Use this resource to understand the structure of data returned by the stock summary resource. The schema is generated from the `StockSummary` Pydantic model.

**Returns:** JSON Schema object describing the stock summary data structure

**Example Usage:**
```
Read resource: gurufocus://schema/stock-summary
```

---

### gurufocus://stock/{symbol}/summary

Get comprehensive summary for a stock.

**URI Parameters:**
| Name       | Type   | Description                                   |
| ---------- | ------ | --------------------------------------------- |
| `{symbol}` | string | Stock ticker symbol (e.g., AAPL, MSFT, GOOGL) |

**Example URI:** `gurufocus://stock/FAKE1/summary`

**Returns:** JSON object with comprehensive stock summary data:

```json
{
  "symbol": "FAKE1",
  "general": {
    "company_name": "Fake Company One",
    "current_price": 256.0,
    "currency": "$",
    "country": "USA",
    "sector": "TestSector",
    "industry_group": "TestGroup",
    "short_description": "Fake Company One is a fictional test company.",
    "valuation_status": "Fairly Valued",
    "risk_assessment": "Medium Risk: For testing purposes only"
  },
  "quality": {
    "gf_score": 67,
    "financial_strength": 5,
    "profitability_rank": 1,
    "growth_rank": 10,
    "gf_value_rank": 8,
    "momentum_rank": 4
  },
  "valuation": {
    "gf_value": 216.09,
    "earnings_power_value": 115.40,
    "tangible_book": 41.68,
    "projected_fcf": 101.93,
    "dcf_fcf_based": 115.92,
    "dcf_earnings_based": 158.24,
    "graham_number": 76.04,
    "peter_lynch_value": 79.05,
    "median_ps_value": 165.04
  },
  "ratios": {
    "pe_ttm": {
      "value": 21.89,
      "status": 0,
      "his": {"low": 12.5, "high": 37.5, "med": 25.0},
      "indu": {"global_rank": 596, "indu_med": 23.32, "indu_tot": 1516}
    },
    "forward_pe": {
      "value": 23.15,
      "status": 0,
      "his": {"low": 11.0, "high": 33.0, "med": 22.0},
      "indu": {"global_rank": 1155, "indu_med": 23.18, "indu_tot": 1078}
    },
    "pb_ratio": {
      "value": 4.85,
      "status": 1,
      "his": {"low": 2.5, "high": 7.5, "med": 5.0},
      "indu": {"global_rank": 1672, "indu_med": 4.72, "indu_tot": 1614}
    },
    "ps_ratio": {
      "value": 2.55,
      "status": 1,
      "his": {"low": 1.5, "high": 4.5, "med": 3.0},
      "indu": {"global_rank": 1951, "indu_med": 2.77, "indu_tot": 1055}
    },
    "current_ratio": {
      "value": 1.32,
      "status": 1,
      "his": {"low": 0.6, "high": 1.8, "med": 1.2},
      "indu": {"global_rank": 1904, "indu_med": 1.19, "indu_tot": 2987}
    },
    "quick_ratio": {
      "value": 1.05,
      "status": 0,
      "his": {"low": 0.45, "high": 1.35, "med": 0.9},
      "indu": {"global_rank": 1018, "indu_med": 0.98, "indu_tot": 1227}
    },
    "cash_ratio": {
      "value": 0.27,
      "status": 1,
      "his": {"low": 0.17, "high": 0.49, "med": 0.33},
      "indu": {"global_rank": 260, "indu_med": 0.3, "indu_tot": 2932}
    },
    "piotroski_score": {
      "value": 6,
      "status": 0,
      "his": {"low": 3.0, "high": 10.0, "med": 7.0},
      "indu": {"global_rank": 1142, "indu_med": 6.57, "indu_tot": 2677}
    }
  },
  "institutional": {
    "guru_buys_pct": 61.2,
    "guru_sells_pct": 1.7,
    "guru_holds_pct": 44.72,
    "fund_buys_pct": 94.18,
    "fund_sells_pct": 54.48,
    "etf_buys_pct": 28.95,
    "etf_sells_pct": 14.76
  }
}
```

**Note:** The response uses `model_dump(mode="json", exclude_none=True)`, so any `null` values are automatically excluded from the response.

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": true,
  "error_type": "error_category",
  "message": "Human-readable error message",
  "details": {},
  "suggestions": ["Helpful suggestion 1", "Helpful suggestion 2"]
}
```

**Error Types:**
- `invalid_input`: Invalid parameter value (e.g., bad symbol format)
- `invalid_symbol`: Stock symbol not found
- `authentication_error`: API token issue
- `rate_limit`: Rate limit exceeded
- `not_found`: Resource not found
- `network_error`: Connection issue
- `timeout`: Request timed out
- `api_error`: General API error

---

## Configuration

The server is configured via environment variables:

| Variable                       | Default                                 | Description                      |
| ------------------------------ | --------------------------------------- | -------------------------------- |
| `GURUFOCUS_API_TOKEN`          | (required)                              | GuruFocus API token              |
| `GURUFOCUS_API_BASE_URL`       | `https://api.gurufocus.com/public/user` | API base URL                     |
| `GURUFOCUS_API_TIMEOUT`        | `30.0`                                  | Request timeout in seconds       |
| `GURUFOCUS_CACHE_ENABLED`      | `true`                                  | Enable response caching          |
| `GURUFOCUS_CACHE_DIR`          | `.cache/gurufocus-mcp`                  | Cache directory                  |
| `GURUFOCUS_RATE_LIMIT_ENABLED` | `true`                                  | Enable rate limiting             |
| `GURUFOCUS_RATE_LIMIT_RPM`     | `30.0`                                  | Max requests per minute          |
| `GURUFOCUS_LOG_LEVEL`          | `INFO`                                  | Logging level                    |
| `GURUFOCUS_LOG_FORMAT`         | `console`                               | Log format (`console` or `json`) |
