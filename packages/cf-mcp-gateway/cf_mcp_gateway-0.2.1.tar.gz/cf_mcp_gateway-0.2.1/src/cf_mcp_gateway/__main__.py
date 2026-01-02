"""Entry point for the Cloudflare MCP Gateway."""

import asyncio
import logging
import sys
from typing import NoReturn

from .config import GatewaySettings, TransportMode
from .server import (
    connect_and_mount_services,
    initialize_gateway,
    mcp,
    shutdown_gateway,
)
from .transport import run_http, run_stdio


def setup_logging(log_level: str) -> None:
    """Configure logging for the gateway.

    Logs are written to stderr to avoid interfering with stdio transport.

    Args:
        log_level: The logging level (debug, info, warning, error, critical).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    # Reduce noise from httpx and other libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def async_main() -> None:
    """Async main entry point."""
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        settings = GatewaySettings()
        setup_logging(settings.log_level)

        logger.info("Initializing Cloudflare MCP Gateway")
        logger.info(f"Transport: {settings.transport.value}")
        logger.info(f"Enabled services: {settings.enabled_services}")

        # Initialize the gateway
        await initialize_gateway(settings)

        # Connect to upstream services and mount their tools
        await connect_and_mount_services()

        # Run with the configured transport
        if settings.transport == TransportMode.STDIO:
            await run_stdio(mcp, shutdown_gateway)
        elif settings.transport == TransportMode.STREAMABLE_HTTP:
            await run_http(mcp, settings, shutdown_gateway)
        else:
            raise ValueError(f"Unknown transport mode: {settings.transport}")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def main() -> NoReturn:
    """Main entry point for the CLI."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
