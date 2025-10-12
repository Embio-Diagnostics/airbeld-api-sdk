"""Tests for Airbeld API exceptions."""

from airbeld.exceptions import (
    AirbeldError,
    ApiError,
    AuthError,
    NetworkError,
    RateLimitError,
)


def test_airbeld_error_base():
    """Test base AirbeldError exception."""
    error = AirbeldError("Base error message")
    assert str(error) == "Base error message"
    assert error.message == "Base error message"
    assert isinstance(error, Exception)


def test_auth_error():
    """Test AuthError with default and custom messages."""
    # Default message
    error_default = AuthError()
    assert str(error_default) == "Authentication failed"
    assert error_default.message == "Authentication failed"
    assert isinstance(error_default, AirbeldError)

    # Custom message
    error_custom = AuthError("Invalid token provided")
    assert str(error_custom) == "Invalid token provided"
    assert error_custom.message == "Invalid token provided"


def test_rate_limit_error():
    """Test RateLimitError with optional retry_after."""
    # Default message, no retry_after
    error_default = RateLimitError()
    assert str(error_default) == "Rate limit exceeded"
    assert error_default.message == "Rate limit exceeded"
    assert error_default.retry_after is None
    assert isinstance(error_default, AirbeldError)

    # Custom message with retry_after
    error_with_retry = RateLimitError("Too many requests", retry_after=60)
    assert str(error_with_retry) == "Too many requests"
    assert error_with_retry.message == "Too many requests"
    assert error_with_retry.retry_after == 60


def test_api_error():
    """Test ApiError with status code and optional response body."""
    # Minimal API error
    error_minimal = ApiError("Bad request", 400)
    assert str(error_minimal) == "Bad request"
    assert error_minimal.message == "Bad request"
    assert error_minimal.status_code == 400
    assert error_minimal.response_body is None
    assert isinstance(error_minimal, AirbeldError)

    # API error with response body
    response_body = '{"error": "validation_failed", "details": "Missing required field"}'
    error_with_body = ApiError("Validation failed", 422, response_body)
    assert str(error_with_body) == "Validation failed"
    assert error_with_body.message == "Validation failed"
    assert error_with_body.status_code == 422
    assert error_with_body.response_body == response_body


def test_network_error():
    """Test NetworkError with default and custom messages."""
    # Default message
    error_default = NetworkError()
    assert str(error_default) == "Network error occurred"
    assert error_default.message == "Network error occurred"
    assert isinstance(error_default, AirbeldError)

    # Custom message
    error_custom = NetworkError("Connection timeout after 30 seconds")
    assert str(error_custom) == "Connection timeout after 30 seconds"
    assert error_custom.message == "Connection timeout after 30 seconds"


def test_exception_inheritance():
    """Test that all custom exceptions inherit correctly."""
    errors = [
        AirbeldError("base"),
        AuthError("auth"),
        RateLimitError("rate"),
        ApiError("api", 500),
        NetworkError("network"),
    ]

    for error in errors:
        assert isinstance(error, AirbeldError)
        assert isinstance(error, Exception)


def test_string_representation_safe():
    """Test that string representations don't leak sensitive information."""
    # Ensure no secrets are accidentally exposed in error messages
    auth_error = AuthError("Invalid Bearer token: abc123...")
    api_error = ApiError("Server error", 500, '{"token": "secret123"}')

    # String representation should match the message exactly
    assert str(auth_error) == "Invalid Bearer token: abc123..."
    assert str(api_error) == "Server error"

    # Response body is separate and only accessible via attribute
    assert api_error.response_body == '{"token": "secret123"}'


def test_error_attributes_preserved():
    """Test that error attributes are properly preserved."""
    rate_error = RateLimitError("Custom rate limit message", retry_after=120)
    api_error = ApiError("Internal server error", 500, '{"error": "db_timeout"}')

    # Attributes should be accessible
    assert rate_error.retry_after == 120
    assert api_error.status_code == 500
    assert api_error.response_body == '{"error": "db_timeout"}'

    # Messages should be preserved
    assert rate_error.message == "Custom rate limit message"
    assert api_error.message == "Internal server error"
