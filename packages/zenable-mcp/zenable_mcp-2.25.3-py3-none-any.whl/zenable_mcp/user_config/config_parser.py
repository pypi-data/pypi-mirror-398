from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Optional

import tomllib
import yaml
from pydantic import BaseModel

from zenable_mcp.user_config.data_models import (
    DEFAULT_CONFIG,
    FindingType,
    FindingTypeConfig,
    UserConfig,
    _UserDBConfig,
    _UserTomlConfig,
    _UserYamlConfig,
)


class MergeStrategy:
    """Base class for merge strategies for different config fields."""

    @staticmethod
    def merge(origin_value: Any, destination_value: Any) -> Any:
        """Default merge strategy: origin takes precedence."""
        return origin_value


class SkipFilenamesMergeStrategy(MergeStrategy):
    """Merge strategy for skip_filenames field that prepends defaults to user patterns."""

    @staticmethod
    def merge(origin_value: list[str], destination_value: list[str]) -> list[str]:
        """Prepend default patterns to user patterns for proper negation support."""
        if origin_value is None:
            return destination_value
        return destination_value + origin_value


class FindingsMergeStrategy(MergeStrategy):
    """Merge strategy for findings field that merges two dictionaries."""

    @staticmethod
    def merge(
        origin_value: dict[FindingType, Any], destination_value: dict[FindingType, Any]
    ) -> dict[FindingType, FindingTypeConfig]:
        """Replace the destination value for every key that is present in the origin value."""
        result = deepcopy(destination_value)
        for key, value in origin_value.items():
            result[key] = FindingTypeConfig(**value.model_dump())
        return result


class ConfigParser(ABC):
    """
    Config parser for user config.
    """

    compatible_file_extensions: list[str]

    # Field-specific merge strategies
    _field_merge_strategies: dict[str, type[MergeStrategy]] = {
        "pr_reviews.skip_filenames": SkipFilenamesMergeStrategy,
        "pr_reviews.findings": FindingsMergeStrategy,
    }

    @abstractmethod
    def parse_config(self, content: str) -> tuple[UserConfig, Optional[str]]:
        """Parse config content and return config with optional warning about extra fields."""
        pass

    def _get_merge_strategy(self, field_path: str) -> type[MergeStrategy]:
        """Get the appropriate merge strategy for a field."""
        return self._field_merge_strategies.get(field_path, MergeStrategy)

    def _merge_config(
        self, _origin_config: UserConfig, _destination_config: UserConfig
    ) -> UserConfig:
        """
        Merge the origin config with the destination config.
        Uses field-specific merge strategies where defined, otherwise origin takes precedence.
        """
        merged = _destination_config.model_copy(deep=True)
        self._merge_model(merged, _origin_config, _destination_config)
        return merged

    def _merge_model(
        self,
        merged: BaseModel,
        origin: BaseModel,
        destination: BaseModel,
        parent_path: str = "",
    ) -> None:
        """Recursively merge model fields using appropriate strategies."""
        fields_changed = origin.model_fields_set

        for field_name in fields_changed:
            field_path = f"{parent_path}.{field_name}" if parent_path else field_name
            origin_value = getattr(origin, field_name, None)
            destination_value = getattr(destination, field_name, None)

            if isinstance(origin_value, BaseModel):
                # For nested models, create a copy and recursively merge
                merged_nested = destination_value.model_copy(deep=True)
                self._merge_model(
                    merged_nested, origin_value, destination_value, field_path
                )
                setattr(merged, field_name, merged_nested)
            else:
                # Use appropriate merge strategy for the field
                merge_strategy = self._get_merge_strategy(field_path)
                merged_value = merge_strategy.merge(origin_value, destination_value)
                setattr(merged, field_name, merged_value)

    def _merge_default_config(self, _loaded_config: UserConfig) -> UserConfig:
        """
        Merge the loaded config with the default config.
        """
        return self._merge_config(_loaded_config, DEFAULT_CONFIG)

    def _collect_extra_fields(self, model: BaseModel, path: str = "") -> dict[str, Any]:
        """
        Recursively collect all extra fields from a model and its nested models.
        Returns a dict with dot-separated paths as keys.
        """
        extra_fields = {}

        # Get extra fields from current model
        if hasattr(model, "__pydantic_extra__") and model.__pydantic_extra__:
            for field, value in model.__pydantic_extra__.items():
                field_path = f"{path}.{field}" if path else field
                extra_fields[field_path] = value

        # Recursively check nested models
        for field_name in model.model_dump(mode="json"):
            if hasattr(model, field_name):
                actual_value = getattr(model, field_name)
                if isinstance(actual_value, BaseModel):
                    nested_path = f"{path}.{field_name}" if path else field_name
                    nested_extras = self._collect_extra_fields(
                        actual_value, nested_path
                    )
                    extra_fields.update(nested_extras)
                if isinstance(actual_value, list) and all(
                    isinstance(item, BaseModel) for item in actual_value
                ):
                    for index, item in enumerate(actual_value):
                        nested_path = (
                            f"{path}.{field_name}[{index}]" if path else field_name
                        )
                        nested_extras = self._collect_extra_fields(item, nested_path)
                        extra_fields.update(nested_extras)
                if isinstance(actual_value, dict) and all(
                    isinstance(item, BaseModel) for item in actual_value.values()
                ):
                    for key, item in actual_value.items():
                        nested_path = (
                            f"{path}.{field_name}[{key}]" if path else field_name
                        )
                        nested_extras = self._collect_extra_fields(item, nested_path)
                        extra_fields.update(nested_extras)

        return extra_fields

    def _format_extra_fields_warning(
        self, extra_fields: dict[str, Any]
    ) -> Optional[str]:
        """
        Format extra fields into a warning message.
        """
        if not extra_fields:
            return None

        field_list = []
        for field_path, value in extra_fields.items():
            field_list.append(f"'{field_path}'")

        fields_str = ", ".join(sorted(field_list))
        return f"The following configuration fields were ignored as they are not recognized: {fields_str}"


