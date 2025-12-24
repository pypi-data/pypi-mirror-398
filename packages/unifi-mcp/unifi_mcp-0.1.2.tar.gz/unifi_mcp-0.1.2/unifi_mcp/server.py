"""Main FastMCP server for UniFi integration."""

import importlib.util
import logging
import sys
from typing import Any

from fastmcp import FastMCP

# Check FastMCP rate limiting middleware availability (Phase 3.3 M2: improved pattern)
RATE_LIMITING_AVAILABLE = (
    importlib.util.find_spec("fastmcp.server.middleware.rate_limiting") is not None
)

# Check ServerPanels availability (Phase 3.3 M2: improved pattern)
SERVERPANELS_AVAILABLE = importlib.util.find_spec("mcp_common.ui") is not None

from unifi_mcp.clients.access_client import AccessClient
from unifi_mcp.clients.network_client import NetworkClient
from unifi_mcp.config import Settings
from unifi_mcp.tools.access_tools import (
    get_unifi_access_logs,
    get_unifi_access_points,
    get_unifi_access_users,
    set_unifi_access_schedule,
    unlock_unifi_door,
)
from unifi_mcp.tools.network_tools import (
    disable_unifi_ap,
    enable_unifi_ap,
    get_unifi_clients,
    get_unifi_devices,
    get_unifi_sites,
    get_unifi_statistics,
    get_unifi_wlans,
    restart_unifi_device,
)


def create_server(settings: Settings) -> FastMCP:
    """Create and configure the UniFi MCP server."""
    # Initialize FastMCP server
    server = FastMCP(
        name="UniFi Controller MCP Server",
    )

    # Add rate limiting middleware to protect UniFi API from excessive requests
    if RATE_LIMITING_AVAILABLE:
        from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware

        # UniFi controllers typically handle 10-20 requests/sec well
        # Use token bucket algorithm for burst handling
        rate_limiter = RateLimitingMiddleware(
            max_requests_per_second=10.0,  # Sustainable rate
            burst_capacity=20,  # Allow brief bursts
            global_limit=True,  # Protect the UniFi controller globally
        )
        server.add_middleware(rate_limiter)

    # Initialize clients
    network_client = _create_network_client(settings)
    access_client = _create_access_client(settings)

    # Register tools if clients are available
    if network_client:
        _register_network_tools(server, network_client)

    if access_client:
        _register_access_tools(server, access_client)

    return server


def _create_network_client(settings: Settings) -> NetworkClient | None:
    """Create a NetworkClient if configuration is provided."""
    if settings.network_controller:
        return NetworkClient(
            host=settings.network_controller.host,
            port=settings.network_controller.port,
            username=settings.network_controller.username,
            password=settings.network_controller.password,
            verify_ssl=settings.network_controller.verify_ssl,
            timeout=settings.network_controller.timeout,
        )
    return None


def _create_access_client(settings: Settings) -> AccessClient | None:
    """Create an AccessClient if configuration is provided."""
    if settings.access_controller:
        return AccessClient(
            host=settings.access_controller.host,
            port=settings.access_controller.port,
            username=settings.access_controller.username,
            password=settings.access_controller.password,
            verify_ssl=settings.access_controller.verify_ssl,
            timeout=settings.access_controller.timeout,
        )
    return None


def _register_network_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register network tools with the server."""
    _register_site_tools(server, network_client)
    _register_device_tools(server, network_client)
    _register_client_tools(server, network_client)
    _register_wlan_tools(server, network_client)
    _register_device_control_tools(server, network_client)
    _register_statistics_tools(server, network_client)


def _register_site_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register site-related tools."""

    @server.tool()
    async def unifi_get_sites() -> list[dict[str, Any]]:
        """Get all sites from the UniFi Network Controller"""
        result = await get_unifi_sites(network_client)
        if isinstance(result, list):
            return result
        return []


