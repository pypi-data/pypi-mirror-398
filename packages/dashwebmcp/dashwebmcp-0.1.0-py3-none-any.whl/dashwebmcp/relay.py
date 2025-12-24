"""
MCP Relay Server for Dash Applications

Implements a "UI-only MCP relay" pattern where:
- Server exposes MCP Streamable HTTP endpoint
- Tool execution happens in browser tabs via WebSocket
- Each browser tab registers its available tools dynamically
- Server acts as a relay - no business logic

Security:
- Server never runs tool logic directly
- Tools can only do what the UI already has access to
- Origin validation for WebSocket connections
- Optional human-in-the-loop confirmation
"""

import asyncio
import contextlib
import json
import secrets
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime

# MCP SDK imports (optional - graceful fallback if not installed)
try:
    import mcp.types as mcp_types
    from mcp.server.lowlevel import Server as MCPServer
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    mcp_types = None
    MCPServer = None
    StreamableHTTPSessionManager = None


# =============================================================================
# BROWSER SESSION MANAGEMENT
# =============================================================================

@dataclass
class BrowserSession:
    """
    Represents a connected browser tab with its registered tools.

    Attributes:
        sid: Unique session ID for this browser tab
        ws: WebSocket connection (from Starlette)
        tools: Registered tools from this tab {name: {description, inputSchema, annotations}}
        pending: Pending tool calls waiting for browser response {call_id: Future}
        page_url: Current page URL in the browser tab
        view_id: Current view ID (if on a view page)
        connected_at: When this session connected
    """
    sid: str
    ws: Any  # WebSocket from Starlette
    tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pending: Dict[str, asyncio.Future] = field(default_factory=dict)
    page_url: str = ""
    view_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)


# Global session registry
SESSIONS: Dict[str, BrowserSession] = {}


def _generate_call_id() -> str:
    """Generate unique ID for tool calls."""
    return secrets.token_urlsafe(12)


async def _call_browser_tool(
    sid: str,
    tool_name: str,
    args: Dict[str, Any],
    timeout_s: float = 30.0
) -> Dict[str, Any]:
    """
    Forward a tool call to a browser session and wait for result.

    Args:
        sid: Browser session ID
        tool_name: Name of the tool to call
        args: Arguments to pass to the tool
        timeout_s: Timeout in seconds

    Returns:
        Tool result from browser

    Raises:
        RuntimeError: If session not found or tool call fails
    """
    sess = SESSIONS.get(sid)
    if not sess:
        raise RuntimeError(f"No active browser session for sid={sid}")

    call_id = _generate_call_id()
    fut: asyncio.Future = asyncio.get_event_loop().create_future()
    sess.pending[call_id] = fut

    # Send tool call request to browser
    await sess.ws.send_text(json.dumps({
        "type": "call",
        "sid": sid,
        "call_id": call_id,
        "tool": tool_name,
        "args": args or {},
    }))

    try:
        result = await asyncio.wait_for(fut, timeout=timeout_s)
        return result
    except asyncio.TimeoutError:
        raise RuntimeError(f"Tool call timed out after {timeout_s}s: {tool_name}")
    finally:
        sess.pending.pop(call_id, None)


# =============================================================================
# MCP SERVER IMPLEMENTATION
# =============================================================================

