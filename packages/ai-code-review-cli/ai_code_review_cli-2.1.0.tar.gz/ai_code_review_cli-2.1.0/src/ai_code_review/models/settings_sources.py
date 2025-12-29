"""Custom settings sources for Pydantic Settings.

This module provides custom settings sources for loading configuration from
various sources like YAML files, following Pydantic Settings patterns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

# Default config file path
DEFAULT_CONFIG_PATH = Path(".ai_review/config.yml")


class ConfigFileSettingsSource(PydanticBaseSettingsSource):
    """Settings source that loads from YAML config file.

    This source loads configuration from a YAML file, supporting:
    - Auto-detection of .ai_review/config.yml in current directory
    - Explicit config file path via constructor or init kwargs
    - Graceful handling of missing files (returns empty dict)
    - Validation of YAML syntax and structure

    The source integrates with Pydantic's settings_customise_sources to provide
    proper priority ordering where config file has lower priority than
    environment variables.

    Note:
        - YAML data is cached after first load and not reloaded during the
          instance lifetime. Create a new source instance to reload the file.
        - Only top-level YAML keys are used. Nested structures are passed as-is
          to Pydantic for validation (use flat keys in config files).
        - Pydantic automatically converts string values to enums during model
          instantiation, so YAML can use string values like "gemini" for enums.

    Attributes:
        _config_path: Path to the config file to load
        _require_exists: If True, raise error when file doesn't exist
        _yaml_cache: Cached YAML data to avoid re-reading
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        config_path: Path | str | None = None,
        require_exists: bool = False,
    ) -> None:
        """Initialize the config file settings source.

        Args:
            settings_cls: The settings class this source is for
            config_path: Optional path to config file. If None, uses default.
            require_exists: If True, raise ValueError when file doesn't exist.
                           If False (default), return empty dict for missing files.
        """
        super().__init__(settings_cls)
        self._config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._require_exists = require_exists
        self._yaml_cache: dict[str, Any] | None = None

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        """Get value for a specific field from YAML config.

        Note: This method is required by PydanticBaseSettingsSource, but when
        __call__ is implemented (as we do), Pydantic uses __call__ instead.
        We implement this for completeness and testing.

        Args:
            field: The field info from Pydantic (unused)
            field_name: Name of the field to get value for

        Returns:
            Tuple of (value, field_key, is_complex).
        """
        yaml_data = self._load_yaml()
        field_value = yaml_data.get(field_name)
        return field_value, field_name, False

    def _load_yaml(self) -> dict[str, Any]:
        """Load and cache YAML config file.

        Returns:
            Dict with config values, or empty dict if file doesn't exist
            (unless require_exists=True).

        Raises:
            ValueError: If file doesn't exist and require_exists=True,
                       or if file contains invalid YAML or non-dict content.
        """
        # Return cached data if available
        if self._yaml_cache is not None:
            return self._yaml_cache

        # Initialize empty cache
        self._yaml_cache = {}

        # Check if file exists
        if not self._config_path.exists():
            if self._require_exists:
                raise ValueError(
                    f"Config file not found: {self._config_path}. "
                    f"Please check the path or remove --config-file option."
                )
            return self._yaml_cache

        # Load and parse YAML
        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

                if not isinstance(data, dict):
                    raise ValueError(
                        f"Config file must contain a YAML object/mapping, "
                        f"got {type(data).__name__}"
                    )

                self._yaml_cache = data

        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML syntax in config file {self._config_path}: {e}"
            ) from e

        except OSError as e:
            raise ValueError(
                f"Failed to read config file {self._config_path}: {e}"
            ) from e

        return self._yaml_cache

    def __call__(self) -> dict[str, Any]:
        """Return all values from YAML config.

        This is called by Pydantic Settings to get all config values at once.

        Returns:
            Dict with all config values from YAML file.
        """
        return self._load_yaml()

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"ConfigFileSettingsSource("
            f"path={self._config_path}, "
            f"require_exists={self._require_exists}, "
            f"loaded={self._yaml_cache is not None})"
        )
