"""HTTP client for sending usage data to public_api."""

import json
import logging
import os
from http.client import HTTPException

import requests

from zenable_mcp.usage.models import ZenableMcpUsagePayload

LOG = logging.getLogger(__name__)

# Base Zenable URL (override with ZENABLE_URL env var)
_zenable_url = os.environ.get("ZENABLE_URL", "https://www.zenable.app").rstrip("/")

# Public API endpoint
PUBLIC_API_URL = f"{_zenable_url}/api/public/usage"

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 5


def send_usage_data(payload: ZenableMcpUsagePayload) -> None:
    """
    Send usage data to public_api endpoint.

    This function is non-blocking and will not raise exceptions.
    All failures are logged but don't affect the main command.

    Args:
        payload: ZenableMcpUsagePayload to send
    """
    try:
        # Serialize payload to JSON
        usage_data_payload = {
            "activity_type": payload.usage_data.activity_type,
            "event": payload.usage_data.event,
            "timestamp": payload.usage_data.timestamp.isoformat(),
            "duration_ms": payload.usage_data.duration_ms,
            "command_args": payload.usage_data.command_args,
            "zenable_mcp_version": payload.usage_data.zenable_mcp_version,
            "data": payload.usage_data.data,
        }

        request_body = {
            "integration": payload.integration,
            "system_hash": payload.system_hash,
            "schema_version": payload.schema_version,
            "system_info": payload.system_info.model_dump(),
            "usage_data": usage_data_payload,
        }

        # Send POST request (no authentication)
        response = requests.post(
            PUBLIC_API_URL,
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )

        # Log response (2xx = success)
        if 200 <= response.status_code < 300:
            LOG.debug(f"Usage data sent successfully (HTTP {response.status_code})")
        else:
            LOG.debug(
                f"Usage tracking failed: HTTP {response.status_code} - {response.text}"
            )

    except requests.exceptions.Timeout:
        LOG.debug("Usage tracking timeout - request took too long")
    except requests.exceptions.ConnectionError:
        LOG.debug("Usage tracking failed - connection error")
    except HTTPException:
        LOG.debug("Usage tracking failed - HTTP error", exc_info=True)
    except json.JSONDecodeError:
        LOG.debug("Usage tracking failed - JSON encoding error", exc_info=True)
    except Exception:
        # Catch all other exceptions to ensure we never break the main command
        LOG.debug("Usage tracking failed unexpectedly", exc_info=True)
