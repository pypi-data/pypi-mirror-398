"""Test script for UniFi MCP server."""

import asyncio
import os

from unifi_mcp.clients.access_client import AccessClient
from unifi_mcp.clients.network_client import NetworkClient


async def test_network_client():
    """Test the Network Controller client."""
    print("Testing Network Controller client...")

    # Get credentials from environment or use defaults (these are just for testing)
    host = os.getenv("UNIFI_HOST", "unifi.example.com")
    port = int(os.getenv("UNIFI_PORT", 8443))
    username = os.getenv("UNIFI_USERNAME", "admin")
    password = os.getenv("UNIFI_PASSWORD", "password")

    # Skip actual test if no credentials provided
    if host == "unifi.example.com":
        print("Skipping Network Controller test - no credentials provided")
        print(
            "To run this test, set UNIFI_HOST, UNIFI_PORT, UNIFI_USERNAME, and UNIFI_PASSWORD environment variables"
        )
        return

    async with NetworkClient(host, port, username, password) as client:
        try:
            # Test authentication
            authenticated = await client.authenticate()
            print(f"Authentication: {'Success' if authenticated else 'Failed'}")

            # Test getting sites
            if authenticated:
                sites = await client.get_sites()
                print(f"Found {len(sites)} sites")

                # Test getting devices from the first site if available
                if sites:
                    site_id = sites[0].get("name", "default")
                    devices = await client.get_devices(site_id)
                    print(f"Found {len(devices)} devices in site '{site_id}'")

        except Exception as e:
            print(f"Error testing Network Controller client: {e}")


async def test_access_client():
    """Test the Access Controller client."""
    print("Testing Access Controller client...")

    # Get credentials from environment or use defaults (these are just for testing)
    host = os.getenv("UNIFI_ACCESS_HOST", "unifi-access.example.com")
    port = int(os.getenv("UNIFI_ACCESS_PORT", 8444))
    username = os.getenv("UNIFI_ACCESS_USERNAME", "admin")
    password = os.getenv("UNIFI_ACCESS_PASSWORD", "password")

    # Skip actual test if no credentials provided
    if host == "unifi-access.example.com":
        print("Skipping Access Controller test - no credentials provided")
        print(
            "To run this test, set UNIFI_ACCESS_HOST, UNIFI_ACCESS_PORT, UNIFI_ACCESS_USERNAME, and UNIFI_ACCESS_PASSWORD environment variables"
        )
        return

    async with AccessClient(host, port, username, password) as client:
        try:
            # Test authentication
            authenticated = await client.authenticate()
            print(f"Authentication: {'Success' if authenticated else 'Failed'}")

            # Test getting access points
            if authenticated:
                access_points = await client.get_access_points()
                print(f"Found {len(access_points)} access points")

        except Exception as e:
            print(f"Error testing Access Controller client: {e}")


async def main():
    """Run tests."""
    print("Starting UniFi MCP server tests...")
    await test_network_client()
    print()
    await test_access_client()
    print("Tests completed.")


if __name__ == "__main__":
    asyncio.run(main())
