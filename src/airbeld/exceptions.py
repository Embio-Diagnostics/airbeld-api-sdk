"""Custom exceptions for the Airbeld API SDK."""


class AirbeldError(Exception):
    """Base exception for all Airbeld SDK errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthError(AirbeldError):
    """Authentication or authorization error (401/403)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class RateLimitError(AirbeldError):
    """Rate limit exceeded error (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ApiError(AirbeldError):
    """API error for other 4xx/5xx HTTP status codes."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class NetworkError(AirbeldError):
    """Network connectivity or timeout error."""

    def __init__(self, message: str = "Network error occurred") -> None:
        super().__init__(message)
