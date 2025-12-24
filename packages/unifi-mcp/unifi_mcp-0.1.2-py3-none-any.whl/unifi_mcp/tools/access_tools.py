"""MCP tools for UniFi Access operations."""

from typing import Any

from unifi_mcp.clients.access_client import AccessClient


async def get_unifi_access_points(access_client: AccessClient) -> list[dict[str, Any]]:
    """Get all access points from the UniFi Access Controller."""
    access_points = await access_client.get_access_points()
    return access_points


async def get_unifi_access_users(access_client: AccessClient) -> list[dict[str, Any]]:
    """Get all users from the UniFi Access Controller."""
    users = await access_client.get_users()
    return users


async def get_unifi_access_logs(access_client: AccessClient) -> list[dict[str, Any]]:
    """Get door access logs from the UniFi Access Controller."""
    logs = await access_client.get_door_access_logs()
    return logs


async def unlock_unifi_door(
    access_client: AccessClient, door_id: str
) -> dict[str, Any]:
    """Unlock a door via the UniFi Access Controller."""
    result = await access_client.unlock_door(door_id)
    return result


async def set_unifi_access_schedule(
    access_client: AccessClient, user_id: str, schedule: dict[str, Any]
) -> dict[str, Any]:
    """Set access schedule for a user via the UniFi Access Controller."""
    result = await access_client.set_access_schedule(user_id, schedule)
    return result
