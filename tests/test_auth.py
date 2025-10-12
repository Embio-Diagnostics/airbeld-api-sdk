"""Tests for Airbeld API authentication."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from airbeld.auth import async_login
from airbeld.exceptions import ApiError, AuthError, NetworkError, RateLimitError
from airbeld.models import TokenSet


@pytest.fixture
def sample_token_response():
    """Sample token response with camelCase keys."""
    return {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sample",
        "refreshToken": "refresh_abc123def456",
        "expiresIn": 86400,
        "tokenType": "Bearer",
    }


@pytest.fixture
def mock_response():
    """Create a mock response helper."""

    def _mock_response(status_code=200, json_data=None, headers=None):
        response = AsyncMock(spec=httpx.Response)
        response.status_code = status_code
        response.is_success = 200 <= status_code < 300
        response.json.return_value = json_data or {}
        response.headers = headers or {}
        response.text = str(json_data) if json_data else ""
        return response

    return _mock_response


@pytest.mark.asyncio
async def test_async_login_happy_path(sample_token_response, mock_response):
    """Test successful login returns TokenSet from sample response."""
    response = mock_response(200, sample_token_response)

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        result = await async_login(
            base_url="https://api.airbeld.com",
            email="user@example.com",
            password="password123",
        )

        # Verify TokenSet with proper snake_case fields
        assert isinstance(result, TokenSet)
        assert result.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sample"
        assert result.refresh_token == "refresh_abc123def456"
        assert result.expires_in == 86400
        assert result.token_type == "Bearer"

        # Verify request was made correctly
        mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
            "https://api.airbeld.com/api/v1/auth/token/",
            json={"email": "user@example.com", "password": "password123"},
            headers={
                "User-Agent": "airbeld-api-sdk/0.0.0",
                "Content-Type": "application/json",
            },
        )


@pytest.mark.asyncio
async def test_async_login_url_construction():
    """Test URL construction with different base URLs."""
    sample_response = {
        "accessToken": "token",
        "refreshToken": "refresh",
        "expiresIn": 3600,
        "tokenType": "Bearer",
    }
    response = AsyncMock(spec=httpx.Response)
    response.status_code = 200
    response.is_success = True
    response.json.return_value = sample_response

    test_cases = [
        ("https://api.airbeld.com", "https://api.airbeld.com/api/v1/auth/token/"),
        ("https://api.airbeld.com/", "https://api.airbeld.com/api/v1/auth/token/"),
        (
            "https://staging.airbeld.com",
            "https://staging.airbeld.com/api/v1/auth/token/",
        ),
    ]

    for base_url, expected_url in test_cases:
        with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = response

            await async_login(base_url=base_url, email="test@example.com", password="pass")

            mock_client.return_value.__aenter__.return_value.post.assert_called_once()
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            assert call_args[0][0] == expected_url


@pytest.mark.asyncio
async def test_async_login_401_invalid_credentials(mock_response):
    """Test 401 invalid credentials raises AuthError."""
    error_response = {"error": "Invalid credentials"}
    response = mock_response(401, error_response)

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        with pytest.raises(AuthError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="wrong@example.com",
                password="wrongpass",
            )

        assert str(exc_info.value) == "Invalid credentials"


@pytest.mark.asyncio
async def test_async_login_429_with_retry_after(mock_response):
    """Test 429 with Retry-After header raises RateLimitError."""
    error_response = {"error": "Rate limit exceeded"}
    headers = {"Retry-After": "30"}
    response = mock_response(429, error_response, headers)

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="user@example.com",
                password="password123",
            )

        assert str(exc_info.value) == "Rate limit exceeded"
        assert exc_info.value.retry_after == 30


@pytest.mark.asyncio
async def test_async_login_429_without_retry_after(mock_response):
    """Test 429 without Retry-After header raises RateLimitError."""
    error_response = {"error": "Rate limit exceeded"}
    response = mock_response(429, error_response)

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="user@example.com",
                password="password123",
            )

        assert str(exc_info.value) == "Rate limit exceeded"
        assert exc_info.value.retry_after is None


@pytest.mark.asyncio
async def test_async_login_400_bad_request(mock_response):
    """Test 400 bad request raises ApiError."""
    error_response = {"error": "Invalid request", "detail": "Missing email field"}
    response = mock_response(400, error_response)

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        with pytest.raises(ApiError) as exc_info:
            await async_login(base_url="https://api.airbeld.com", email="", password="password123")

        assert str(exc_info.value) == "Invalid request"
        assert exc_info.value.status_code == 400
        assert exc_info.value.response_body == str(error_response)


@pytest.mark.asyncio
async def test_async_login_500_server_error(mock_response):
    """Test 5xx server error raises ApiError."""
    error_response = {"error": "Server error"}
    response = mock_response(500, error_response)

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        with pytest.raises(ApiError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="user@example.com",
                password="password123",
            )

        assert str(exc_info.value) == "Server error"
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_async_login_malformed_error_response(mock_response):
    """Test malformed error response falls back to HTTP status."""
    # Response with no JSON or malformed JSON
    response = mock_response(404)
    response.json.side_effect = Exception("Invalid JSON")

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        with pytest.raises(ApiError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="user@example.com",
                password="password123",
            )

        assert str(exc_info.value) == "HTTP 404"
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_async_login_network_error():
    """Test network error raises NetworkError."""
    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.NetworkError(
            "Connection failed"
        )

        with pytest.raises(NetworkError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="user@example.com",
                password="password123",
            )

        assert "Network error: Connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_login_timeout_error():
    """Test timeout error raises NetworkError."""
    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException(
            "Request timeout"
        )

        with pytest.raises(NetworkError) as exc_info:
            await async_login(
                base_url="https://api.airbeld.com",
                email="user@example.com",
                password="password123",
            )

        assert "Request timeout: Request timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_login_custom_timeout():
    """Test custom timeout parameter is passed to httpx client."""
    sample_response = {
        "accessToken": "token",
        "refreshToken": "refresh",
        "expiresIn": 3600,
        "tokenType": "Bearer",
    }
    response = AsyncMock(spec=httpx.Response)
    response.status_code = 200
    response.is_success = True
    response.json.return_value = sample_response

    with patch("airbeld.auth.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = response

        await async_login(
            base_url="https://api.airbeld.com",
            email="user@example.com",
            password="password123",
            timeout=30.0,
        )

        # Verify AsyncClient was created with custom timeout
        mock_client.assert_called_once_with(timeout=30.0)
