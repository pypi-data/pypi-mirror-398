"""Base HTTP client for UniFi API interactions."""

from abc import ABC
from typing import Any

import httpx


class BaseUniFiClient(ABC):
    """Base client for UniFi API interactions."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.base_url = f"https://{host}:{port}"

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            verify=verify_ssl,
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UniFi-MCP-Client/1.0",
            },
        )

        # Store authentication state
        self._authenticated = False
        self._csrf_token = None

    async def authenticate(self) -> bool:
        """Authenticate with the UniFi controller."""
        # This will be implemented by subclasses
        raise NotImplementedError

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated HTTP request to the UniFi controller."""
        if not self._authenticated:
            await self.authenticate()

        url = f"{self.base_url}{endpoint}"

        # Add CSRF token to headers if available
        headers = self.client.headers.copy()
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        response = await self.client.request(
            method=method, url=url, json=data, params=params, headers=headers
        )

        # Check if authentication expired
        if response.status_code == 401 or "Login required" in response.text:
            self._authenticated = False
            await self.authenticate()
            # Retry the request
            response = await self.client.request(
                method=method, url=url, json=data, params=params, headers=headers
            )

        response.raise_for_status()
        json_data = response.json()
        if isinstance(json_data, dict):
            return json_data
        # Handle case where response is not a dict
        return {"data": json_data}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "BaseUniFiClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
