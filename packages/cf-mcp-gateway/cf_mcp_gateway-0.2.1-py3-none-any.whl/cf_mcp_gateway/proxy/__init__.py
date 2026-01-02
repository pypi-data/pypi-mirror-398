"""Proxy tools for upstream MCP services."""

from .tool import ProxyTool
from .upstream import configure, get_auth_headers

__all__ = [
    "ProxyTool",
    "configure",
    "get_auth_headers",
]
