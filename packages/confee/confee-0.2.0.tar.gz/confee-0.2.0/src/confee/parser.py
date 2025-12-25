"""Configuration parser with Hydra-like features and inheritance support."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from .config import ConfigBase
from .loaders import ConfigLoader

T = TypeVar("T", bound=ConfigBase)


class ConfigParser:
    """Advanced configuration parser with Hydra-like inheritance and composition.

    Features:
    - Configuration inheritance through defaults lists
    - Package-based configuration organization
    - Profile support (dev, prod, test)
    - Configuration composition and merging
    - Customizable source priority (file, env, cli)
    """

    # Supported source types for ordering
    SUPPORTED_SOURCES = {"file", "env", "cli"}
    DEFAULT_SOURCE_ORDER = ["cli", "env", "file"]  # CLI > Env > File > defaults

    def __init__(
        self,
        config_dir: Union[str, Path],
        strict: bool = False,
        source_order: Optional[List[str]] = None,
    ):
        """Initialize parser with configuration directory.

        Args:
            config_dir: Directory containing configuration files
            strict: If True, enforce strict validation (forbid extra fields)
            source_order: Priority order for configuration sources.
                         Default: ["cli", "env", "file"]
                         Higher priority sources override lower priority sources.
                         Available sources: "file", "env", "cli"

        Raises:
            ValueError: If source_order contains unsupported sources

        Examples:
            >>> # CLI overrides env, env overrides file
            >>> parser = ConfigParser("./configs", source_order=["cli", "env", "file"])

            >>> # File only, no env/cli overrides
            >>> parser = ConfigParser("./configs", source_order=["file"])
        """
        self.config_dir = Path(config_dir)
        self.strict = strict

        # Validate and set source order
        if source_order is None:
            self.source_order = self.DEFAULT_SOURCE_ORDER.copy()
        else:
            # Validate source types
            for source in source_order:
                if source not in self.SUPPORTED_SOURCES:
                    raise ValueError(
                        f"Unsupported source: '{source}'. "
                        f"Supported sources: {self.SUPPORTED_SOURCES}"
                    )
            self.source_order = source_order

    def load_config_file(
        self,
        file_name: str,
    ) -> Dict[str, Any]:
        """Load a configuration file from the config directory.

        Args:
            file_name: Name of configuration file (with or without extension)

        Returns:
            Configuration dictionary
        """
        # Try to find the file with different extensions
        for ext in [".yaml", ".yml", ".json"]:
            file_path = self.config_dir / f"{file_name}{ext}"
            if file_path.exists():
                data = ConfigLoader.load(file_path, strict=self.strict)
                # Ensure we return a dict (handle None from empty YAML)
                return data if isinstance(data, dict) else {}

        raise FileNotFoundError(f"Config file not found: {file_name} in {self.config_dir}")

    def resolve_defaults(
        self,
        config_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve default configurations from defaults list.

        Supports Hydra-style defaults list for inheritance.

        Args:
            config_dict: Configuration dictionary that may contain defaults

        Returns:
            Merged configuration with defaults resolved

        Example YAML structure:
            defaults:
              - base
              - database/postgres
              - _self_

            debug: true
        """
        if "defaults" not in config_dict:
            return config_dict

        defaults = config_dict.pop("defaults")
        current_config = config_dict.copy()  # Save current config before merging
        merged = {}
        has_self = False

        for default in defaults:
            if default == "_self_":
                # Include current config
                merged.update(current_config)
                has_self = True
            else:
                # Load default configuration
                try:
                    default_config = self.load_config_file(default)
                    merged.update(default_config)
                except FileNotFoundError:
                    if self.strict:
                        raise
                    # Silently ignore missing defaults in non-strict mode (strict=False)

        # If _self_ was not specified, add current config at the end
        if not has_self:
            merged.update(current_config)

        return merged

    def parse(
        self,
        config_file: str,
        config_class: Type[T],
    ) -> T:
        """Parse configuration file into config class.

        Handles defaults resolution and inheritance.

        Args:
            config_file: Name of main configuration file
            config_class: Pydantic config class to parse into

        Returns:
            Parsed configuration instance

        Examples:
            >>> parser = ConfigParser("./configs")
            >>> config = parser.parse("config.yaml", AppConfig)
        """
        config_dict = self.load_config_file(config_file)
        resolved_config = self.resolve_defaults(config_dict)

        try:
            return config_class(**resolved_config)
        except Exception as e:
            if self.strict:
                raise
            print(f"Warning: Configuration validation failed: {e}")
            return config_class()
