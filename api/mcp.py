"""Vercel serverless entry point for the MCP server."""

from src.server import mcp

# Vercel expects an ASGI/WSGI app or a handler.
# FastMCP with streamable-http exposes an ASGI app via .asgi_app()
app = mcp.streamable_http_app()
