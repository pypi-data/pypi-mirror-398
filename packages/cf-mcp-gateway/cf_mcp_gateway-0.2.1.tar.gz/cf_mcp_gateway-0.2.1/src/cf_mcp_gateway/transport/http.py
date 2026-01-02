"""HTTP transport runner."""

import asyncio
import logging
import signal
from typing import Any, Awaitable, Callable

from ..config import GatewaySettings

logger = logging.getLogger(__name__)


async def run_http(
    mcp: Any,
    settings: GatewaySettings,
    shutdown_callback: Callable[[], Awaitable[None]],
) -> None:
    """Run the gateway with streamable HTTP transport.

    Args:
        mcp: FastMCP server instance.
        settings: Gateway configuration settings.
        shutdown_callback: Async function to call on shutdown.
    """
    logger.info(
        f"Starting gateway with streamable HTTP transport on "
        f"{settings.gateway_host}:{settings.gateway_port}"
    )

    shutdown_event = asyncio.Event()

    def signal_handler(sig: int) -> None:
        logger.info(f"Received signal {sig}, initiating shutdown...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    try:
        server_task = asyncio.create_task(
            mcp.run_http_async(
                host=settings.gateway_host,
                port=settings.gateway_port,
            )
        )

        done, pending = await asyncio.wait(
            [server_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"HTTP transport error: {e}")
        raise
    finally:
        await shutdown_callback()
