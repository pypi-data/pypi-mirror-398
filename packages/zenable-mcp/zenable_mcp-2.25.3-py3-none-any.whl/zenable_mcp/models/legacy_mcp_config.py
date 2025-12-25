"""Legacy Pydantic models for MCP configuration validation."""

import os
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from zenable_mcp.logging.logged_echo import echo

# Constants
ZENABLE_MCP_ENDPOINT = os.environ.get(
    "ZENABLE_MCP_ENDPOINT", "https://mcp.zenable.app/"
)

# Legacy endpoint for backwards compatibility
LEGACY_ZENABLE_MCP_ENDPOINT = "https://mcp.www.zenable.app/"


class _LegacyClaudeCodeMCPServerConfig_2025_08(BaseModel):
    """Legacy Claude Code MCP server configuration (command-based format with mcp-remote).

    This was the original format used before SSE support was added in 2025-08.
    Example:
    {
        "command": "npx",
        "args": ["-y", "--", "mcp-remote@latest", "https://...", "--header", "API_KEY:..."]
    }
    """

    command: str = Field(..., description="The command to execute")
    args: list[str] = Field(..., description="Arguments for the command")

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility

    @field_validator("command")
    def validate_command(cls, v):
        if v != "npx":
            raise ValueError(
                f"Legacy Claude Code MCP must use 'npx' command, got '{v}'"
            )
        return v

    @field_validator("args")
    def validate_args(cls, v):
        if not v:
            raise ValueError("Args cannot be empty")

        # Check for required components
        args_str = " ".join(v)

        if "mcp-remote" not in args_str:
            raise ValueError("Args must include 'mcp-remote'")

        # Check for endpoint (current or legacy)
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        legacy_endpoint = LEGACY_ZENABLE_MCP_ENDPOINT.rstrip("/")
        if current_endpoint not in args_str and legacy_endpoint not in args_str:
            raise ValueError(
                f"Args must include Zenable MCP endpoint: {current_endpoint} or {legacy_endpoint}"
            )

        # Check for API key
        has_api_key = any("API_KEY:" in arg for arg in v)
        if not has_api_key:
            raise ValueError("Args must include API_KEY header")

        return v


class _LegacyGenericMCPServerConfig_2025_08(BaseModel):
    """Generic legacy MCP server configuration for all IDEs.

    This format was commonly used across different IDEs, last used in 2025-08.
    Example:
    {
        "command": "npx",
        "args": ["-y", "zenable-mcp"],
        "env": {}
    }
    """

    command: str = Field(..., description="The command to execute")
    args: list[str] = Field(..., description="Arguments for the command")
    env: Optional[dict[str, str]] = Field(
        default=None, description="Environment variables"
    )

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility

    @field_validator("command")
    def validate_command(cls, v):
        if v != "npx":
            raise ValueError(f"Legacy MCP must use 'npx' command, got '{v}'")
        return v

    @field_validator("args")
    def validate_args(cls, v):
        if not v:
            raise ValueError("Args cannot be empty")

        # Check for zenable-mcp in args
        args_str = " ".join(v)
        if "zenable-mcp" not in args_str:
            raise ValueError("Args must include 'zenable-mcp'")

        return v


class _LegacyMCPServerConfig_2025_08(BaseModel):
    """Legacy Base model for MCP server configuration."""

    command: str = Field(..., description="The command to execute")
    args: list[str] = Field(
        default_factory=list, description="Arguments for the command"
    )
    disabled: Optional[bool] = Field(
        default=None,
        description="Whether the server is disabled",
    )
    alwaysAllow: Optional[list[str]] = Field(
        default=None,
        description="Tools to always allow without prompting",
    )
    autoApprove: Optional[list[str]] = Field(
        default=None,
        description="Tools to auto-approve",
    )
    trust: Optional[bool] = Field(
        default=None,
        description="Whether to trust this server",
    )

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility


class _LegacyZenableMCPConfig_2025_08(_LegacyMCPServerConfig_2025_08):
    """Legacy Zenable-specific MCP server configuration."""

    command: str = Field(default="npx", description="The command to execute")
    args: list[str] = Field(
        ..., description="Arguments including mcp-remote and API key"
    )

    @field_validator("command")
    def validate_command(cls, v):
        if v != "npx":
            raise ValueError(f"Zenable MCP must use 'npx' command, got '{v}'")
        return v

    @field_validator("args")
    def validate_args(cls, v):
        if not v:
            raise ValueError("Args cannot be empty")

        # Check for required components
        args_str = " ".join(v)

        if "mcp-remote" not in args_str:
            raise ValueError("Args must include 'mcp-remote'")

        endpoint_base = ZENABLE_MCP_ENDPOINT.rstrip("/")
        if endpoint_base not in args_str:
            raise ValueError(f"Args must include Zenable MCP endpoint: {endpoint_base}")

        # Check for API key
        has_api_key = any("API_KEY:" in arg for arg in v)
        if not has_api_key:
            raise ValueError("Args must include API_KEY header")

        return v

    @model_validator(mode="after")
    def validate_mcp_remote_version(self):
        """Validate that mcp-remote uses @latest version."""
        for arg in self.args:
            if "mcp-remote@" in arg and "@latest" not in arg:
                raise ValueError(f"mcp-remote must use @latest version, got: {arg}")
        return self


