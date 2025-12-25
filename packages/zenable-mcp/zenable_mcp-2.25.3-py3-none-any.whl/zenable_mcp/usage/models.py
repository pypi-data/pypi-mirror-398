"""Data models for usage tracking."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Schema version for the usage tracking payload format
# Update this when making breaking changes to the usage_data structure
USAGE_SCHEMA_VERSION = "1.0.0"


class SystemInfo(BaseModel):
    """High-level system information for grouping."""

    model_config = ConfigDict(strict=True)

    os_type: str  # e.g., "Linux", "Darwin", "Windows"
    architecture: str  # e.g., "x86_64", "arm64"
    python_version: str  # e.g., "3.11.5"


class UsageEventData(BaseModel):
    """Usage event data following activity/event pattern."""

    model_config = ConfigDict(strict=True)

    activity_type: str  # "check", "install_mcp", "install_hook", "hook"
    event: str  # "started", "completed", "cancelled"
    timestamp: datetime
    duration_ms: int
    command_args: list[str]  # CLI-style args like ["--dry-run", "--global"]
    zenable_mcp_version: str  # Version of zenable_mcp sending this event
    data: dict | None = None  # Activity-specific payload (outcome, stats, etc)


class ZenableMcpUsagePayload(BaseModel):
    """Usage data to send to public_api."""

    model_config = ConfigDict(strict=True)

    integration: str = "zenable_mcp"
    system_hash: str
    schema_version: str = USAGE_SCHEMA_VERSION
    system_info: SystemInfo
    usage_data: UsageEventData
