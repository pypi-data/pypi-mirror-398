"""Stdio transport runner."""

import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


async def run_stdio(
    mcp: Any,
    shutdown_callback: Callable[[], Awaitable[None]],
) -> None:
    """Run the gateway with stdio transport.

    Args:
        mcp: FastMCP server instance.
        shutdown_callback: Async function to call on shutdown.
    """
    logger.info("Starting gateway with stdio transport")

    try:
        await mcp.run_async()
    except Exception as e:
        logger.error(f"Stdio transport error: {e}")
        raise
    finally:
        await shutdown_callback()
