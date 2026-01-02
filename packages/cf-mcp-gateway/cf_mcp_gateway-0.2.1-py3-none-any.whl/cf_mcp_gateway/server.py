"""FastMCP server for the Cloudflare MCP Gateway."""

import logging

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

from .config import GatewaySettings
from .proxy import ProxyTool, configure as configure_upstream, get_auth_headers
from .services import ServiceRegistry

logger = logging.getLogger(__name__)

# Global state for the gateway
_settings: GatewaySettings | None = None
_registry: ServiceRegistry | None = None
_service_endpoints: dict[str, str] = {}

# Create the FastMCP server instance
mcp = FastMCP(
    "Cloudflare MCP Gateway",
    instructions="A unified gateway for accessing multiple Cloudflare services. "
    "Tools are prefixed with the service name (e.g., docs_, kv_, r2_).",
)


async def initialize_gateway(settings: GatewaySettings) -> None:
    """Initialize the gateway with settings.

    Args:
        settings: Gateway configuration settings.
    """
    global _settings, _registry

    _settings = settings
    _registry = ServiceRegistry(settings)

    logger.info(
        f"Initialized registry with {len(_registry)} services: "
        f"{', '.join(s.id for s in _registry)}"
    )


def _register_tool(service_id: str, tool) -> None:
    """Register upstream tool as transparent proxy - only name changes.

    Args:
        service_id: The service ID prefix.
        tool: Upstream tool definition from MCP.
    """
    prefixed_name = f"{service_id}_{tool.name}"
    input_schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
    output_schema = getattr(tool, "outputSchema", None)

    proxy_tool = ProxyTool(
        name=prefixed_name,
        description=tool.description or f"Call {tool.name} on {service_id}",
        parameters=input_schema,
        output_schema=output_schema,
        service_id=service_id,
        upstream_name=tool.name,
    )

    mcp._tool_manager.add_tool(proxy_tool)
    logger.debug(f"Registered proxy tool: {prefixed_name}")


async def connect_and_mount_services() -> None:
    """Connect to all enabled upstream services and import their tools."""
    global _service_endpoints

    if not _registry or not _settings:
        raise RuntimeError("Gateway not initialized. Call initialize_gateway() first.")

    # Build endpoints map first
    for service in _registry.get_enabled_services():
        _service_endpoints[service.id] = service.endpoint

    # Configure upstream module before connecting (needed for auth headers)
    configure_upstream(_settings, _service_endpoints)

    for service in _registry.get_enabled_services():
        try:
            logger.info(f"Connecting to {service.id} at {service.endpoint}")

            # Create temporary client to fetch tool definitions
            transport = StreamableHttpTransport(
                url=service.endpoint, headers=get_auth_headers()
            )
            client = Client(transport)

            async with client:
                tools_result = await client.list_tools()
                tools = (
                    tools_result.tools if hasattr(tools_result, "tools") else tools_result
                )

                logger.info(f"Found {len(tools)} tools from {service.id}")

                for tool in tools:
                    try:
                        _register_tool(service.id, tool)
                    except Exception as e:
                        logger.error(f"Failed to register tool {tool.name}: {e}")

            logger.info(
                f"Successfully imported tools from {service.id} with prefix '{service.id}_'"
            )

        except Exception as e:
            logger.warning(f"Failed to connect to {service.id}, will skip: {e}")


async def shutdown_gateway() -> None:
    """Perform graceful shutdown of the gateway."""
    global _service_endpoints

    logger.info("Shutting down gateway...")
    _service_endpoints = {}
    logger.info("Gateway shutdown complete")
