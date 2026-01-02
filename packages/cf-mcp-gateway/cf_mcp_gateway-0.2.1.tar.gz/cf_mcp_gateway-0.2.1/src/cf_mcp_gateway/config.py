"""Configuration module for the MCP Gateway."""

from enum import Enum

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TransportMode(str, Enum):
    """Supported transport modes for the gateway."""

    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


class GatewaySettings(BaseSettings):
    """Configuration settings for the MCP Gateway.

    All settings can be configured via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Required: Cloudflare credentials
    cloudflare_api_token: str
    cloudflare_account_id: str

    # Required: Service selection (comma-separated)
    enabled_services: str

    # Transport configuration
    transport: TransportMode = TransportMode.STDIO
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 3000

    # Logging
    log_level: str = "info"

    @field_validator("enabled_services")
    @classmethod
    def validate_enabled_services(cls, v: str) -> str:
        """Validate that enabled_services is not empty."""
        if not v or not v.strip():
            raise ValueError("ENABLED_SERVICES must not be empty")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v.lower()

    def get_enabled_service_ids(self) -> list[str]:
        """Return list of enabled service IDs."""
        return [s.strip() for s in self.enabled_services.split(",") if s.strip()]
