"""Vercel serverless entry point — MCP server only."""

from src.server import mcp

app = mcp.streamable_http_app()
