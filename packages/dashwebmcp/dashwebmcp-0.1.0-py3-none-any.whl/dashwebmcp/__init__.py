"""
DashWebMCP - MCP Bridge for Dash Applications

Expose any Dash application as an MCP (Model Context Protocol) server,
allowing AI agents to interact with your dashboards.

Features:
- WebSocket bridge between browser tabs and MCP server
- Automatic tool registration from browser pages
- Built-in UI interaction tools (click, setValue, getText, etc.)
- Custom tool registration via JavaScript API
- Human-in-the-loop confirmation support

Quick Start:
    from dashwebmcp import MCPRelay, create_mcp_routes, mcp_lifespan

    # Create relay
    mcp_relay = MCPRelay()

    # Add routes to your ASGI app
    routes = create_mcp_routes(mcp_relay)

    # Use lifespan for proper startup/shutdown
    async with mcp_lifespan(app, mcp_relay):
        ...

Client-side (JavaScript):
    // Register custom tool
    window.DashMCP.registerTool('getData', {
        description: 'Get dashboard data',
        inputSchema: { type: 'object', properties: {} },
        annotations: { readOnly: true }
    }, async (args) => {
        return { data: [...] };
    });

For more information, see:
https://github.com/Cemberk/dashwebmcp
"""

from dashwebmcp.relay import (
    MCPRelay,
    BrowserSession,
    create_mcp_routes,
    mcp_lifespan,
    websocket_bridge,
    SESSIONS,
    MCP_AVAILABLE,
    ALLOWED_ORIGINS,
    get_js_bridge_path,
    get_js_bridge_content,
)

__version__ = "0.1.0"
__all__ = [
    "MCPRelay",
    "BrowserSession",
    "create_mcp_routes",
    "mcp_lifespan",
    "websocket_bridge",
    "SESSIONS",
    "MCP_AVAILABLE",
    "ALLOWED_ORIGINS",
    "get_js_bridge_path",
    "get_js_bridge_content",
]