class MCPRelay:
    """
    MCP Server that relays tool calls to browser tabs.

    This class manages the MCP server and coordinates tool calls between
    AI agents and browser-side tool implementations.
    """

    def __init__(self, app_name: str = "dash-web-mcp"):
        self.app_name = app_name
        self.mcp_app = None
        self.session_manager = None
        self._tools_changed_callbacks: List[Callable] = []

        if MCP_AVAILABLE:
            self._setup_mcp_server()

    def _setup_mcp_server(self):
        """Initialize MCP server with tool handlers."""
        self.mcp_app = MCPServer(self.app_name)

        # Register tool list handler
        @self.mcp_app.list_tools()
        async def list_tools() -> list:
            return self._list_all_tools()

        # Register tool call handler
        @self.mcp_app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            return await self._call_tool(name, arguments)

        # Create session manager for Streamable HTTP
        self.session_manager = StreamableHTTPSessionManager(
            app=self.mcp_app,
            event_store=None,
            json_response=True,
            stateless=True,  # Stateless mode for simpler deployment
        )

    def _list_all_tools(self) -> list:
        """
        Build the complete tool list from all browser sessions.

        Returns tools in format:
        - dash.sessions.list: List active browser sessions
        - dash.<sid>.<tool>: Tools registered by each browser session
        """
        if not MCP_AVAILABLE:
            return []

        tools = []

        # Built-in: List active sessions
        tools.append(
            mcp_types.Tool(
                name="dash.sessions.list",
                description="List active browser sessions and their registered tools. Use this first to discover available sessions.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                },
            )
        )

        # Per-session tools
        for sid, sess in SESSIONS.items():
            for tool_name, meta in sess.tools.items():
                tools.append(
                    mcp_types.Tool(
                        name=f"dash.{sid}.{tool_name}",
                        description=self._build_tool_description(sess, tool_name, meta),
                        inputSchema=meta.get("inputSchema") or {"type": "object", "properties": {}},
                    )
                )

        return tools

    def _build_tool_description(self, sess: BrowserSession, tool_name: str, meta: dict) -> str:
        """Build tool description with context."""
        desc = str(meta.get("description") or tool_name)

        # Add page context if available
        if sess.page_url:
            desc += f"\n\n[Page: {sess.page_url}]"
        if sess.view_id:
            desc += f"\n[View: {sess.view_id}]"

        return desc

    async def _call_tool(self, name: str, arguments: Dict[str, Any]):
        """
        Handle tool calls from MCP clients.

        Args:
            name: Tool name in format "dash.<sid>.<tool>" or "dash.sessions.list"
            arguments: Tool arguments

        Returns:
            MCP CallToolResult
        """
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP SDK not installed")

        # Built-in: List sessions
        if name == "dash.sessions.list":
            payload = {
                "sessions": [
                    {
                        "sid": sid,
                        "page_url": sess.page_url,
                        "view_id": sess.view_id,
                        "tool_count": len(sess.tools),
                        "tools": sorted(sess.tools.keys()),
                        "connected_at": sess.connected_at.isoformat(),
                    }
                    for sid, sess in SESSIONS.items()
                ]
            }
            return mcp_types.CallToolResult(
                content=[mcp_types.TextContent(type="text", text=json.dumps(payload, indent=2))],
                structuredContent=payload,
            )

        # Parse tool name: dash.<sid>.<tool>
        if not name.startswith("dash."):
            raise ValueError(f"Unknown tool: {name}. Expected format: dash.<sid>.<tool>")

        parts = name.split(".", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid tool name format: {name}. Expected: dash.<sid>.<tool>")

        _, sid, tool_name = parts

        # Find session
        sess = SESSIONS.get(sid)
        if not sess:
            raise RuntimeError(f"Browser session not found: {sid}. Call dash.sessions.list to see active sessions.")

        # Verify tool exists
        if tool_name not in sess.tools:
            raise ValueError(
                f"Tool '{tool_name}' not found in session {sid}. "
                f"Available tools: {', '.join(sorted(sess.tools.keys()))}"
            )

        # Forward to browser and wait for result
        result = await _call_browser_tool(sid, tool_name, arguments or {})

        # Normalize result to MCP format
        text = ""
        structured = None

        if isinstance(result, dict):
            if "text" in result or "structured" in result:
                text = str(result.get("text") or "")
                structured = result.get("structured")
            elif "error" in result:
                text = f"Error: {result.get('error')}"
                structured = result
            else:
                structured = result
                text = json.dumps(result, indent=2, default=str)
        elif isinstance(result, str):
            text = result
        else:
            text = json.dumps(result, indent=2, default=str)
            structured = result

        return mcp_types.CallToolResult(
            content=[mcp_types.TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    def on_tools_changed(self, callback: Callable):
        """Register callback for when tool list changes."""
        self._tools_changed_callbacks.append(callback)

    def _notify_tools_changed(self):
        """Notify that tool list has changed."""
        for cb in self._tools_changed_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"[MCP] Error in tools_changed callback: {e}")

    @property
    def is_available(self) -> bool:
        """Check if MCP is available."""
        return MCP_AVAILABLE


# =============================================================================
# WEBSOCKET BRIDGE
# =============================================================================

# Allowed origins for WebSocket connections
# In production, update this to match your deployment
ALLOWED_ORIGINS = {
    "http://localhost:8050",
    "http://127.0.0.1:8050",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}

# Add custom origins from environment
_extra_origins = os.environ.get("MCP_ALLOWED_ORIGINS", "")
if _extra_origins:
    ALLOWED_ORIGINS.update(o.strip() for o in _extra_origins.split(",") if o.strip())


async def websocket_bridge(websocket, mcp_relay: Optional[MCPRelay] = None):
    """
    WebSocket endpoint for browser-server communication.

    Protocol:
    - Browser sends "hello" with sid and initial tools
    - Browser sends "tools" when tool list changes
    - Server sends "call" to invoke a tool
    - Browser sends "result" with tool call results

    Args:
        websocket: Starlette WebSocket connection
        mcp_relay: MCPRelay instance for notifications
    """
    # Origin validation
    origin = websocket.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        print(f"[MCP WS] Rejected connection from origin: {origin}")
        await websocket.close(code=4403)
        return

    await websocket.accept()

    sess: Optional[BrowserSession] = None

    try:
        while True:
            raw_msg = await websocket.receive_text()

            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                print(f"[MCP WS] Invalid JSON received: {raw_msg[:100]}")
                continue

            msg_type = msg.get("type")

            # Handle "hello" - new session registration
            if msg_type == "hello":
                sid = str(msg.get("sid", _generate_call_id()))
                page_url = msg.get("page_url", "")
                view_id = msg.get("view_id")

                # Create session
                sess = BrowserSession(
                    sid=sid,
                    ws=websocket,
                    page_url=page_url,
                    view_id=view_id,
                )

                # Register initial tools
                tools = msg.get("tools") or []
                sess.tools = {
                    t["name"]: {
                        "description": t.get("description"),
                        "inputSchema": t.get("inputSchema"),
                        "annotations": t.get("annotations", {}),
                    }
                    for t in tools
                }

                SESSIONS[sid] = sess

                # Acknowledge
                await websocket.send_text(json.dumps({
                    "type": "hello_ack",
                    "sid": sid,
                }))

                print(f"[MCP WS] Session {sid} connected ({len(sess.tools)} tools)")

                # Notify MCP clients
                if mcp_relay:
                    mcp_relay._notify_tools_changed()

                continue

            # Require session for other messages
            if not sess:
                print(f"[MCP WS] Message before hello: {msg_type}")
                continue

            # Handle "tools" - tool list update
            if msg_type == "tools":
                tools = msg.get("tools") or []
                sess.tools = {
                    t["name"]: {
                        "description": t.get("description"),
                        "inputSchema": t.get("inputSchema"),
                        "annotations": t.get("annotations", {}),
                    }
                    for t in tools
                }

                print(f"[MCP WS] Session {sess.sid} updated tools: {list(sess.tools.keys())}")

                # Notify MCP clients
                if mcp_relay:
                    mcp_relay._notify_tools_changed()

                continue

            # Handle "result" - tool call result
            if msg_type == "result":
                call_id = msg.get("call_id")
                payload = msg.get("payload")

                fut = sess.pending.get(call_id)
                if fut and not fut.done():
                    fut.set_result(payload)
                else:
                    print(f"[MCP WS] Unknown or expired call_id: {call_id}")

                continue

            # Handle "page_update" - page navigation
            if msg_type == "page_update":
                sess.page_url = msg.get("page_url", sess.page_url)
                sess.view_id = msg.get("view_id", sess.view_id)
                continue

            print(f"[MCP WS] Unknown message type: {msg_type}")

    except Exception as e:
        if "disconnect" not in str(e).lower():
            print(f"[MCP WS] Error in session {sess.sid if sess else 'unknown'}: {e}")
    finally:
        # Cleanup session
        if sess and sess.sid in SESSIONS:
            del SESSIONS[sess.sid]
            print(f"[MCP WS] Session {sess.sid} disconnected")

            # Cancel pending calls
            for call_id, fut in sess.pending.items():
                if not fut.done():
                    fut.set_exception(RuntimeError("Session disconnected"))

            # Notify MCP clients
            if mcp_relay:
                mcp_relay._notify_tools_changed()


# =============================================================================
# ROUTE CREATION
# =============================================================================

def create_mcp_routes(mcp_relay: MCPRelay, mcp_path: str = "/mcp", ws_path: str = "/dash-mcp/ws"):
    """
    Create Starlette routes for MCP endpoints.

    Returns routes for:
    - {mcp_path}: Streamable HTTP endpoint for MCP protocol
    - {ws_path}: WebSocket endpoint for browser bridge

    Args:
        mcp_relay: Configured MCPRelay instance
        mcp_path: Path for MCP HTTP endpoint (default: /mcp)
        ws_path: Path for WebSocket bridge (default: /dash-mcp/ws)

    Returns:
        List of Starlette Route objects
    """
    if not MCP_AVAILABLE:
        print("[MCP] Warning: MCP SDK not available, routes not created")
        return []

    from starlette.routing import Route, WebSocketRoute, Mount

    # Create an ASGI app class wrapper for the MCP session manager
    class MCPApp:
        """ASGI app wrapper for MCP Streamable HTTP."""
        def __init__(self, session_manager):
            self.session_manager = session_manager

        async def __call__(self, scope, receive, send):
            await self.session_manager.handle_request(scope, receive, send)

    mcp_app = MCPApp(mcp_relay.session_manager)

    async def ws_handler(websocket):
        """WebSocket handler for browser bridge."""
        await websocket_bridge(websocket, mcp_relay)

    return [
        Mount(mcp_path, app=mcp_app),
        WebSocketRoute(ws_path, ws_handler),
    ]


# =============================================================================
# LIFESPAN CONTEXT MANAGER
# =============================================================================

@contextlib.asynccontextmanager
async def mcp_lifespan(app, mcp_relay: MCPRelay):
    """
    Async context manager for MCP server lifecycle.

    Usage with Starlette:
        @contextlib.asynccontextmanager
        async def lifespan(app):
            async with mcp_lifespan(app, mcp_relay):
                yield
    """
    if MCP_AVAILABLE and mcp_relay.session_manager:
        async with mcp_relay.session_manager.run():
            yield
    else:
        yield


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_js_bridge_path() -> str:
    """Get path to the JavaScript bridge file for inclusion in Dash assets."""
    import os
    return os.path.join(os.path.dirname(__file__), "assets", "dash_mcp_bridge.js")


def get_js_bridge_content() -> str:
    """Get the JavaScript bridge content as a string."""
    with open(get_js_bridge_path(), "r") as f:
        return f.read()
