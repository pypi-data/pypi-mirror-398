"""System fingerprinting for anonymous usage tracking."""

import hashlib
import platform

from zenable_mcp.usage.models import SystemInfo


def get_system_info() -> SystemInfo:
    """
    Collect high-level system information for fingerprinting.

    Returns:
        SystemInfo object with OS type, architecture, and Python version
    """
    return SystemInfo(
        os_type=platform.system(),  # "Linux", "Darwin", "Windows"
        architecture=platform.machine(),  # "x86_64", "arm64", "AMD64"
        python_version=platform.python_version(),  # "3.11.5"
    )


def create_system_hash(system_info: SystemInfo) -> str:
    """
    Create a deterministic SHA256 hash from system information.

    This hash is used to group usage from the same system without
    tracking user identity. The same system will always produce
    the same hash.

    Args:
        system_info: SystemInfo object containing system details

    Returns:
        SHA256 hash (64 character hex string)
    """
    # Create deterministic string representation
    fingerprint_string = (
        f"{system_info.os_type}|{system_info.architecture}|{system_info.python_version}"
    )

    # Hash it
    return hashlib.sha256(fingerprint_string.encode("utf-8")).hexdigest()


def get_system_fingerprint() -> tuple[SystemInfo, str]:
    """
    Get system info and its hash for anonymous tracking.

    Returns:
        Tuple of (SystemInfo, hash_string)
    """
    system_info = get_system_info()
    system_hash = create_system_hash(system_info)
    return system_info, system_hash
