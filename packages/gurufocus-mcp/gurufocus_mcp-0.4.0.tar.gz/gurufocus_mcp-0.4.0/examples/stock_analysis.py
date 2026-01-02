#!/usr/bin/env python3
"""Stock analysis workflow example.

This example demonstrates how to use the GuruFocus MCP server
for stock analysis workflows, including calling tools and
working with the responses.

Note: This example calls actual API endpoints, so you need a
valid GURUFOCUS_API_TOKEN.
"""

import asyncio
import json
import os

from fastmcp.client import Client

from gurufocus_mcp import create_server
from gurufocus_mcp.config import MCPServerSettings


async def analyze_stock(client: Client, symbol: str) -> None:
    """Perform a comprehensive stock analysis."""
    print(f"\n{'=' * 60}")
    print(f"Analyzing: {symbol}")
    print("=" * 60)

    # Call get_stock_summary tool
    print("\n--- Stock Summary ---")
    result = await client.call_tool("get_stock_summary", {"symbol": symbol})

    # Parse the result
    if result:
        for content in result:
            if hasattr(content, "text"):
                data = json.loads(content.text)
                if "error" in data:
                    print(f"Error: {data.get('message', 'Unknown error')}")
                    return

                print(f"Company: {data.get('company_name')}")
                print(f"Exchange: {data.get('exchange')}")
                print(f"Sector: {data.get('sector')}")
                print(f"Industry: {data.get('industry')}")
                print(f"Market Cap: ${data.get('market_cap', 0):,.0f}")

                if "price" in data:
                    price = data["price"]
                    print(f"Price: ${price.get('current', 0):.2f}")
                    print(f"Change: {price.get('change_pct', 0):.2f}%")

                if "gf_score" in data:
                    gf = data["gf_score"]
                    print(f"\nGF Score: {gf.get('score')}/100")
                    print(f"  Financial Strength: {gf.get('financial_strength')}/10")
                    print(f"  Profitability Rank: {gf.get('profitability_rank')}/10")
                    print(f"  Growth Rank: {gf.get('growth_rank')}/10")


async def compare_stocks(client: Client, symbols: list[str]) -> None:
    """Compare multiple stocks side by side."""
    print(f"\n{'=' * 60}")
    print(f"Comparing: {', '.join(symbols)}")
    print("=" * 60)

    result = await client.call_tool("compare_stocks", {"symbols": symbols})

    if result:
        for content in result:
            if hasattr(content, "text"):
                data = json.loads(content.text)
                if "error" in data:
                    print(f"Error: {data.get('message', 'Unknown error')}")
                    return

                print(f"\nComparing {data.get('comparison_count')} stocks:\n")

                # Print header
                print(f"{'Symbol':<8} {'Company':<25} {'GF Score':>10} {'P/E':>8} {'Sector':<15}")
                print("-" * 70)

                for stock in data.get("stocks", []):
                    if "error" in stock:
                        print(f"{stock['symbol']:<8} Error: {stock['error']}")
                    else:
                        print(
                            f"{stock.get('symbol', 'N/A'):<8} "
                            f"{(stock.get('company_name') or 'N/A')[:25]:<25} "
                            f"{stock.get('gf_score') or 'N/A':>10} "
                            f"{stock.get('pe_ratio') or 'N/A':>8} "
                            f"{(stock.get('sector') or 'N/A')[:15]:<15}"
                        )


async def screen_quality_stocks(client: Client) -> None:
    """Screen for high-quality stocks."""
    print(f"\n{'=' * 60}")
    print("Screening for Quality Stocks")
    print("=" * 60)

    result = await client.call_tool("screen_stocks", {"screen_type": "quality", "limit": 10})

    if result:
        for content in result:
            if hasattr(content, "text"):
                data = json.loads(content.text)
                if "error" in data:
                    print(f"Error: {data.get('message', 'Unknown error')}")
                    return

                print(f"\nScreen Type: {data.get('screen_type')}")
                print(f"Criteria: {json.dumps(data.get('criteria', {}), indent=2)}")
                print(f"Total Matches: {data.get('total_matches')}")
                print(f"\nTop {len(data.get('stocks', []))} Results:\n")

                print(f"{'Symbol':<8} {'Company':<30} {'GF Score':>10} {'P/E':>8}")
                print("-" * 60)

                for stock in data.get("stocks", []):
                    print(
                        f"{stock.get('symbol', 'N/A'):<8} "
                        f"{(stock.get('company_name') or 'N/A')[:30]:<30} "
                        f"{stock.get('gf_score') or 'N/A':>10} "
                        f"{stock.get('pe_ratio') or 'N/A':>8}"
                    )


async def main():
    """Run stock analysis examples."""
    api_token = os.getenv("GURUFOCUS_API_TOKEN")
    if not api_token:
        print("Please set GURUFOCUS_API_TOKEN environment variable")
        print("\nExample:")
        print("  export GURUFOCUS_API_TOKEN=your-token-here")
        print("  python stock_analysis.py")
        return

    settings = MCPServerSettings(api_token=api_token)
    server = create_server(settings)

    async with Client(server) as client:
        print("GuruFocus MCP Stock Analysis Examples")
        print("=" * 60)

        # Example 1: Analyze a single stock
        await analyze_stock(client, "AAPL")

        # Example 2: Compare multiple stocks
        await compare_stocks(client, ["AAPL", "MSFT", "GOOGL"])

        # Example 3: Screen for quality stocks
        await screen_quality_stocks(client)

        print("\n" + "=" * 60)
        print("Analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
