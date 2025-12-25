from typing import Optional

from zenable_mcp.exceptions import AuthenticationError
from zenable_mcp.usage.manager import get_jwt_token_from_cache
from zenable_mcp.user_config.config_handler import APIConfigHandler, ConfigHandler


def get_config_handler(api_base_url: Optional[str] = None) -> ConfigHandler:
    """
    Factory function to create a config handler for the CLI.

    This function creates an APIConfigHandler that fetches configuration from the
    Zenable API using the JWT token from OAuth authentication. The tenant is
    identified from the JWT token.

    Args:
        api_base_url: Optional base URL for the API (defaults to ZENABLE_URL env var)

    Returns:
        APIConfigHandler instance

    Raises:
        AuthenticationError: If no JWT token is available (user not authenticated)
    """
    jwt_token = get_jwt_token_from_cache()

    if not jwt_token:
        raise AuthenticationError(
            "Not authenticated. Please run 'zenable-mcp check' or another command to authenticate via OAuth."
        )

    return APIConfigHandler(jwt_token, api_base_url)
