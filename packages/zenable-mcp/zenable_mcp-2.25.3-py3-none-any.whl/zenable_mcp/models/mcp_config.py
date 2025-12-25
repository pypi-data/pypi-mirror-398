"""Pydantic models for MCP configuration validatoon."""

import os
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from zenable_mcp.logging.logged_echo import echo

ZENABLE_MCP_ENDPOINT = (
    os.environ.get("ZENABLE_MCP_ENDPOINT", "https://mcp.zenable.app/").rstrip("/") + "/"
)


class _GenericMcpServerConfig(BaseModel):
    """Generic MCP server configuration for use when making other generic configs."""

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


class _GenericMCPRemoteServerConfig(_GenericMcpServerConfig):
    """Generic MCP Remote server configuration for all IDEs with OAuth format."""

    type: Literal["http", "streamable-http"] = Field(
        default="http", description="Server type"
    )
    url: str = Field(
        default_factory=lambda: ZENABLE_MCP_ENDPOINT, description="URL for the server"
    )

    model_config = ConfigDict(strict=False, extra="forbid")

    @field_validator("url")
    def validate_url(cls, v):
        """Validate that URL uses the current endpoint (rejects legacy URLs to trigger upgrade)."""
        if not v:
            raise ValueError("URL cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        # Explicitly reject legacy URL to trigger upgrade detection
        if "mcp.www.zenable.app" in v:
            raise ValueError(
                f"Legacy URL detected: {v}. Please upgrade to {current_endpoint}"
            )
        if current_endpoint not in v:
            raise ValueError(
                f"URL must use current Zenable MCP endpoint: {current_endpoint}, got '{v}'"
            )
        return v


class _GenericMCPStdioServerConfig(_GenericMcpServerConfig):
    """Generic MCP Stdio server configuration for all IDEs with OAuth format."""

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

        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        # Explicitly reject legacy URL to trigger upgrade detection
        if "mcp.www.zenable.app" in args_str:
            raise ValueError(
                f"Legacy URL detected in args. Please upgrade to {current_endpoint}"
            )
        if current_endpoint not in args_str:
            raise ValueError(
                f"Args must include current Zenable MCP endpoint: {current_endpoint}"
            )

        return v


class _RooMCPConfig(_GenericMCPStdioServerConfig):
    """Roo-specific MCP configuration with strict requirements."""

    # This can move to OAuth when this issue is fixed: https://github.com/RooCodeInc/Roo-Code/issues/7296

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


class _KiroMCPConfig(_GenericMCPRemoteServerConfig):
    """Kiro-specific MCP configuration with OAuth format.

    Kiro now supports remote servers directly via OAuth.
    See https://kiro.dev/docs/mcp/configuration/ for details.
    """

    # We just use the defaults from _GenericMCPRemoteServerConfig


class _WindsurfMCPConfig(BaseModel):
    """Windsurf-specific MCP configuration.

    Windsurf uses 'serverUrl' instead of 'url' for the server endpoint.
    Note: Windsurf does not support the 'type' field.
    """

    serverUrl: str = Field(
        default_factory=lambda: ZENABLE_MCP_ENDPOINT, description="URL for the server"
    )

    model_config = ConfigDict(strict=False, extra="forbid")

    @field_validator("serverUrl")
    def validate_server_url(cls, v):
        """Validate that serverUrl uses the current endpoint (rejects legacy URLs to trigger upgrade)."""
        if not v:
            raise ValueError("serverUrl cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        # Explicitly reject legacy URL to trigger upgrade detection
        if "mcp.www.zenable.app" in v:
            raise ValueError(
                f"Legacy URL detected: {v}. Please upgrade to {current_endpoint}"
            )
        if current_endpoint not in v:
            raise ValueError(
                f"serverUrl must use current Zenable MCP endpoint: {current_endpoint}, got '{v}'"
            )
        return v


class _GeminiMCPConfig(_GenericMCPRemoteServerConfig):
    """Gemini CLI-specific MCP configuration with OAuth format."""

    httpUrl: str = Field(
        default_factory=lambda: ZENABLE_MCP_ENDPOINT, description="URL for the server"
    )
    # We are "turning off" the url field, since it is replaced by httpUrl for streamable http in Gemini CLI
    url: str = Field(default=None, exclude=True)
    oauth: dict[str, bool] = Field(
        default={"enabled": True}, description="OAuth configuration"
    )
    trust: bool = Field(default=True, description="Must be set to true")

    @field_validator("httpUrl")
    def validate_http_url(cls, v):
        """Validate that httpUrl uses the current endpoint (rejects legacy URLs to trigger upgrade)."""
        if not v:
            raise ValueError("httpUrl cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        # Explicitly reject legacy URL to trigger upgrade detection
        if "mcp.www.zenable.app" in v:
            raise ValueError(
                f"Legacy URL detected: {v}. Please upgrade to {current_endpoint}"
            )
        if current_endpoint not in v:
            raise ValueError(
                f"httpUrl must use current Zenable MCP endpoint: {current_endpoint}, got '{v}'"
            )
        return v

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


class _ClaudeCodeMCPConfig(_GenericMCPRemoteServerConfig):
    """Claude Code-specific MCP server configuration with OAuth."""

    # We just use the defaults


class _VSCodeMCPConfig(_GenericMCPRemoteServerConfig):
    """VS Code-specific MCP server configuration with OAuth."""

    # We just use the defaults


class _CursorMCPConfig(_GenericMCPRemoteServerConfig):
    """Cursor-specific MCP server configuration with OAuth."""

    # We just use the defaults


class _CopilotCLIMCPConfig(_GenericMCPRemoteServerConfig):
    """GitHub Copilot CLI-specific MCP server configuration with OAuth."""

    tools: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Tools to enable - '*' for all tools",
    )


class _CodexMCPConfig(_GenericMCPRemoteServerConfig):
    """Codex-specific MCP server configuration with OAuth.

    Codex uses HTTP transport and requires experimental_use_rmcp_client at top level.
    """

    # We just use the defaults from _GenericMCPRemoteServerConfig


class _AntigravityMCPConfig(BaseModel):
    """Antigravity-specific MCP configuration.

    Antigravity uses 'type' and 'url' fields like standard remote servers,
    but the parent key is 'servers' instead of 'mcpServers'.
    """

    type: Literal["http"] = Field(default="http", description="Server type")
    url: str = Field(
        default_factory=lambda: ZENABLE_MCP_ENDPOINT, description="URL for the server"
    )

    model_config = ConfigDict(strict=False, extra="forbid")

    @field_validator("url")
    def validate_url(cls, v):
        """Validate that URL uses the current endpoint (rejects legacy URLs to trigger upgrade)."""
        if not v:
            raise ValueError("URL cannot be empty")
        current_endpoint = ZENABLE_MCP_ENDPOINT.rstrip("/")
        # Explicitly reject legacy URL to trigger upgrade detection
        if "mcp.www.zenable.app" in v:
            raise ValueError(
                f"Legacy URL detected: {v}. Please upgrade to {current_endpoint}"
            )
        if current_endpoint not in v:
            raise ValueError(
                f"URL must use current Zenable MCP endpoint: {current_endpoint}, got '{v}'"
            )
        return v


class _AmazonQMCPConfig(_GenericMCPStdioServerConfig):
    """Amazon Q-specific MCP configuration for OAuth authentication."""

    disabled: bool = Field(default=False, description="Whether the server is disabled")
    timeout: int = Field(default=5000, description="Timeout in milliseconds")

    @field_validator("disabled")
    def validate_disabled(cls, v):
        if v is not False:
            raise ValueError(f"Amazon Q MCP must have disabled=false, got {v}")
        return v


class _ContinueMCPServerEntry(_GenericMCPRemoteServerConfig):
    """Individual MCP server entry for Continue configuration with Oauth."""

    name: str = Field(default="Zenable", description="Server name")
    # Override type for Continue to use streamable-http as per Continue docs
    # https://docs.continue.dev/customize/deep-dives/mcp#how-to-use-streamable-http-transport
    type: Literal["streamable-http"] = Field(
        default="streamable-http", description="Server type"
    )

    # Strict mode since we expect to own this entire configuration
    model_config = ConfigDict(strict=True, extra="forbid")


def _create_default_continue_servers() -> list[_ContinueMCPServerEntry]:
    """Create default Continue MCP server entries with proper error handling."""
    try:
        entry = _ContinueMCPServerEntry()
        return [entry]
    except ValidationError as e:
        # If we can't create the default server, re-raise the exception
        echo(f"Failed to create default Continue MCP server: {e}", err=True)
        raise


class _ContinueMCPConfig(BaseModel):
    """Continue-specific complete configuration file structure.

    This represents the entire YAML file for Continue MCP configuration.
    We use strict mode because we expect to own and control the entire file.
    """

    name: str = Field(default="Zenable", description="Configuration name")
    version: str = Field(description="Version of zenable_mcp")
    schema_version: str = Field(
        default="v1", alias="schema", description="Schema version"
    )
    mcpServers: list[_ContinueMCPServerEntry] = Field(
        default_factory=lambda: _create_default_continue_servers(),
        description="List of MCP servers",
    )

    # Strict mode because we expect to own the entire file
    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True)


class _MCPConfigFile(BaseModel):
    """Model for the complete MCP configuration file."""

    mcpServers: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="MCP server configurations"
    )

    model_config = ConfigDict(
        strict=False, extra="allow"
    )  # Allow additional top-level fields
