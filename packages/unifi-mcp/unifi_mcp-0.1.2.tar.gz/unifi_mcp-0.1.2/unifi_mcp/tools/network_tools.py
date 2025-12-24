"""MCP tools for UniFi Network operations."""

from typing import Any

from unifi_mcp.clients.network_client import NetworkClient


async def get_unifi_sites(network_client: NetworkClient) -> list[dict[str, Any]]:
    """Get all sites from the UniFi Network Controller."""
    sites = await network_client.get_sites()
    return sites


async def get_unifi_devices(
    network_client: NetworkClient, site_id: str = "default"
) -> list[dict[str, Any]]:
    """Get all devices in a specific site from the UniFi Network Controller."""
    devices = await network_client.get_devices(site_id)
    return devices


async def get_unifi_clients(
    network_client: NetworkClient, site_id: str = "default"
) -> list[dict[str, Any]]:
    """Get all clients in a specific site from the UniFi Network Controller."""
    clients = await network_client.get_clients(site_id)
    return clients


async def get_unifi_wlans(
    network_client: NetworkClient, site_id: str = "default"
) -> list[dict[str, Any]]:
    """Get all WLANs in a specific site from the UniFi Network Controller."""
    wlans = await network_client.get_wlans(site_id)
    return wlans


async def restart_unifi_device(
    network_client: NetworkClient, mac: str, site_id: str = "default"
) -> dict[str, Any]:
    """Restart a device by its MAC address in the UniFi Network Controller."""
    result = await network_client.restart_device(mac, site_id)
    return result


async def disable_unifi_ap(
    network_client: NetworkClient, mac: str, site_id: str = "default"
) -> dict[str, Any]:
    """Disable an access point by its MAC address in the UniFi Network Controller."""
    result = await network_client.disable_ap(mac, site_id)
    return result


async def enable_unifi_ap(
    network_client: NetworkClient, mac: str, site_id: str = "default"
) -> dict[str, Any]:
    """Enable an access point by its MAC address in the UniFi Network Controller."""
    result = await network_client.enable_ap(mac, site_id)
    return result


async def get_unifi_statistics(
    network_client: NetworkClient, site_id: str = "default"
) -> dict[str, Any]:
    """Get site statistics from the UniFi Network Controller."""
    stats = await network_client.get_statistics(site_id)
    return stats
