import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

import requests
from pydantic import ValidationError

from zenable_mcp.user_config.config_parser import UserDBConfigParser
from zenable_mcp.user_config.data_models import DEFAULT_CONFIG, FindingType, UserConfig

LOG = logging.getLogger(__name__)

# Timeout for API requests (in seconds)
API_REQUEST_TIMEOUT = 10


class ConfigHandler(ABC):
    """
    Abstract class for config handlers.
    """

    @abstractmethod
    def load_config(self) -> tuple[UserConfig, Optional[str]]:
        """
        Load the user config.

        Returns:
            Tuple of (config, error_message)
        """


class DBConfigHandler(ConfigHandler):
    """
    Config handler for database-stored user config.
    """

    def __init__(self, tenant_config: Optional[dict]):
        """
        Initialize with tenant config from database.

        Args:
            tenant_config: Dictionary containing the tenant configuration.
                          None means no config (use defaults).
        """
        self.tenant_config = tenant_config

    def load_config(self) -> tuple[UserConfig, Optional[str]]:
        """
        Load config by merging tenant config with DEFAULT_CONFIG.

        Returns:
            Tuple of (config, error_message)
            - config: The merged config or default config if loading failed
            - error_message: Error message if config loading/validation failed, None otherwise
        """
        # If no config, return default config
        if not self.tenant_config:
            LOG.debug(
                "No tenant config in DB, using the Zenable defaults...",
            )
            return DEFAULT_CONFIG, None

        try:
            # Use the DB config parser to validate and merge with defaults
            # It's not a parser, but we keep the same interface for consistency
            parser = UserDBConfigParser()

            # Get the merged config from the DB config
            merged_config, warning = parser.get_config_from_dict(self.tenant_config)

            if warning:
                LOG.exception(
                    f"Tenant DB config loaded, found extra fields. {warning}. This shouldn't "
                    "happen, it probably means that there's a data inconsistency in the DB."
                )
            else:
                LOG.info(
                    "Tenant DB config loaded successfully.",
                )

            return merged_config, warning
        except Exception:
            error_message = (
                "Internal error: Failed to load tenant configuration. Using defaults."
            )
            LOG.exception(error_message)
            return DEFAULT_CONFIG, error_message


class APIConfigHandler(ConfigHandler):
    """
    Config handler that fetches tenant configuration from the Zenable API.

    This handler is used by the CLI to retrieve configuration stored in the database
    via the data_api endpoint. It uses the JWT token from OAuth authentication to
    identify the tenant.
    """

    def __init__(self, jwt_token: str, api_base_url: Optional[str] = None):
        """
        Initialize with JWT token for authentication.

        Args:
            jwt_token: JWT token from OAuth flow containing tenant information
            api_base_url: Base URL for the API (defaults to ZENABLE_URL env var or production)
        """
        self.jwt_token = jwt_token
        self.api_base_url = (
            api_base_url or os.environ.get("ZENABLE_URL", "https://www.zenable.app")
        ).rstrip("/")
        self.config_endpoint = f"{self.api_base_url}/api/data/tenant-config"

    def _preprocess_api_config(self, config_dict: dict) -> None:
        """
        Preprocess config dict from API to handle serialization issues.

        The API returns model_dump() which serializes:
        - sets as lists (e.g., skip_branches)
        - enum keys as strings (e.g., findings dict keys)

        This method modifies the config_dict in place.
        """
        # Handle pr_reviews section
        if "pr_reviews" in config_dict:
            pr_reviews = config_dict["pr_reviews"]

            # Convert skip_branches from list to set
            if "skip_branches" in pr_reviews and isinstance(
                pr_reviews["skip_branches"], list
            ):
                pr_reviews["skip_branches"] = set(pr_reviews["skip_branches"])

            # Convert findings dict keys from strings to FindingType enums
            if "findings" in pr_reviews and isinstance(pr_reviews["findings"], dict):
                converted_findings = {}
                for key, val in pr_reviews["findings"].items():
                    # If key is already a FindingType, keep it
                    if isinstance(key, FindingType):
                        converted_findings[key] = val
                    # If key is a string, convert to FindingType
                    elif isinstance(key, str):
                        try:
                            converted_findings[FindingType(key)] = val
                        except ValueError:
                            # Skip invalid finding types
                            LOG.warning(f"Skipping invalid finding type: {key}")
                            continue
                pr_reviews["findings"] = converted_findings

    def load_config(self) -> tuple[UserConfig, Optional[str]]:
        """
        Load config by fetching from the API.

        The tenant_uid is implicitly identified from the JWT token.

        Returns:
            Tuple of (config, error_message)
            - config: The merged config or default config if loading failed
            - error_message: Error message if config loading failed, None otherwise
        """
        try:
            # Make authenticated request to get tenant config
            response = requests.get(
                self.config_endpoint,
                headers={
                    "Authorization": f"Bearer {self.jwt_token}",
                    "Content-Type": "application/json",
                },
                timeout=API_REQUEST_TIMEOUT,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract merged_config from response
            merged_config_dict = data.get("merged_config")
            if not merged_config_dict:
                error_message = "API response missing merged_config field"
                LOG.exception(error_message)
                return DEFAULT_CONFIG, error_message

            # Preprocess merged_config to handle serialization issues from API
            # The API returns model_dump() which serializes:
            # - sets as lists
            # - enum keys as strings
            self._preprocess_api_config(merged_config_dict)

            # Parse merged config into UserConfig model
            try:
                merged_config = UserConfig(**merged_config_dict)
            except ValidationError as e:
                error_message = f"Invalid config from API: {e}"
                LOG.exception(error_message)
                return DEFAULT_CONFIG, error_message

            # Get any config error from the API response
            config_error = data.get("config_error")

            if config_error:
                LOG.warning(f"Config loaded with warning: {config_error}")
            else:
                LOG.info("Tenant config loaded successfully from API")

            return merged_config, config_error

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_message = (
                    "Authentication failed. Please run a command to re-authenticate."
                )
            elif e.response.status_code == 404:
                error_message = "Tenant configuration not found. Using defaults."
            else:
                error_message = (
                    f"Failed to fetch config from API: HTTP {e.response.status_code}"
                )
            LOG.exception(error_message)
            return DEFAULT_CONFIG, error_message

        except requests.exceptions.Timeout:
            error_message = "Timeout fetching config from API. Using defaults."
            LOG.exception(error_message)
            return DEFAULT_CONFIG, error_message

        except requests.exceptions.ConnectionError:
            error_message = "Connection error fetching config from API. Using defaults."
            LOG.exception(error_message)
            return DEFAULT_CONFIG, error_message

        except Exception as e:
            error_message = f"Unexpected error fetching config from API: {str(e)}"
            LOG.exception(error_message)
            return DEFAULT_CONFIG, error_message
