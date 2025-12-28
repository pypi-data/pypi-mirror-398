"""Azure SFI Agent - MCP Server for Azure resource deployment with compliance orchestration."""

__version__ = "1.0.0"
__author__ = "Azure SFI Agent Contributors"
__description__ = "Interactive Azure deployment with automatic NSP and Log Analytics orchestration"

from agent.server import mcp, main

# Import all tool modules to register them with the MCP server
from agent import azure_tools, ado_tools, fabric_tools

__all__ = ["mcp", "main", "__version__"]

# Allow running as: python -m agent
if __name__ == "__main__":
    main()
