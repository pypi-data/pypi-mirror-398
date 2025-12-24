"""UniFi Network Controller API client."""

from typing import Any

import httpx

from .base_client import BaseUniFiClient


class NetworkClient(BaseUniFiClient):
    """Client for UniFi Network Controller API."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Network Controller specific endpoints
        self.api_base = "/api"
        self.base_url = f"https://{self.host}:{self.port}"

    async def authenticate(self) -> bool:
        """Authenticate with the UniFi Network Controller."""
        try:
            # First, get CSRF token by making a request to the login page
            login_url = f"{self.base_url}/api/auth/login"

            response = await self.client.post(
                login_url,
                json={
                    "username": self.username,
                    "password": self.password,
                    "remember": True,
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "UniFi-MCP-Client/1.0",
                },
            )

            # Check if login was successful
            if response.status_code == 200:
                self._authenticated = True
                # Extract CSRF token from response headers or cookies
                csrf_token = response.headers.get("x-csrf-token")
                if csrf_token:
                    self._csrf_token = csrf_token
                return True
            else:
                raise Exception(
                    f"Authentication failed with status {response.status_code}"
                )

        except httpx.RequestError as e:
            raise Exception(f"Network error during authentication: {e}")
        except Exception as e:
            raise Exception(f"Authentication error: {e}")

    async def get_sites(self) -> list[dict[str, Any]]:
        """Get all sites from the UniFi controller."""
        endpoint = f"{self.api_base}/self/sites"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_devices(self, site_id: str = "default") -> list[dict[str, Any]]:
        """Get all devices in a specific site."""
        endpoint = f"{self.api_base}/s/{site_id}/stat/device"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_clients(self, site_id: str = "default") -> list[dict[str, Any]]:
        """Get all clients in a specific site."""
        endpoint = f"{self.api_base}/s/{site_id}/stat/sta"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_wlans(self, site_id: str = "default") -> list[dict[str, Any]]:
        """Get all WLANs in a specific site."""
        endpoint = f"{self.api_base}/s/{site_id}/rest/wlanconf"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def restart_device(
        self, mac: str, site_id: str = "default"
    ) -> dict[str, Any]:
        """Restart a device by its MAC address."""
        endpoint = f"{self.api_base}/s/{site_id}/cmd/devmgr"
        data = {"cmd": "restart", "mac": mac}
        return await self._make_request("POST", endpoint, data)

    async def disable_ap(self, mac: str, site_id: str = "default") -> dict[str, Any]:
        """Disable an access point by its MAC address."""
        endpoint = f"{self.api_base}/s/{site_id}/rest/device/{mac}"
        data = {"disabled": True}
        return await self._make_request("PUT", endpoint, data)

    async def enable_ap(self, mac: str, site_id: str = "default") -> dict[str, Any]:
        """Enable an access point by its MAC address."""
        endpoint = f"{self.api_base}/s/{site_id}/rest/device/{mac}"
        data = {"disabled": False}
        return await self._make_request("PUT", endpoint, data)

    async def get_statistics(self, site_id: str = "default") -> dict[str, Any]:
        """Get site statistics."""
        endpoint = f"{self.api_base}/s/{site_id}/stat/statistics"
        return await self._make_request("GET", endpoint)
