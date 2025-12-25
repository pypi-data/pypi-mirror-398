"""Constants used across zenable_mcp."""

from pathlib import Path

# OAuth token cache directory
# This is where FastMCP stores OAuth tokens for authentication
OAUTH_TOKEN_CACHE_DIR = Path.home() / ".zenable" / "oauth-mcp-client-cache"
