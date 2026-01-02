"""MCP Tools for GuruFocus data.

Tools are model-controlled functions that allow LLMs to fetch financial data.
"""

from .analysis import register_analysis_tools
from .insiders import register_insider_tools
from .stocks import register_stock_tools

__all__ = ["register_analysis_tools", "register_insider_tools", "register_stock_tools"]
