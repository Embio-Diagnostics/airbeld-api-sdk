"""Version information for airbeld-api-sdk."""

__version__ = "0.1.1"


def get_user_agent() -> str:
    """Get the User-Agent string for SDK requests."""
    return f"airbeld-api-sdk/{__version__}"
