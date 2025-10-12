"""Authentication utilities for the Airbeld API."""

from urllib.parse import urljoin

import httpx

from .exceptions import ApiError, AuthError, NetworkError, RateLimitError
from .models import TokenSet


async def async_login(
    base_url: str,
    email: str,
    password: str,
    *,
    timeout: float = 10.0,
) -> TokenSet:
    """Authenticate with email/password and get access token.

    Args:
        base_url: Base URL for the API (e.g., "https://api.airbeld.com")
        email: User email address
        password: User password
        timeout: Request timeout in seconds (default: 10.0)

    Returns:
        TokenSet containing access_token, refresh_token, expires_in, token_type

    Raises:
        AuthError: Authentication failed (401)
        ApiError: Other API errors (400, 429, 5xx)
        NetworkError: Network connectivity issues
    """
    url = urljoin(base_url.rstrip("/") + "/api/v1/", "auth/token/")

    payload: dict[str, str] = {
        "email": email,
        "password": password,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "User-Agent": "airbeld-api-sdk/0.0.0",
                    "Content-Type": "application/json",
                },
            )
            _handle_http_errors(response)
            token_data = response.json()
            return TokenSet(**token_data)

        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {e}") from e
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timeout: {e}") from e


def _handle_http_errors(response: httpx.Response) -> None:
    """Handle HTTP error responses."""
    if response.is_success:
        return

    status_code = response.status_code

    try:
        error_data = response.json()
        error_message = error_data.get("error", f"HTTP {status_code}")
    except Exception:
        error_message = f"HTTP {status_code}"

    if status_code == 401:
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
