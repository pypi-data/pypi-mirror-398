"""Transparent proxy tool for upstream MCP services."""

from typing import Any

from fastmcp.tools.tool import Tool, ToolResult

from .upstream import call_upstream_tool


class ProxyTool(Tool):
    """Proxy tool that preserves exact upstream inputSchema.

    This tool acts as a transparent proxy - it passes the upstream
    inputSchema through unchanged, only modifying the tool name
    (adding service prefix).

    Arguments are forwarded to the upstream service without any
    type coercion or validation by the gateway.
    """

    service_id: str
    upstream_name: str

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        """Forward arguments directly to upstream without modification.

        Args:
            arguments: Arguments dict from MCP client (schema validated upstream).

        Returns:
            ToolResult containing upstream response content.
        """
        content = await call_upstream_tool(self.service_id, self.upstream_name, arguments)
        return ToolResult(content=content)
