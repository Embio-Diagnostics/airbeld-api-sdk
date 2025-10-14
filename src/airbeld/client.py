"""Async HTTP client for the Airbeld API."""

import time
from typing import Any
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import ApiError, AuthError, NetworkError, RateLimitError
from .models import DeviceReadings, DeviceSummary, Readings
from .version import get_user_agent


class AirbeldClient:
    """Async HTTP client for the Airbeld API."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.airbeld.com",
        timeout: float = 10.0,
    ) -> None:
        """Initialize the Airbeld API client.

        Args:
            token: JWT access token for authentication
            base_url: Base URL for the API (default: https://api.airbeld.com)
            timeout: Request timeout in seconds (default: 10.0)
        """
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api/v1"
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": get_user_agent(),
            },
        )

    async def __aenter__(self) -> "AirbeldClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        del exc_type, exc_val, exc_tb  # Unused parameters
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    def set_token(self, new_token: str) -> None:
        """Update the authorization token at runtime.

        Args:
            new_token: New JWT access token for authentication
        """
        self._client.headers["Authorization"] = f"Bearer {new_token}"

    def _build_url(self, path: str) -> str:
        """Build full URL from API path."""
        return urljoin(f"{self.base_url}{self.api_prefix}/", path.lstrip("/"))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((NetworkError, RateLimitError)),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retries and error handling."""
        url = self._build_url(path)

        try:
            response = await self._client.request(method, url, **kwargs)
            self._handle_http_errors(response)
            return response
        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {e}") from e
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timeout: {e}") from e
        except RateLimitError as e:
            # Handle Retry-After header for rate limiting
            if e.retry_after:
                time.sleep(e.retry_after)
            raise

    def _handle_http_errors(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        if response.is_success:
            return

        status_code = response.status_code

        try:
            error_data = response.json()
            error_message = error_data.get("error", f"HTTP {status_code}")
        except Exception:
            error_message = f"HTTP {status_code}"

        if status_code in (401, 403):
            raise AuthError(error_message)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            raise RateLimitError(error_message, retry_after=retry_seconds)
        else:
            raise ApiError(
                error_message,
                status_code=status_code,
                response_body=response.text,
            )

    async def async_get_devices(self) -> list[DeviceSummary]:
        """Get list of all devices.

        Returns:
            List of device summary objects

        Raises:
            AuthError: Authentication failed (401/403)
            ApiError: Other API errors (4xx/5xx)
            NetworkError: Network connectivity issues
        """
        response = await self._request("GET", "devices/")
        devices_data = response.json()
        return [DeviceSummary(**device) for device in devices_data]

    async def async_get_readings_by_date(
        self,
        device_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        sensor: str | None = None,
        period: str | None = None,
    ) -> Readings:
        """Get telemetry readings for a device within a date range.

        Args:
            device_id: Device ID (int)
            start_date: Optional start date. Use 'today' or format 'YYYY-MM-DD'. If omitted, returns latest data.
            end_date: Optional end date. Use 'today' or format 'YYYY-MM-DD'. If omitted, returns latest data.
            sensor: Optional sensor name to filter (e.g., "temperature", "pm2p5"). Leave blank for all sensors.
            period: Optional data aggregation period. Values: "day" or "hour".

        Returns:
            Readings object containing sensor readings

        Raises:
            AuthError: Authentication failed (401/403)
            ApiError: API errors including 404 (device not found), 413 (range too large)
            RateLimitError: Rate limit exceeded (429)
            NetworkError: Network connectivity issues
        """
        # Build query parameters
        params: dict[str, str] = {}

        if start_date is not None:
            params["start-date"] = start_date

        if end_date is not None:
            params["end-date"] = end_date

        if sensor:
            params["sensor"] = sensor

        if period:
            params["period"] = period

        response = await self._request(
            "GET", f"devices/{device_id}/readings_by_date/", params=params
        )
        readings_data = response.json()

        # API response contains only sensors data, which matches Readings
        return Readings(**readings_data)

    async def async_get_all_readings_by_date(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sensor: str | None = None,
        period: str | None = None,
    ) -> list[DeviceReadings]:
        """Get telemetry readings for all devices within a date range.

        Args:
            start_date: Optional start date. Use 'today' or format 'YYYY-MM-DD'. If omitted, returns latest data.
            end_date: Optional end date. Use 'today' or format 'YYYY-MM-DD'. If omitted, returns latest data.
            sensor: Optional sensor name to filter (e.g., "temperature", "pm2p5"). Leave blank for all sensors.
            period: Optional data aggregation period. Values: "day" or "hour".

        Returns:
            List of DeviceReadings objects, each containing device metadata and sensor readings

        Raises:
            AuthError: Authentication failed (401/403)
            ApiError: API errors including 413 (range too large)
            RateLimitError: Rate limit exceeded (429)
            NetworkError: Network connectivity issues
        """
        # Build query parameters
        params: dict[str, str] = {}

        if start_date is not None:
            params["start-date"] = start_date

        if end_date is not None:
            params["end-date"] = end_date

        if sensor:
            params["sensor"] = sensor

        if period:
            params["period"] = period

        response = await self._request(
            "GET", "devices/all_readings_by_date/", params=params
        )
        response_data = response.json()

        # API response is wrapped in a "devices" key
        devices_list = response_data.get("devices", [])
        return [DeviceReadings(**device) for device in devices_list]
