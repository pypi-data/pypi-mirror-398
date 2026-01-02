"""Service registry for managing enabled Cloudflare MCP services."""

from ..config import GatewaySettings
from .definitions import (
    AVAILABLE_SERVICES,
    ServiceConfig,
    get_available_service_ids,
    validate_service_ids,
)


class ServiceRegistryError(Exception):
    """Error raised when service registry encounters invalid configuration."""

    pass


class ServiceRegistry:
    """Registry for managing enabled Cloudflare MCP services.

    This class validates and manages the set of services enabled via
    the ENABLED_SERVICES environment variable.
    """

    def __init__(self, settings: GatewaySettings) -> None:
        """Initialize the registry with gateway settings.

        Args:
            settings: Gateway configuration settings.

        Raises:
            ServiceRegistryError: If any enabled service ID is invalid.
        """
        self.settings = settings
        self._enabled_services: list[ServiceConfig] = []
        self._validate_and_load()

    def _validate_and_load(self) -> None:
        """Validate enabled service IDs and load service configs."""
        enabled_ids = self.settings.get_enabled_service_ids()

        if not enabled_ids:
            raise ServiceRegistryError(
                "No services enabled. Set ENABLED_SERVICES with at least one service ID. "
                f"Available services: {', '.join(get_available_service_ids())}"
            )

        valid, invalid = validate_service_ids(enabled_ids)

        if invalid:
            raise ServiceRegistryError(
                f"Unknown service IDs: {', '.join(invalid)}. "
                f"Available services: {', '.join(get_available_service_ids())}"
            )

        self._enabled_services = [AVAILABLE_SERVICES[sid] for sid in valid]

    def get_enabled_services(self) -> list[ServiceConfig]:
        """Return list of enabled service configurations."""
        return self._enabled_services.copy()

    def __len__(self) -> int:
        """Return number of enabled services."""
        return len(self._enabled_services)

    def __iter__(self):
        """Iterate over enabled services."""
        return iter(self._enabled_services)
