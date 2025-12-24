"""UniFi Access Controller API client."""

from typing import Any

import httpx

from .base_client import BaseUniFiClient


class AccessClient(BaseUniFiClient):
    """Client for UniFi Access Controller API."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Access Controller specific endpoints
        self.api_base = "/api/v1"
        self.base_url = f"https://{self.host}:{self.port}"

    async def authenticate(self) -> bool:
        """Authenticate with the UniFi Access Controller."""
        try:
            # Access Controller authentication might be different
            # This is a placeholder - actual implementation depends on specific API
            login_url = f"{self.base_url}/api/auth/login"

            response = await self.client.post(
                login_url,
                json={"username": self.username, "password": self.password},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "UniFi-MCP-Client/1.0",
                },
            )

            # Check if login was successful
            if response.status_code in (200, 201):
                self._authenticated = True
                # Extract any tokens or session info from response
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

    async def get_access_points(self) -> list[dict[str, Any]]:
        """Get all access points from the UniFi Access Controller."""
        # This is a placeholder - the actual endpoint depends on Access Controller API
        endpoint = f"{self.api_base}/access-points"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_users(self) -> list[dict[str, Any]]:
        """Get all users from the UniFi Access Controller."""
        # This is a placeholder - the actual endpoint depends on Access Controller API
        endpoint = f"{self.api_base}/users"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_door_access_logs(self) -> list[dict[str, Any]]:
        """Get door access logs from the UniFi Access Controller."""
        # This is a placeholder - the actual endpoint depends on Access Controller API
        endpoint = f"{self.api_base}/access-logs"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def unlock_door(self, door_id: str) -> dict[str, Any]:
        """Unlock a door via the UniFi Access Controller."""
        # This is a placeholder - the actual endpoint depends on Access Controller API
        endpoint = f"{self.api_base}/doors/{door_id}/unlock"
        return await self._make_request("POST", endpoint)

    async def set_access_schedule(
        self, user_id: str, schedule: dict[str, Any]
    ) -> dict[str, Any]:
        """Set access schedule for a user via the UniFi Access Controller."""
        # This is a placeholder - the actual endpoint depends on Access Controller API
        endpoint = f"{self.api_base}/users/{user_id}/schedule"
        return await self._make_request("PUT", endpoint, schedule)
