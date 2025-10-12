# Home Assistant Authentication

## Overview

When using the Airbeld SDK within Home Assistant, authentication is handled automatically by the Home Assistant integration. You do not need to manually authenticate or manage tokens.

## How It Works

- **OAuth2 Flow**: Home Assistant performs the OAuth2 authentication flow with the Airbeld API
- **Token Management**: Home Assistant securely stores and manages access/refresh tokens
- **SDK Integration**: The integration provides ready JWT tokens to the SDK automatically
- **No Manual Auth**: Users never need to handle credentials or tokens directly

## For Home Assistant Users

If you're using Home Assistant:
- ✅ Use the official Home Assistant integration
- ✅ Authentication is handled automatically
- ❌ Do not use `async_login()` from this SDK
- ❌ Do not manually manage tokens

## For Non-Home Assistant Users

If you're building standalone applications (CLI tools, scripts, demos):
- ✅ Use `async_login(email, password)` for authentication
- ✅ Manage tokens manually as needed
- ✅ See the main [README.md](../README.md) for examples

## References

- TODO: Link to official Home Assistant Airbeld integration docs
- TODO: Link to Home Assistant OAuth2 documentation
- TODO: Link to Airbeld API authentication guide

---

**Note**: This SDK's `async_login()` function is designed for standalone usage outside of Home Assistant. The Home Assistant integration uses a different authentication path optimized for the HA ecosystem.