class _LegacyRooMCPConfig_2025_08(_LegacyMCPServerConfig_2025_08):
    """Legacy Roo-specific MCP configuration with strict requirements."""

    disabled: bool = Field(default=False, description="Must be explicitly set to false")
    alwaysAllow: list[str] = Field(
        default_factory=lambda: ["conformance_check"],
        description="Must include conformance_check",
    )

    @field_validator("disabled")
    def validate_disabled(cls, v):
        if v is not False:
            raise ValueError(f"Roo MCP must have disabled=false, got {v}")
        return v

    @field_validator("alwaysAllow")
    def validate_always_allow(cls, v):
        if "conformance_check" not in v:
            raise ValueError("Roo MCP must have 'conformance_check' in alwaysAllow")
        return v


class _LegacyGeminiMCPConfig_2025_08(_LegacyMCPServerConfig_2025_08):
    """Legacy Gemini CLI-specific MCP configuration."""

    trust: bool = Field(default=True, description="Must be set to true")

    @field_validator("trust")
    def validate_trust(cls, v):
        if v is not True:
            raise ValueError(f"Gemini MCP must have trust=true, got {v}")
        return v


class _LegacyVSCodeMCPConfig_2025_09(BaseModel):
    """Legacy VS Code-specific MCP server configuration."""

    type: Literal["sse"] = Field(default="sse", description="Server type")
    url: str = Field(..., description="URL for SSE server")

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility

    @field_validator("url")
    def validate_url(cls, v):
        if not v:
            raise ValueError("URL cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        legacy_endpoint = LEGACY_ZENABLE_MCP_ENDPOINT.rstrip("/")
        if current_endpoint not in v and legacy_endpoint not in v:
            raise ValueError(
                f"URL must be Zenable MCP endpoint: {current_endpoint} or {legacy_endpoint}, got '{v}'"
            )
        return v


class _LegacyClaudeCodeMCPConfig_2025_09(BaseModel):
    """Legacy Claude Code-specific MCP server configuration."""

    type: Literal["sse"] = Field(default="sse", description="Server type")
    url: str = Field(..., description="URL for SSE server")
    headers: dict = Field(..., description="HTTP headers with API key")

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility

    @field_validator("url")
    def validate_url(cls, v):
        if not v:
            raise ValueError("URL cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        legacy_endpoint = LEGACY_ZENABLE_MCP_ENDPOINT.rstrip("/")
        if current_endpoint not in v and legacy_endpoint not in v:
            raise ValueError(
                f"URL must be Zenable MCP endpoint: {current_endpoint} or {legacy_endpoint}, got '{v}'"
            )
        return v


class _LegacyAmazonQMCPConfig_2025_09(BaseModel):
    """Legacy Amazon Q-specific MCP configuration."""

    url: str = Field(..., description="URL for the MCP server")
    disabled: bool = Field(default=False, description="Whether the server is disabled")
    timeout: int = Field(default=3000, description="Timeout in milliseconds")
    headers: dict[str, str] = Field(..., description="HTTP headers with API key")

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility

    @field_validator("url")
    def validate_url(cls, v):
        if not v:
            raise ValueError("URL cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        legacy_endpoint = LEGACY_ZENABLE_MCP_ENDPOINT.rstrip("/")
        if current_endpoint not in v and legacy_endpoint not in v:
            raise ValueError(
                f"URL must be Zenable MCP endpoint: {current_endpoint} or {legacy_endpoint}, got '{v}'"
            )
        return v

    @field_validator("disabled")
    def validate_disabled(cls, v):
        if v is not False:
            raise ValueError(f"Amazon Q MCP must have disabled=false, got {v}")
        return v

    @field_validator("headers")
    def validate_headers(cls, v):
        if not v:
            raise ValueError("Headers cannot be empty")
        if "API_KEY" not in v:
            raise ValueError("Headers must include API_KEY")
        if not v.get("API_KEY"):
            raise ValueError("API_KEY header cannot be empty")
        return v


class _LegacyGenericMcpServerConfig_2025_09_sse(BaseModel):
    """legacy Generic MCP server configuration for use when making other generic configs (when we used sse)"""

    disabled: Optional[bool] = Field(
        default=None, description="Whether the server is disabled"
    )
    alwaysAllow: Optional[list[str]] = Field(
        default=None, description="Tools to always allow without prompting"
    )
    autoApprove: Optional[list[str]] = Field(
        default=None, description="Tools to auto-approve"
    )
    trust: Optional[bool] = Field(
        default=None, description="Whether to trust this server"
    )

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional fields for flexibility


class _LegacyGenericMCPRemoteServerConfig_2025_09_sse(
    _LegacyGenericMcpServerConfig_2025_09_sse
):
    """Legacy Generic MCP Remote server configuration for all IDEs with OAuth format over sse."""

    type: Literal["http", "streamable-http", "sse"] = Field(
        default="sse", description="Server type"
    )
    url: str = Field(default=ZENABLE_MCP_ENDPOINT, description="URL for the server")

    model_config = ConfigDict(strict=False, extra="forbid")


class _LegacyGenericMCPStdioServerConfig_2025_09_sse(
    _LegacyGenericMcpServerConfig_2025_09_sse
):
    """Legacy Generic MCP Stdio server configuration for all IDEs with OAuth format over sse."""

    command: Literal["npx"] = Field(
        default="npx", description="Command to execute for stdio server"
    )
    args: list[str] = Field(
        # We don't use mcp-remote@latest because the OAuth creds are per-mcp-remote version and we want them cached as long as possible
        # while we work on making this no longer necessary
        default_factory=lambda: ["-y", "--", "mcp-remote", ZENABLE_MCP_ENDPOINT],
        description="Arguments for the command",
    )

    model_config = ConfigDict(strict=False, extra="forbid")

    @field_validator("command")
    def validate_command(cls, v):
        if v != "npx":
            raise ValueError(f"Zenable MCP must use 'npx' command, got '{v}'")
        return v

    @field_validator("args")
    def validate_args(cls, v):
        if not v:
            raise ValueError("Args cannot be empty")

        # Check for required components
        args_str = " ".join(v)

        if "mcp-remote" not in args_str:
            raise ValueError("Args must include 'mcp-remote'")

        endpoint_base = ZENABLE_MCP_ENDPOINT.rstrip("/")
        if endpoint_base not in args_str:
            raise ValueError(f"Args must include Zenable MCP endpoint: {endpoint_base}")

        return v


class _LegacyGeminiMCPConfig_2025_09_sse(
    _LegacyGenericMCPRemoteServerConfig_2025_09_sse
):
    """Legacy Gemini CLI-specific MCP configuration with OAuth format over sse."""

    oauth: dict[str, bool] = Field(
        default={"enabled": True}, description="OAuth configuration"
    )
    trust: bool = Field(default=True, description="Must be set to true")

    @field_validator("trust")
    def validate_trust(cls, v):
        if v is not True:
            raise ValueError(f"Gemini MCP must have trust=true, got {v}")
        return v

    @field_validator("oauth")
    def validate_oauth(cls, v):
        if not isinstance(v, dict):
            raise ValueError("oauth must be a dictionary")
        if v.get("enabled") is not True:
            raise ValueError("oauth.enabled must be true")
        return v


class _LegacyClaudeCodeMCPConfig_2025_09_sse(
    _LegacyGenericMCPRemoteServerConfig_2025_09_sse
):
    """Legacy Claude Code-specific MCP server configuration with OAuth over sse."""

    # We just use the defaults


class _LegacyVSCodeMCPConfig_2025_09_sse(
    _LegacyGenericMCPRemoteServerConfig_2025_09_sse
):
    """Legacy VS Code-specific MCP server configuration with OAuth over sse."""

    # We just use the defaults


class _LegacyContinueMCPServerEntry_2025_09_sse(BaseModel):
    """Legacy Individual MCP server entry for Continue configuration with OAuth over sse."""

    name: str = Field(default="Zenable", description="Server name")
    type: Literal["sse"] = Field(default="sse", description="Server type")
    url: str = Field(default=ZENABLE_MCP_ENDPOINT, description="Server URL")

    # Strict mode since we expect to own this entire configuration
    model_config = ConfigDict(strict=True, extra="forbid")


def _create_default_continue_servers() -> list[
    _LegacyContinueMCPServerEntry_2025_09_sse
]:
    """Create default Continue MCP server entries with proper error handling."""
    try:
        entry = _LegacyContinueMCPServerEntry_2025_09_sse()
        return [entry]
    except ValidationError as e:
        # If we can't create the default server, re-raise the exception
        echo(f"Failed to create default Continue MCP server: {e}", err=True)
        raise


class _LegacyContinueMCPConfig_2025_09_sse(BaseModel):
    """Legacy Continue-specific complete configuration file structure using sse.

    This represents the entire YAML file for Continue MCP configuration.
    We use strict mode because we expect to own and control the entire file.
    """

    name: str = Field(default="Zenable", description="Configuration name")
    version: str = Field(description="Version of zenable_mcp")
    schema_version: str = Field(
        default="v1", alias="schema", description="Schema version"
    )
    mcpServers: list[_LegacyContinueMCPServerEntry_2025_09_sse] = Field(
        default_factory=lambda: _create_default_continue_servers(),
        description="List of MCP servers",
    )

    # Strict mode because we expect to own the entire file
    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True)
