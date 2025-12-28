"""Configuration base classes with Pydantic validation and inheritance support."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="ConfigBase")


class ConfigBase(BaseModel):
    """Base configuration class using Pydantic for type validation.

    Supports:
    - Type checking and validation
    - Configuration inheritance
    - Flexible field handling (strict/non-strict modes)
    - Environment variable overrides

    Examples:
        >>> class AppConfig(ConfigBase):
        ...     name: str
        ...     debug: bool = False
        ...     workers: int = 4

        >>> config = AppConfig(name="myapp")
        >>> config.name
        'myapp'
    """

    model_config = ConfigDict(
        extra="ignore",  # Default: ignore extra fields (strict=False)
        validate_default=True,
        str_strip_whitespace=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def to_json(self, **kwargs: Any) -> str:
        """Convert configuration to JSON string."""
        return self.model_dump_json(**kwargs)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create configuration from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Create configuration from JSON string."""
        return cls.model_validate_json(json_str)

    def print(self) -> None:
        """Print the configuration instance using devtools.debug."""
        from devtools import debug

        debug(self, color=True)

    @classmethod
    def load(
        cls: Type[T],
        config_file: Optional[Union[str, Path]] = None,
        cli_args: Optional[List[str]] = None,
        env_prefix: str = "CONFEE_",
        source_order: Optional[List[str]] = None,
        help_flags: Optional[List[str]] = None,
        strict: bool = True,
    ) -> T:
        """Load configuration from multiple sources (file, environment, CLI).

        Unified parsing method — processes file, environment variables, and CLI at once.
        This consolidates the capabilities of OverrideHandler.parse() and load_from_file().

        Args:
            config_file: Path to configuration file (YAML/JSON)
            cli_args: CLI arguments list (default: sys.argv[1:])
            env_prefix: Environment variable prefix (default: "CONFEE_")
            source_order: Parsing order (default: ["cli", "env", "file"])
            help_flags: Help flags (default: ["--help", "-h"])
            strict: If True, forbid extra fields; if False, ignore extra fields (default: True)

        Returns:
            Configuration instance

        Examples:
            >>> # Automatically parse from all sources
            >>> config = AppConfig.load(config_file="config.yaml")

            >>> # Use file only
            >>> config = AppConfig.load(
            ...     config_file="config.yaml",
            ...     source_order=["file"]
            ... )

            >>> # Use CLI + environment variables only
            >>> config = AppConfig.load(source_order=["cli", "env"])
        """
        from .overrides import OverrideHandler

        # Convert Path to str for type compatibility
        config_file_str: Optional[str] = None
        if config_file is not None:
            config_file_str = str(config_file)

        try:
            config = OverrideHandler.parse(
                cls,
                config_file=config_file_str,
                cli_args=cli_args,
                env_prefix=env_prefix,
                source_order=source_order,
                help_flags=help_flags,
                strict=strict,
            )
            config.print()
            return config
        except FileNotFoundError:
            import sys
            from pathlib import Path

            if config_file is not None:
                abs_path = Path(config_file).resolve()
                print("Error: Config file not found", file=sys.stderr)
                print(f"  File: {config_file}", file=sys.stderr)
                print(f"  Full path: {abs_path}", file=sys.stderr)
            else:
                print("Error: Config file not found", file=sys.stderr)
            print(f"  Current directory: {Path.cwd()}", file=sys.stderr)
            raise SystemExit(1)

    def override_with(self: T, defaults: "ConfigBase") -> T:
        """Override this configuration's values with defaults from another configuration.
        This configuration's values take precedence over the defaults.

        Args:
            defaults: Default configuration to merge with (lower priority)

        Returns:
            Merged configuration instance

        Examples:
            >>> defaults_config = AppConfig(name="default", debug=False, workers=4)
            >>> custom_config = AppConfig(name="custom", debug=True)
            >>> result = custom_config.override_with(defaults_config)
            >>> result.name
            'custom'
            >>> result.workers
            4
        """
        defaults_dict = defaults.model_dump()
        current_dict = self.model_dump()

        # Create merged dict: start with defaults, override with non-None current values
        merged = {**defaults_dict}
        for key, value in current_dict.items():
            # Override with current value if it's not None
            if value is not None:
                merged[key] = value

        return self.__class__(**merged)

    @classmethod
    def set_strict_mode(cls, strict: bool = True) -> None:
        """Enable/disable strict mode.
        - True: forbid extra fields (forbid unknown fields)
        - False: ignore extra fields (strict=False)
        """
        if strict:
            cls.model_config = ConfigDict(**{**cls.model_config, "extra": "forbid"})
        else:
            cls.model_config = ConfigDict(**{**cls.model_config, "extra": "ignore"})
