"""Upstream service communication."""

import asyncio
import logging
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import TextContent

from ..config import GatewaySettings

logger = logging.getLogger(__name__)

# Default timeout for upstream calls (seconds)
UPSTREAM_TIMEOUT = 60.0

# Module-level state (configured by server.py)
_settings: GatewaySettings | None = None
_service_endpoints: dict[str, str] = {}


def configure(settings: GatewaySettings, endpoints: dict[str, str]) -> None:
    """Configure upstream communication.

    Args:
        settings: Gateway settings with credentials.
        endpoints: Mapping of service_id to endpoint URL.
    """
    global _settings, _service_endpoints
    _settings = settings
    _service_endpoints = endpoints


def get_auth_headers() -> dict[str, str]:
    """Get authorization headers for upstream calls.

    Returns:
        Dict with Authorization and CF-Account-ID headers.

    Raises:
        RuntimeError: If upstream is not configured.
    """
    if not _settings:
        raise RuntimeError("Upstream not configured. Call configure() first.")
    return {
        "Authorization": f"Bearer {_settings.cloudflare_api_token}",
        "CF-Account-ID": _settings.cloudflare_account_id,
    }


async def call_upstream_tool(
    service_id: str, tool_name: str, arguments: dict[str, Any]
) -> list[TextContent]:
    """Call upstream tool with fresh connection.

    Creates a fresh transport and client for each call to avoid
    connection reuse issues with FastMCP proxy.

    Args:
        service_id: The service ID to call.
        tool_name: The tool name on the upstream service.
        arguments: Arguments to pass to the tool.

    Returns:
        List of TextContent from the upstream tool.

    Raises:
        RuntimeError: If service endpoint is not configured.
    """
    endpoint = _service_endpoints.get(service_id)
    if not endpoint:
        raise RuntimeError(f"No endpoint configured for service {service_id}")

    logger.debug(f"Calling upstream {service_id}.{tool_name}")

    transport = StreamableHttpTransport(url=endpoint, headers=get_auth_headers())
    client = Client(transport)

    try:
        async with client:
            result = await asyncio.wait_for(
                client.call_tool(tool_name, arguments),
                timeout=UPSTREAM_TIMEOUT,
            )
            logger.debug(f"Upstream {service_id}.{tool_name} returned {len(result.content)} items")
            return result.content
    except asyncio.TimeoutError:
        logger.error(f"Upstream call to {service_id}.{tool_name} timed out after {UPSTREAM_TIMEOUT}s")
        raise RuntimeError(f"Upstream call timed out after {UPSTREAM_TIMEOUT}s")