class UserTomlConfigParser(ConfigParser):
    """
    Config parser for TOML based user config.
    """

    compatible_file_extensions = [".toml"]

    def parse_config(self, content: str) -> tuple[UserConfig, Optional[str]]:
        # Map data from str toml to dict
        data = tomllib.loads(content)
        # Map data from toml dict to UserTomlConfig
        config_data = _UserTomlConfig(**data)

        # Collect any extra fields that were ignored
        extra_fields = self._collect_extra_fields(config_data)
        warning = self._format_extra_fields_warning(extra_fields)

        # Merge the loaded config with the default config, this will also map it to a UserConfig.
        merged_config = self._merge_default_config(config_data)
        return merged_config, warning


class UserYamlConfigParser(ConfigParser):
    """
    Config parser for YAML based user config.
    """

    compatible_file_extensions = [".yaml", ".yml"]

    def parse_config(self, content: str) -> tuple[UserConfig, Optional[str]]:
        # Map data from str yaml to dict
        data = yaml.safe_load(content) or {}
        # Map data from yaml dict to UserYamlConfig
        config_data = _UserYamlConfig(**data)

        # Collect any extra fields that were ignored
        extra_fields = self._collect_extra_fields(config_data)
        warning = self._format_extra_fields_warning(extra_fields)

        # Merge the loaded config with the default config, this will also map it to a UserConfig.
        merged_config = self._merge_default_config(config_data)
        return merged_config, warning


class UserDBConfigParser(ConfigParser):
    """
    Config parser for database-stored user config.

    This class handles configuration deltas stored in the database, validating and merging them with
    DEFAULT_CONFIG.

    The word "parse" is kept for consistency or historical reasons, but technically we don't parse
    anything, the config is a dict in the db.
    """

    compatible_file_extensions = []  # Not file-based

    def parse_config(self, content: str) -> tuple[UserConfig, Optional[str]]:
        """
        Not used for DB configs since they come as dicts, not strings.
        Use parse_config_dict instead.

        We used to get the configuration from parsers, now we store it ourselves as a dict. The word
        "parse" is kept for consistency with the other parsers or historical reasons, but technically
        we don't parse anything, the config is a dict in the db.
        """
        raise NotImplementedError(
            "DB configs are not parsed, the config is a dict. Use get_config_from_dict instead."
        )

    def get_config_from_dict(
        self, tenant_config: dict[str, Any]
    ) -> tuple[UserConfig, Optional[str]]:
        """
        Parse and validate a tenant config from the database.

        Args:
            tenant_config: Dictionary containing the tenant configuration from DB

        Returns:
            Tuple of (merged_config, warning_message)
        """
        # Map data from dict to UserDBConfig
        config_data = _UserDBConfig(**tenant_config)

        # Collect any extra fields that were ignored
        extra_fields = self._collect_extra_fields(config_data)
        warning = self._format_extra_fields_warning(extra_fields)

        # Merge the loaded config with the default config
        merged_config = self._merge_default_config(config_data)
        return merged_config, warning
