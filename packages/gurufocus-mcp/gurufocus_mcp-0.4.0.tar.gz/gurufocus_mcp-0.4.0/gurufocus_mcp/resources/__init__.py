"""MCP Resources for GuruFocus data.

Resources are application-controlled contextual data (schemas, documentation).
"""

from .stocks import register_stock_resources

__all__ = ["register_stock_resources"]
