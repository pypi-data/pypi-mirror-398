"""MCP Prompts for GuruFocus.

Prompts are user-controlled templates for guided interactions.
"""

from fastmcp import FastMCP

from .analysis import register_prompts as register_analysis_prompts


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts.

    Args:
        mcp: FastMCP server instance
    """
    register_analysis_prompts(mcp)
