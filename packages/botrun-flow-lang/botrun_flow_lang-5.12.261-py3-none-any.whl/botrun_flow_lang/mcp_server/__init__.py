"""
MCP Server module for BotrunFlowLang

This module provides MCP (Model Context Protocol) server implementation
that exposes tools for LangGraph agents.
"""

from .default_mcp import mcp

__all__ = ["mcp"]
