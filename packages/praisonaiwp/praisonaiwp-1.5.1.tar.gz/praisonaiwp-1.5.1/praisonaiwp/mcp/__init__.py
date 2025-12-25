"""
MCP (Model Context Protocol) integration for PraisonAIWP

This module provides MCP server functionality to expose WordPress operations
to MCP-compatible clients like Claude Desktop, Cursor, VS Code, etc.
"""

from praisonaiwp.mcp.server import get_wp_client, mcp

__all__ = [
    "mcp",
    "get_wp_client",
]
