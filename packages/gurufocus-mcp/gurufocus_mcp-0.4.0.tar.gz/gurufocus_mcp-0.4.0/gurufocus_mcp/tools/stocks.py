"""Stock-related MCP tools.

Tools for fetching stock financial data from GuruFocus API.
"""

from typing import Annotated, Any, Literal, cast

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from gurufocus_api.logging import get_logger

from ..errors import raise_api_error, validate_symbol
from ..formatting import OutputFormat, format_output

logger = get_logger(__name__)


def register_stock_tools(mcp: FastMCP) -> None:
    """Register stock-related tools with the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools with.
    """

    @mcp.tool
    async def get_stock_summary(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get comprehensive financial summary for a stock.

        Returns structured data including:
        - Company info: name, sector, industry, market cap, description
        - Current price and daily change percentage
        - Quality scores: GF Score, financial strength, profitability rank, growth rank
        - Valuation metrics: P/E, P/B, P/S ratios, GF Value, DCF estimates
        - Financial ratios with 5/10-year averages and industry medians
        - Institutional activity: guru and fund buying/selling percentages

        Use this tool when you need to analyze a stock's fundamentals,
        valuation, or financial health.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_summary_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            summary = await client.stocks.get_summary(normalized)
            data = cast(dict[str, Any], summary.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_summary_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_summary_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_quote(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get real-time stock quote data.

        Returns current market data for a stock:
        - current_price: Current trading price
        - price_change: Absolute price change from previous close
        - price_change_pct: Percentage change from previous close
        - open, high, low: Daily OHLV data
        - volume: Trading volume for the day
        - exchange: Stock exchange (NAS, NYSE, etc.)
        - currency: Price currency (USD, EUR, etc.)

        This is a lightweight alternative to get_stock_summary when you only
        need current price and daily trading data, not full fundamental analysis.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_quote_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            quote = await client.stocks.get_quote(normalized)
            data = cast(dict[str, Any], quote.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_quote_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_quote_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_dividend(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get dividend history for a stock.

        Returns historical dividend payment data:
        - payments: Array of historical dividend payments
          - ex_date: Ex-dividend date
          - pay_date: Payment date
          - record_date: Record date
          - amount: Dividend amount per share
          - type: Dividend type (regular, special, etc.)
          - frequency: Payment frequency (quarterly, annual, etc.)

        Use this tool when you need to analyze a stock's dividend history,
        track payout trends, or evaluate income potential.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_dividend_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            dividends = await client.stocks.get_dividends(normalized)
            data = cast(dict[str, Any], dividends.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_dividend_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_dividend_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_current_dividend(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get current dividend information for a stock.

        Returns current dividend data including:
        - dividend_yield: Current dividend yield percentage
        - dividends_per_share_ttm: Trailing twelve months dividend per share
        - dividend_yield_10y_range: 10-year historical yield range
        - dividend_yield_10y_median: 10-year median dividend yield
        - next_payment_date: Next scheduled dividend payment date
        - frequency: Payment frequency (Quarterly, Annual, etc.)
        - currency: Currency symbol

        Use this tool when you need to analyze a stock's current dividend
        yield, compare it to historical ranges, or check payment schedule.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_current_dividend_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            current_div = await client.stocks.get_current_dividend(normalized)
            data = cast(dict[str, Any], current_div.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_current_dividend_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_current_dividend_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_financials(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        period_type: Annotated[
            Literal["annual", "quarterly"],
            Field(
                default="annual",
                description="Financial period type: 'annual' for yearly data or 'quarterly' for quarterly data",
            ),
        ] = "annual",
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get financial statements for a stock.

        Returns historical financial data including:
        - Per-share metrics: revenue per share, EPS, book value per share, FCF per share
        - Income statement: revenue, gross profit, operating income, net income, EBITDA
        - Balance sheet: total assets, liabilities, equity, debt, cash
        - Cash flow: operating cash flow, capex, free cash flow, dividends paid
        - Margins: gross margin, operating margin, net margin

        Data is organized by fiscal period (most recent first) with both annual
        and quarterly options available.

        Use this tool when you need to analyze a company's financial performance
        over time, track revenue/earnings trends, or evaluate balance sheet health.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug(
            "get_stock_financials_called",
            symbol=normalized,
            period_type=period_type,
            format=format,
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            financials = await client.stocks.get_financials(normalized, period_type=period_type)
            data = cast(dict[str, Any], financials.model_dump(mode="json", exclude_none=True))
            logger.debug(
                "get_stock_financials_success",
                symbol=normalized,
                period_type=period_type,
                format=format,
            )
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_financials_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_keyratios(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get key financial ratios for a stock.

        Returns comprehensive financial ratios organized by category:
        - Quality scores: Piotroski F-Score, Altman Z-Score, GF Score, financial strength
        - Profitability: ROE, ROA, ROIC, gross/operating/net margins
        - Liquidity: current ratio, quick ratio, cash ratio
        - Solvency: debt-to-equity, debt-to-asset, interest coverage
        - Efficiency: asset turnover, inventory turnover, days sales outstanding
        - Growth: 1/3/5/10-year revenue, EPS, and FCF growth rates
        - Valuation: P/E, P/B, P/S, PEG, EV/EBITDA, GF Value
        - Price metrics: 52-week high/low, beta, volatility, returns
        - Dividends: yield, payout ratio, growth rates, years of consecutive growth

        Use this tool when you need to evaluate a company's financial health,
        compare it to peers, or assess investment quality across multiple dimensions.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_keyratios_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            keyratios = await client.stocks.get_keyratios(normalized)
            data = cast(dict[str, Any], keyratios.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_keyratios_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_keyratios_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_gurus(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get guru (institutional investor) holdings for a stock.

        Returns data about famous investors who hold positions in this stock:
        - Picks: Recent trading activity including buys, sells, and position changes
          - guru: Investor/firm name (e.g., Warren Buffett, BlackRock)
          - action: Trade type (Add, Reduce, New Buy, Sold Out)
          - impact: Position impact percentage
          - price range: Min/max/avg prices during the period
          - current_shares: Shares held after the action
        - Holdings: Current guru positions
          - current_shares: Number of shares held
          - perc_shares: Percentage of company shares owned
          - perc_assets: Percentage of guru's portfolio
          - change: Position change percentage

        Use this tool when you need to see which famous investors own a stock,
        track guru buying/selling activity, or follow institutional investor trends.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_gurus_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            gurus = await client.stocks.get_gurus(normalized)
            data = cast(dict[str, Any], gurus.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_gurus_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_gurus_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_executives(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get company executives and directors for a stock.

        Returns a list of company officers and board members:
        - name: Executive name
        - position: Title/role (e.g., 'director, officer: Chief Executive Officer')
        - transaction_date: Date of last insider transaction

        Use this tool when you need to identify company leadership,
        check insider trading activity, or understand corporate governance.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_executives_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            executives = await client.stocks.get_executives(normalized)
            data = cast(dict[str, Any], executives.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_executives_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_executives_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_trades_history(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get guru trades history for a stock.

        Returns historical guru trading activity organized by portfolio
        reporting periods:
        - periods: Array of trading activity by date
          - portdate: Portfolio reporting date (YYYY-MM-DD)
          - buy_count: Number of gurus who bought
          - buy_gurus: List of buyers with guru_name and share_change
          - sell_count: Number of gurus who sold
          - sell_gurus: List of sellers with guru_name and share_change

        Use this tool when you need to track guru buying/selling patterns
        over time or identify periods of institutional accumulation/distribution.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug("get_stock_trades_history_called", symbol=normalized, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            trades = await client.stocks.get_trades_history(normalized)
            data = cast(dict[str, Any], trades.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_trades_history_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_trades_history_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_price_ohlc(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        start_date: Annotated[
            str | None,
            Field(
                default=None,
                description="Start date in YYYYMMDD format (e.g., 20250101). If not provided, returns all available data.",
            ),
        ] = None,
        end_date: Annotated[
            str | None,
            Field(
                default=None,
                description="End date in YYYYMMDD format (e.g., 20251231). If not provided, returns up to current date.",
            ),
        ] = None,
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get OHLC (Open-High-Low-Close) price history for a stock.

        Returns daily OHLC price bars with volume data:
        - bars: Array of daily price bars
          - date: Trading date (YYYY-MM-DD)
          - open: Opening price
          - high: Highest price of the day
          - low: Lowest price of the day
          - close: Closing price
          - volume: Trading volume
          - unadjusted_close: Unadjusted closing price

        Use this tool when you need historical candlestick/OHLC data for
        technical analysis, charting, or computing price-based indicators.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug(
            "get_stock_price_ohlc_called",
            symbol=normalized,
            start_date=start_date,
            end_date=end_date,
            format=format,
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            ohlc = await client.stocks.get_price_ohlc(
                normalized, start_date=start_date, end_date=end_date
            )
            data = cast(dict[str, Any], ohlc.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_price_ohlc_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_price_ohlc_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_volume(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        start_date: Annotated[
            str | None,
            Field(
                default=None,
                description="Start date in YYYYMMDD format (e.g., 20250101). If not provided, returns all available data.",
            ),
        ] = None,
        end_date: Annotated[
            str | None,
            Field(
                default=None,
                description="End date in YYYYMMDD format (e.g., 20251231). If not provided, returns up to current date.",
            ),
        ] = None,
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get trading volume history for a stock.

        Returns daily trading volume data:
        - data: Array of daily volume points
          - date: Trading date (MM-DD-YYYY)
          - volume: Number of shares traded

        Use this tool when you need to analyze volume patterns,
        identify accumulation/distribution, or study liquidity trends.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug(
            "get_stock_volume_called",
            symbol=normalized,
            start_date=start_date,
            end_date=end_date,
            format=format,
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            volume = await client.stocks.get_volume(
                normalized, start_date=start_date, end_date=end_date
            )
            data = cast(dict[str, Any], volume.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_volume_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_volume_error", symbol=normalized, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_stock_unadjusted_price(
        symbol: Annotated[
            str,
            Field(description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"),
        ],
        start_date: Annotated[
            str | None,
            Field(
                default=None,
                description="Start date in YYYYMMDD format (e.g., 20250101). If not provided, returns all available data.",
            ),
        ] = None,
        end_date: Annotated[
            str | None,
            Field(
                default=None,
                description="End date in YYYYMMDD format (e.g., 20251231). If not provided, returns up to current date.",
            ),
        ] = None,
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get unadjusted (pre-split) price history for a stock.

        Returns daily unadjusted prices:
        - prices: Array of daily price points
          - date: Trading date (MM-DD-YYYY)
          - price: Unadjusted closing price

        Unadjusted prices show the actual historical trading prices without
        adjustments for stock splits or dividends. Use this when you need
        to see the actual price investors paid at a given time, or to
        compare with historical news/events.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        normalized = validate_symbol(symbol)
        if not normalized:
            raise ToolError(
                f"Invalid symbol format: '{symbol}'. "
                "Please provide a valid stock ticker symbol (e.g., AAPL, MSFT)."
            )

        logger.debug(
            "get_stock_unadjusted_price_called",
            symbol=normalized,
            start_date=start_date,
            end_date=end_date,
            format=format,
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            prices = await client.stocks.get_unadjusted_price(
                normalized, start_date=start_date, end_date=end_date
            )
            data = cast(dict[str, Any], prices.model_dump(mode="json", exclude_none=True))
            logger.debug("get_stock_unadjusted_price_success", symbol=normalized, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_stock_unadjusted_price_error", symbol=normalized, error=str(e))
            raise_api_error(e)
