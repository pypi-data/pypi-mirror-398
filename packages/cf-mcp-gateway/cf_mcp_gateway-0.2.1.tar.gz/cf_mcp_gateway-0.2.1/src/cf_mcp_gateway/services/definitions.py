"""Service definitions for Cloudflare MCP services."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    """Configuration for a Cloudflare MCP service."""

    id: str
    name: str
    endpoint: str
    description: str


AVAILABLE_SERVICES: dict[str, ServiceConfig] = {
    "docs": ServiceConfig(
        id="docs",
        name="Documentation",
        endpoint="https://docs.mcp.cloudflare.com/mcp",
        description="Get up to date reference information on Cloudflare",
    ),
    "bindings": ServiceConfig(
        id="bindings",
        name="Workers Bindings",
        endpoint="https://bindings.mcp.cloudflare.com/mcp",
        description="Build Workers applications with storage, AI, and compute primitives",
    ),
    "builds": ServiceConfig(
        id="builds",
        name="Workers Builds",
        endpoint="https://builds.mcp.cloudflare.com/mcp",
        description="Get insights and manage your Cloudflare Workers Builds",
    ),
    "observability": ServiceConfig(
        id="observability",
        name="Observability",
        endpoint="https://observability.mcp.cloudflare.com/mcp",
        description="Debug and get insight into your application's logs and analytics",
    ),
    "radar": ServiceConfig(
        id="radar",
        name="Radar",
        endpoint="https://radar.mcp.cloudflare.com/mcp",
        description="Get global Internet traffic insights, trends, URL scans, and other utilities",
    ),
    "containers": ServiceConfig(
        id="containers",
        name="Containers",
        endpoint="https://containers.mcp.cloudflare.com/mcp",
        description="Spin up a sandbox development environment",
    ),
    "browser": ServiceConfig(
        id="browser",
        name="Browser Rendering",
        endpoint="https://browser.mcp.cloudflare.com/mcp",
        description="Fetch web pages, convert them to markdown and take screenshots",
    ),
    "logpush": ServiceConfig(
        id="logpush",
        name="Logpush",
        endpoint="https://logs.mcp.cloudflare.com/mcp",
        description="Get quick summaries for Logpush job health",
    ),
    "ai-gateway": ServiceConfig(
        id="ai-gateway",
        name="AI Gateway",
        endpoint="https://ai-gateway.mcp.cloudflare.com/mcp",
        description="Search your logs, get details about the prompts and responses",
    ),
    "autorag": ServiceConfig(
        id="autorag",
        name="AutoRAG",
        endpoint="https://autorag.mcp.cloudflare.com/mcp",
        description="List and search documents on your AutoRAGs",
    ),
    "auditlogs": ServiceConfig(
        id="auditlogs",
        name="Audit Logs",
        endpoint="https://auditlogs.mcp.cloudflare.com/mcp",
        description="Query audit logs and generate reports for review",
    ),
    "dns-analytics": ServiceConfig(
        id="dns-analytics",
        name="DNS Analytics",
        endpoint="https://dns-analytics.mcp.cloudflare.com/mcp",
        description="Optimize DNS performance and debug issues based on current set up",
    ),
    "dex": ServiceConfig(
        id="dex",
        name="Digital Experience Monitoring",
        endpoint="https://dex.mcp.cloudflare.com/mcp",
        description="Get quick insight on critical applications for your organization",
    ),
    "casb": ServiceConfig(
        id="casb",
        name="CASB",
        endpoint="https://casb.mcp.cloudflare.com/mcp",
        description="Quickly identify any security misconfigurations for SaaS applications to safeguard users & data",
    ),
    "graphql": ServiceConfig(
        id="graphql",
        name="GraphQL Analytics",
        endpoint="https://graphql.mcp.cloudflare.com/mcp",
        description="Get analytics data using Cloudflare's GraphQL API",
    ),
}


def get_available_service_ids() -> list[str]:
    """Return list of all available service IDs."""
    return list(AVAILABLE_SERVICES.keys())


def validate_service_ids(service_ids: list[str]) -> tuple[list[str], list[str]]:
    """Validate service IDs and return (valid, invalid) lists."""
    valid = []
    invalid = []
    for sid in service_ids:
        if sid in AVAILABLE_SERVICES:
            valid.append(sid)
        else:
            invalid.append(sid)
    return valid, invalid