def _register_device_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register device-related tools."""

    @server.tool()
    async def unifi_get_devices(site_id: str = "default") -> list[dict[str, Any]]:
        """Get all devices in a specific site from the UniFi Network Controller.

        Args:
            site_id: The site ID to query (defaults to 'default')
        """
        result = await get_unifi_devices(network_client, site_id)
        if isinstance(result, list):
            return result
        return []


def _register_client_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register client-related tools."""

    @server.tool()
    async def unifi_get_clients(site_id: str = "default") -> list[dict[str, Any]]:
        """Get all clients in a specific site from the UniFi Network Controller.

        Args:
            site_id: The site ID to query (defaults to 'default')
        """
        result = await get_unifi_clients(network_client, site_id)
        if isinstance(result, list):
            return result
        return []


def _register_wlan_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register WLAN-related tools."""

    @server.tool()
    async def unifi_get_wlans(site_id: str = "default") -> list[dict[str, Any]]:
        """Get all WLANs in a specific site from the UniFi Network Controller.

        Args:
            site_id: The site ID to query (defaults to 'default')
        """
        result = await get_unifi_wlans(network_client, site_id)
        if isinstance(result, list):
            return result
        return []


def _register_device_control_tools(
    server: FastMCP, network_client: NetworkClient
) -> None:
    """Register device control tools."""

    @server.tool()
    async def unifi_restart_device(
        mac: str, site_id: str = "default"
    ) -> dict[str, Any]:
        """Restart a device by its MAC address in the UniFi Network Controller.

        Args:
            mac: The MAC address of the device to restart
            site_id: The site ID (defaults to 'default')
        """
        result = await restart_unifi_device(network_client, mac, site_id)
        if isinstance(result, dict):
            return result
        return {}

    @server.tool()
    async def unifi_disable_ap(mac: str, site_id: str = "default") -> dict[str, Any]:
        """Disable an access point by its MAC address in the UniFi Network Controller.

        Args:
            mac: The MAC address of the access point to disable
            site_id: The site ID (defaults to 'default')
        """
        result = await disable_unifi_ap(network_client, mac, site_id)
        if isinstance(result, dict):
            return result
        return {}

    @server.tool()
    async def unifi_enable_ap(mac: str, site_id: str = "default") -> dict[str, Any]:
        """Enable an access point by its MAC address in the UniFi Network Controller.

        Args:
            mac: The MAC address of the access point to enable
            site_id: The site ID (defaults to 'default')
        """
        result = await enable_unifi_ap(network_client, mac, site_id)
        if isinstance(result, dict):
            return result
        return {}


def _register_statistics_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register statistics tools."""

    @server.tool()
    async def unifi_get_statistics(site_id: str = "default") -> dict[str, Any]:
        """Get site statistics from the UniFi Network Controller.

        Args:
            site_id: The site ID to query (defaults to 'default')
        """
        result = await get_unifi_statistics(network_client, site_id)
        if isinstance(result, dict):
            return result
        return {}


def _register_access_tools(server: FastMCP, access_client: AccessClient) -> None:
    """Register access tools with the server."""

    @server.tool()
    async def unifi_get_access_points() -> list[dict[str, Any]]:
        """Get all access points from the UniFi Access Controller"""
        result = await get_unifi_access_points(access_client)
        if isinstance(result, list):
            return result
        return []

    @server.tool()
    async def unifi_get_access_users() -> list[dict[str, Any]]:
        """Get all users from the UniFi Access Controller"""
        result = await get_unifi_access_users(access_client)
        if isinstance(result, list):
            return result
        return []

    @server.tool()
    async def unifi_get_access_logs() -> list[dict[str, Any]]:
        """Get door access logs from the UniFi Access Controller"""
        result = await get_unifi_access_logs(access_client)
        if isinstance(result, list):
            return result
        return []

    @server.tool()
    async def unifi_unlock_door(door_id: str) -> dict[str, Any]:
        """Unlock a door via the UniFi Access Controller.

        Args:
            door_id: The ID of the door to unlock
        """
        result = await unlock_unifi_door(access_client, door_id)
        if isinstance(result, dict):
            return result
        return {}

    @server.tool()
    async def unifi_set_access_schedule(user_id: str, schedule: dict) -> dict[str, Any]:
        """Set access schedule for a user via the UniFi Access Controller.

        Args:
            user_id: The user ID to configure
            schedule: The schedule configuration dictionary
        """
        result = await set_unifi_access_schedule(access_client, user_id, schedule)
        if isinstance(result, dict):
            return result
        return {}


