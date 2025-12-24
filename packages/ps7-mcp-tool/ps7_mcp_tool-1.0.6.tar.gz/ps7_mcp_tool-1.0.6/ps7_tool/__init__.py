"""
PS7 Tool - PowerShell 7 MCP Server for Zencoder

A custom MCP (Model Context Protocol) server that exposes PowerShell 7 
command execution to Zencoder, bypassing shell limitations.
"""

__version__ = "1.0.0"
__author__ = "Nomad"
__title__ = "ps7-mcp-tool"

from .mcp_server import PS7MCPServer, MCPProtocol

__all__ = ["PS7MCPServer", "MCPProtocol"]
