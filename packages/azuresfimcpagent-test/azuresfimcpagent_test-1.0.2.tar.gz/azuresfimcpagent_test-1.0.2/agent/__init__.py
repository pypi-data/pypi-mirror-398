"""Azure SFI Agent - MCP Server for Azure resource deployment with compliance orchestration."""

__version__ = "1.0.0"
__author__ = "Azure SFI Agent Contributors"
__description__ = "Interactive Azure deployment with automatic NSP and Log Analytics orchestration"

from agent.server import mcp, main

__all__ = ["mcp", "main", "__version__"]
