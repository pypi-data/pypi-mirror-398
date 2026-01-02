"""Insider activity MCP tools.

Tools for fetching insider trading signals from GuruFocus API.
"""

from typing import Annotated, Any, cast

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from gurufocus_api.logging import get_logger

from ..errors import raise_api_error
from ..formatting import OutputFormat, format_output

logger = get_logger(__name__)


def register_insider_tools(mcp: FastMCP) -> None:
    """Register insider activity tools with the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools with.
    """

    @mcp.tool
    async def get_insider_updates(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get recent insider transaction updates.

        Returns a list of recent insider transactions filed with the SEC:
        - symbol: Stock ticker
        - insider: Name of the insider
        - position: Insider's role (CEO, Director, etc.)
        - type: Transaction type - 'P' (Purchase) or 'S' (Sell)
        - trans_share: Number of shares transacted
        - price: Transaction price per share
        - date: Transaction date
        - file_date: SEC filing date

        Use this tool to monitor recent insider buying and selling activity
        across all stocks. High insider buying can be a bullish signal.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug("get_insider_updates_called", page=page, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            updates = await client.insiders.get_updates(page=page)
            data = cast(dict[str, Any], updates.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_updates_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_updates_error", page=page, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_insider_ceo_buys(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        within_days: Annotated[
            int | None,
            Field(default=None, description="Filter to transactions within N days"),
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
        """Get stocks where CEOs are buying shares.

        Returns paginated list of CEO buy transactions - a strong bullish signal:
        - symbol: Stock ticker
        - company: Company name
        - name: CEO name
        - trans_share: Shares purchased
        - trade_price: Purchase price
        - cost: Total transaction cost
        - shares_change: Percentage change in holdings
        - change_from_insider_trade: Stock price change since purchase

        CEO buying is often considered one of the most bullish insider signals
        as CEOs have the deepest knowledge of their company's prospects.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug(
            "get_insider_ceo_buys_called", page=page, within_days=within_days, format=format
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            ceo_buys = await client.insiders.get_ceo_buys(page=page, within_days=within_days)
            data = cast(dict[str, Any], ceo_buys.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_ceo_buys_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_ceo_buys_error", page=page, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_insider_cfo_buys(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        within_days: Annotated[
            int | None,
            Field(default=None, description="Filter to transactions within N days"),
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
        """Get stocks where CFOs are buying shares.

        Returns paginated list of CFO buy transactions - a bullish signal:
        - symbol: Stock ticker
        - company: Company name
        - name: CFO name
        - trans_share: Shares purchased
        - trade_price: Purchase price
        - cost: Total transaction cost
        - shares_change: Percentage change in holdings

        CFO buying is a significant signal as CFOs have detailed knowledge
        of the company's financial position and future outlook.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug(
            "get_insider_cfo_buys_called", page=page, within_days=within_days, format=format
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            cfo_buys = await client.insiders.get_cfo_buys(page=page, within_days=within_days)
            data = cast(dict[str, Any], cfo_buys.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_cfo_buys_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_cfo_buys_error", page=page, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_insider_cluster_buys(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        within_days: Annotated[
            int | None,
            Field(default=None, description="Filter to transactions within N days"),
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
        """Get stocks with cluster insider buying.

        Returns stocks where multiple insiders are buying - a very bullish signal:
        - symbol: Stock ticker
        - company: Company name
        - insider_buy_count: Total insider buy transactions
        - insider_buy_count_unique: Number of unique insiders buying
        - buy_total_shares: Total shares purchased
        - buy_price_avg: Average purchase price
        - buy_price_value: Total value of purchases
        - buy_company_held_shares: Percentage of company shares held by insiders

        Cluster buying occurs when multiple insiders buy around the same time,
        which is one of the strongest bullish signals from insider activity.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug(
            "get_insider_cluster_buys_called", page=page, within_days=within_days, format=format
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            cluster = await client.insiders.get_cluster_buys(page=page, within_days=within_days)
            data = cast(dict[str, Any], cluster.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_cluster_buys_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_cluster_buys_error", page=page, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_insider_double_buys(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        within_days: Annotated[
            int | None,
            Field(default=None, description="Filter to transactions within N days"),
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
        """Get stocks with double-down insider buying.

        Returns stocks where insiders are doubling down on purchases:
        - symbol: Stock ticker
        - company: Company name
        - buy_add_count: Number of additional buy transactions
        - insider_buy_count: Total insider buy transactions
        - insider_buy_shares: Total shares purchased

        Double-down buying indicates insiders are adding to existing positions,
        showing continued conviction in the stock.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug(
            "get_insider_double_buys_called", page=page, within_days=within_days, format=format
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            double = await client.insiders.get_double_buys(page=page, within_days=within_days)
            data = cast(dict[str, Any], double.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_double_buys_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_double_buys_error", page=page, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_insider_triple_buys(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        within_days: Annotated[
            int | None,
            Field(default=None, description="Filter to transactions within N days"),
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
        """Get stocks with triple-down insider buying.

        Returns stocks where insiders have made multiple additional purchases:
        - symbol: Stock ticker
        - company: Company name
        - buy_add_count: Number of additional buy transactions
        - insider_buy_count: Total insider buy transactions
        - total_buyback_1y: Company's total buyback in past year (%)

        Triple-down buying is an even stronger signal than double-down,
        indicating very high insider conviction in the stock.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug(
            "get_insider_triple_buys_called", page=page, within_days=within_days, format=format
        )

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            triple = await client.insiders.get_triple_buys(page=page, within_days=within_days)
            data = cast(dict[str, Any], triple.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_triple_buys_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_triple_buys_error", page=page, error=str(e))
            raise_api_error(e)

    @mcp.tool
    async def get_insider_list(
        page: Annotated[
            int,
            Field(default=1, description="Page number for paginated results"),
        ] = 1,
        format: Annotated[
            OutputFormat,
            Field(
                default="toon",
                description="Output format: 'toon' (default, token-efficient) or 'json' (standard)",
            ),
        ] = "toon",
        ctx: Context = None,  # type: ignore[assignment]
    ) -> str | dict[str, Any]:
        """Get list of known company insiders.

        Returns paginated list of insiders in the database:
        - cik: SEC CIK identifier
        - name: Insider's name
        - address: Mailing address (may be empty)
        - latest_transaction_date: Date of most recent transaction
        - companies: List of stock symbols associated with the insider

        Use this tool to look up information about specific insiders
        or to browse the insider database.

        The 'format' parameter controls output encoding:
        - 'toon': Token-efficient format (30-60% smaller), recommended for AI contexts
        - 'json': Standard JSON format for debugging or compatibility
        """
        logger.debug("get_insider_list_called", page=page, format=format)

        try:
            client = getattr(ctx.fastmcp, "state", {}).get("client")
            if client is None:
                raise ToolError(
                    "GuruFocus client not initialized. "
                    "Please ensure GURUFOCUS_API_TOKEN environment variable is set."
                )

            insiders = await client.insiders.get_list(page=page)
            data = cast(dict[str, Any], insiders.model_dump(mode="json", exclude_none=True))
            logger.debug("get_insider_list_success", page=page, format=format)
            return format_output(data, format)

        except ToolError:
            raise
        except Exception as e:
            logger.error("get_insider_list_error", page=page, error=str(e))
            raise_api_error(e)