def run_server() -> None:
    """Run the UniFi MCP server."""
    settings = _load_and_validate_settings()
    server = _create_server_with_error_handling(settings)
    _configure_logging(settings)
    features = _build_feature_list(settings)
    _display_startup_message(settings, features)
    _run_server_instance(server, settings)


def _load_and_validate_settings() -> Settings:
    """Load and validate settings, handling configuration errors."""
    try:
        settings = Settings()
        settings.validate_credentials_at_startup()
        return settings
    except Exception as e:
        # Check if this is an MCP server error (if exceptions available)
        from unifi_mcp.config import EXCEPTIONS_AVAILABLE

        if EXCEPTIONS_AVAILABLE:
            from mcp_common.exceptions import MCPServerError

            if isinstance(e, MCPServerError):
                print(f"\n❌ Server Configuration Error: {e}", file=sys.stderr)
                if hasattr(e, "field") and e.field:
                    print(f"   Field: {e.field}", file=sys.stderr)
                sys.exit(1)

        # Re-raise if not an MCP error or exceptions unavailable
        raise


def _create_server_with_error_handling(settings: Settings) -> FastMCP:
    """Create server with proper error handling."""
    return create_server(settings)


def _configure_logging(settings: Settings) -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=logging.INFO if settings.server.debug else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _build_feature_list(settings: Settings) -> list[str]:
    """Build a list of features based on configured controllers."""
    features = []

    if settings.network_controller:
        features.extend(
            [
                "🌐 Network Controller Integration",
                "  • Site Management & Statistics",
                "  • Device Control (AP enable/disable, restart)",
                "  • Client & WLAN Management",
            ]
        )

    if settings.access_controller:
        features.extend(
            [
                "🔒 Access Controller Integration",
                "  • Door Access Control & Unlock",
                "  • User & Schedule Management",
                "  • Access Event Logging",
            ]
        )

    features.extend(
        [
            "⚡ Connection Pooling (persistent HTTP clients)",
            "🛡️ Rate Limiting (10 req/sec, burst to 20)"
            if RATE_LIMITING_AVAILABLE
            else None,
            "🔒 Credential Validation (12+ char passwords)",
            "🎨 Modern FastMCP Architecture",
        ]
    )

    # Remove None entries if rate limiting not available
    return [f for f in features if f is not None]


def _display_startup_message(settings: Settings, features: list[str]) -> None:
    """Display startup message with ServerPanels or fallback to plain text."""
    if SERVERPANELS_AVAILABLE:
        from mcp_common.ui import ServerPanels

        ServerPanels.startup_success(
            server_name="UniFi Controller MCP",
            version="1.0.0",
            features=features,
            endpoint=f"http://{settings.server.host}:{settings.server.port}/mcp",
        )
    else:
        # Fallback to plain text
        print("\n✅ UniFi Controller MCP Server Starting", file=sys.stderr)
        print(
            f"   Endpoint: http://{settings.server.host}:{settings.server.port}/mcp",
            file=sys.stderr,
        )
        for feature in features:
            print(f"   {feature}", file=sys.stderr)
        print("", file=sys.stderr)


def _run_server_instance(server: FastMCP, settings: Settings) -> None:
    """Run the server instance with the provided settings."""
    server.run(
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )


# Export ASGI app for uvicorn (standardized startup pattern)
# Create a default server instance for uvicorn
_default_settings = Settings()
_default_server = create_server(_default_settings)
http_app = _default_server.http_app


if __name__ == "__main__":
    run_server()
