"""Command-line argument and environment variable override handling."""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from .config import ConfigBase

T = TypeVar("T", bound=ConfigBase)


# ANSI Color codes
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    _enabled = True

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_MAGENTA = "\033[95m"

    @classmethod
    def enable(cls, enabled: bool) -> None:
        """Enable/disable ANSI color output globally."""
        cls._enabled = enabled

    @classmethod
    def _maybe(cls, code: str) -> str:
        return code if cls._enabled else ""

    # Expose color getters that respect enable flag
    @property
    def reset(self) -> str:
        return self._maybe(self.RESET)


class ErrorFormatter:
    """Format validation errors in a user-friendly way."""

    @staticmethod
    def format_validation_error(error: Exception, style: str = "compact") -> str:
        """Format Pydantic validation errors in a readable way.

        Args:
            error: Pydantic ValidationError

        Returns:
            Formatted error message
        """
        from pydantic import ValidationError

        error_str = str(error)

        # Check if it's a Pydantic ValidationError
        if isinstance(error, ValidationError):
            # Extract detailed error information from Pydantic V2 ValidationError
            errors = error.errors()

            if style == "compact":
                # Compact format: show first error only
                if errors:
                    first_error = errors[0]
                    field = first_error.get("loc", ("unknown",))[0]
                    error_type = first_error.get("type", "unknown_error")
                    msg = first_error.get("msg", "validation failed")

                    if error_type == "missing":
                        return f"Config error: missing required field '{field}'"
                    else:
                        return f"Config error: field '{field}' - {msg}"
                return "Config error: validation failed"

            # Verbose format with detailed error information
            lines = []
            lines.append(f"{Color.BOLD}{Color.RED}❌ Configuration Validation Error{Color.RESET}")
            lines.append("")

            if errors:
                lines.append(f"  {Color.BRIGHT_YELLOW}Found {len(errors)} validation error(s):{Color.RESET}")
                lines.append("")

                for idx, error_detail in enumerate(errors, 1):
                    field = error_detail.get("loc", ("unknown",))[0]
                    error_type = error_detail.get("type", "unknown_error")
                    msg = error_detail.get("msg", "validation failed")
                    input_value = error_detail.get("input", None)

                    lines.append(f"  {Color.BRIGHT_MAGENTA}[{idx}] Field: {Color.BOLD}{field}{Color.RESET}")
                    lines.append(f"      {Color.YELLOW}Error: {msg}{Color.RESET}")
                    lines.append(f"      {Color.DIM}Type: {error_type}{Color.RESET}")

                    if input_value is not None:
                        lines.append(f"      {Color.DIM}Got: {repr(input_value)}{Color.RESET}")

                    lines.append("")
            else:
                lines.append(f"  {error_str}")
                lines.append("")

            lines.append(f"  {Color.CYAN}💡 How to fix:{Color.RESET}")
            lines.append("    1. Add the required field to your configuration file")
            lines.append("    2. Or pass the value via CLI: python main.py name=myapp")
            lines.append("    3. Or set an environment variable: export CONFEE_NAME=myapp")
            lines.append("    4. Check field types match your configuration class")

            return "\n".join(lines)

        # Check if it's a validation error by string pattern
        if "validation error" in error_str.lower():
            if style == "compact":
                # Try extract missing field for concise output
                import re

                field = None
                if "field required" in error_str.lower():
                    m = re.search(r"(\w+)\s*\n\s*Field required", error_str)
                    if m:
                        field = m.group(1)
                if field:
                    return f"Config error: missing required field '{field}'"
                return "Config error: validation failed"

            # verbose style (defaulting to existing rich output)
            lines = []
            lines.append(f"{Color.BOLD}{Color.RED}❌ Configuration Validation Error{Color.RESET}")
            lines.append("")

            # Try to extract field name and error type
            if "field required" in error_str.lower():
                # Extract field name from error message
                import re

                match = re.search(r"(\w+)\s*\n\s*Field required", error_str)
                if match:
                    field_name = match.group(1)
                    lines.append(
                        f"  {Color.BRIGHT_YELLOW}Missing required field: {Color.BOLD}{field_name}{Color.RESET}"
                    )
                    lines.append("  This field is required for configuration.")
                else:
                    lines.append("  A required field is missing.")
            else:
                lines.append(f"  {error_str}")

            lines.append("")
            lines.append(f"  {Color.CYAN}💡 How to fix:{Color.RESET}")
            lines.append("    1. Add the required field to your configuration file")
            lines.append("    2. Or pass the value via CLI: python main.py name=myapp")
            lines.append("    3. Or set an environment variable: export CONFEE_NAME=myapp")

            return "\n".join(lines)

        # Non-validation generic error
        if style == "compact":
            return f"Error: {error_str}"
        return f"{Color.RED}Error: {error_str}{Color.RESET}"


class HelpFormatter:
    """Format and display help messages for configuration classes."""

    @staticmethod
    def _format_default_field(field: Any) -> str:
        """Return a colored default-string segment for a Pydantic v2 field.

        Rules:
        - default_factory present: factory()
        - default is explicitly None: None
        - required (no default and no factory): <required>
        - otherwise: actual default value
        """
        # Detect Pydantic's undefined sentinel so we don't render it as a string
        _PUD: Any
        try:
            from pydantic_core import PydanticUndefined as _PUD  # type: ignore
        except Exception:  # pragma: no cover - fallback path
            try:
                from pydantic import PydanticUndefined as _PUD  # type: ignore
            except Exception:  # pragma: no cover
                _PUD = object()  # type: ignore

        # 1) Prioritize default_factory
        if getattr(field, "default_factory", None) is not None:
            factory = getattr(field.default_factory, "__name__", "factory")
            return f" {Color.BRIGHT_YELLOW}[default: {factory}()]{Color.RESET}"

        # 2) Explicit None
        if getattr(field, "default", None) is None and hasattr(field, "default"):
            return f" {Color.BRIGHT_YELLOW}[default: None]{Color.RESET}"

        # 3) Determine required: use sentinel or is_required() if available
        is_required_method = getattr(field, "is_required", None)
        is_required = False
        if callable(is_required_method):
            try:
                is_required = bool(is_required_method())
            except Exception:
                is_required = False

        if is_required or getattr(field, "default", _PUD) is _PUD:
            # Requirement: omit the [default: ...] text entirely for required fields (no default)
            return ""

        # 4) Otherwise: render actual default value
        return f" {Color.BRIGHT_YELLOW}[default: {field.default}]{Color.RESET}"

    @staticmethod
    def generate_help(
        config_class: Type[ConfigBase],
        program_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Generate help text for a configuration class with colors.

        Args:
            config_class: Configuration class to generate help for
            program_name: Name of the program (default: sys.argv[0])
            description: Custom description text

        Returns:
            Formatted help text with ANSI colors

        Examples:
            >>> help_text = HelpFormatter.generate_help(AppConfig)
            >>> print(help_text)
        """
        if program_name is None:
            program_name = sys.argv[0]

        help_text = (
            f"{Color.BOLD}{Color.BRIGHT_CYAN}Usage:{Color.RESET} {program_name} [OPTIONS]\n\n"
        )

        if description:
            help_text += f"{Color.BOLD}Description:{Color.RESET}\n  {description}\n\n"

        help_text += f"{Color.BOLD}{Color.BRIGHT_CYAN}Options:{Color.RESET}\n"

        # Extract fields from config class
        field_info = []
        if hasattr(config_class, "model_fields"):
            # Pydantic V2
            for field_name, field in config_class.model_fields.items():
                field_type = field.annotation
                type_str = (
                    field_type.__name__  # type: ignore
                    if hasattr(field_type, "__name__")
                    else str(field_type)
                )

                # Get description from field info
                description_text = field.description or field_name.replace("_", " ")

                # Get default value (robust formatting)
                default_str = HelpFormatter._format_default_field(field)

                field_info.append((field_name, type_str, description_text, default_str))

        # Format field information
        if field_info:
            max_name_width = max(len(name) for name, _, _, _ in field_info)
            max_type_width = max(len(type_str) for _, type_str, _, _ in field_info)

            for name, type_str, desc, default in field_info:
                help_text += f"  {Color.BRIGHT_GREEN}--{name}{Color.RESET}"
                help_text += " " * (max_name_width - len(name) + 2)
                help_text += f"{Color.CYAN}{type_str:<{max_type_width}}{Color.RESET}  "
                help_text += f"{desc}{default}\n"

        help_text += f"\n{Color.BOLD}{Color.BRIGHT_CYAN}Override format:{Color.RESET}\n"
        help_text += f"  {Color.GREEN}key=value{Color.RESET}              Set a simple value\n"
        help_text += f"  {Color.GREEN}nested.key=value{Color.RESET}       Set a nested value\n"
        help_text += f"  {Color.GREEN}@file:path/to/file{Color.RESET}     Read value from file\n"
        help_text += f"  {Color.GREEN}true/false/yes/no/on/off{Color.RESET} for boolean values\n"
        help_text += f"\n{Color.BOLD}{Color.BRIGHT_CYAN}Examples:{Color.RESET}\n"
        help_text += f"  {Color.MAGENTA}{program_name} debug=true workers=8{Color.RESET}\n"
        help_text += f"  {Color.MAGENTA}{program_name} --help{Color.RESET}\n"

        return help_text

    @staticmethod
    def print_help(
        config_class: Type[ConfigBase],
        program_name: Optional[str] = None,
        description: Optional[str] = None,
        exit_code: int = 0,
    ) -> None:
        """Print help message and optionally exit.

        Args:
            config_class: Configuration class to generate help for
            program_name: Name of the program
            description: Custom description text
            exit_code: Exit code (None to not exit)
        """
        help_text = HelpFormatter.generate_help(config_class, program_name, description)
        print(help_text)
        if exit_code is not None:
            sys.exit(exit_code)


def is_help_command(
    arg: str,
    help_flags: Optional[List[str]] = None,
) -> bool:
    """Check if an argument is a help command.

    Args:
        arg: Argument to check
        help_flags: Help flags to recognize (default: ["--help", "-h"])

    Returns:
        True if argument is a help command
    """
    if help_flags is None:
        help_flags = ["--help", "-h"]

    return arg in help_flags


class OverrideHandler:
    """Handle configuration overrides from command-line arguments and environment variables.

    Supports:
    - Command-line overrides: key=value format
    - Environment variable overrides: CONFIG_KEY format
    - Nested field access: database.host=localhost
    - Type coercion based on config class
    """

    @staticmethod
    def parse_override_string(override_str: str) -> Tuple[str, str]:
        """Parse override string in key=value format.

        Args:
            override_str: String like "key=value" or "nested.key=value"

        Returns:
            Tuple of (key, value)

        Raises:
            ValueError: If format is invalid
        """
        if "=" not in override_str:
            raise ValueError(
                f"Invalid override format: '{override_str}'. Expected format: key=value"
            )

        key, value = override_str.split("=", 1)
        return key.strip(), value.strip()

    @staticmethod
    def parse_overrides(
        override_strings: List[str],
    ) -> Dict[str, Any]:
        """Parse multiple override strings into a dictionary.

        Args:
            override_strings: List of "key=value" strings

        Returns:
            Dictionary of overrides

        Examples:
            >>> overrides = OverrideHandler.parse_overrides([
            ...     "debug=true",
            ...     "workers=8"
            ... ])
            >>> overrides
            {'debug': 'true', 'workers': '8'}
        """
        overrides: Dict[str, Any] = {}

        for override_str in override_strings:
            key, value = OverrideHandler.parse_override_string(override_str)
            overrides[key] = value

        return overrides

    @staticmethod
    def get_env_overrides(
        prefix: str = "CONFEE_",
        strict: bool = False,
    ) -> Dict[str, str]:
        """Get configuration overrides from environment variables.

        Args:
            prefix: Environment variable prefix (default: CONFEE_)
            strict: If True, only variables with prefix are used

        Returns:
            Dictionary of environment-based overrides

        Examples:
            # Environment: CONFEE_DEBUG=true CONFEE_WORKERS=8
            >>> overrides = OverrideHandler.get_env_overrides()
            >>> overrides
            {'debug': 'true', 'workers': '8'}
        """
        env_overrides: Dict[str, str] = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()
                env_overrides[config_key] = value

        return env_overrides

    @staticmethod
    def coerce_value(value: str, target_type: Type[Any]) -> Any:
        """Coerce string value to target type.

        Supports special handling for boolean values:
        - True: "true", "yes", "1", "on" (case-insensitive)
        - False: "false", "no", "0", "off" (case-insensitive)

        Args:
            value: String value to coerce
            target_type: Target Python type

        Returns:
            Coerced value

        Examples:
            >>> OverrideHandler.coerce_value("true", bool)
            True
            >>> OverrideHandler.coerce_value("false", bool)
            False
            >>> OverrideHandler.coerce_value("yes", bool)
            True
            >>> OverrideHandler.coerce_value("42", int)
            42
        """
        if target_type == bool:
            value_lower = value.lower().strip()
            if value_lower in {"true", "yes", "1", "on"}:
                return True
            elif value_lower in {"false", "no", "0", "off"}:
                return False
            else:
                raise ValueError(
                    f"Cannot coerce '{value}' to bool. Use: true/yes/on/1 or false/no/off/0"
                )
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == str:
            return value
        else:
            # Try direct conversion
            return target_type(value)

    @staticmethod
    def apply_overrides(
        config_instance: T,
        overrides: Dict[str, Any],
        strict: bool = False,
    ) -> T:
        """Apply overrides to configuration instance.

        Supports nested field access using dot notation (e.g., "database.host").

        Args:
            config_instance: Configuration instance to override
            overrides: Dictionary of overrides
            strict: If False, ignore unknown keys. If True, raise error.

        Returns:
            New configuration instance with overrides applied

        Examples:
            >>> config = AppConfig(name="myapp", debug=False)
            >>> overrides = {"debug": "true"}
            >>> config = OverrideHandler.apply_overrides(config, overrides)
            >>> config.debug
            True

            >>> # Nested field access
            >>> overrides = {"database.host": "localhost", "database.port": "5432"}
            >>> config = OverrideHandler.apply_overrides(config, overrides)
            >>> config.database.host
            'localhost'
        """
        config_dict = config_instance.model_dump()

        for key, value in overrides.items():
            # Nested field support (a.b.c format)
            if "." in key:
                parts = key.split(".")
                current = config_dict

                # Navigate until the penultimate part
                for part in parts[:-1]:
                    if part not in current:
                        if strict:
                            raise KeyError(f"Unknown configuration key: {key}")
                        continue
                    current = current[part]

                # Set the value at the last part
                last_key = parts[-1]
                if last_key in current:
                    # Coerce based on the type of the existing value
                    if isinstance(current[last_key], bool):
                        current[last_key] = OverrideHandler.coerce_value(value, bool)
                    elif isinstance(current[last_key], int):
                        current[last_key] = OverrideHandler.coerce_value(value, int)
                    elif isinstance(current[last_key], float):
                        current[last_key] = OverrideHandler.coerce_value(value, float)
                    else:
                        current[last_key] = value
                elif strict:
                    raise KeyError(f"Unknown configuration key: {key}")
            else:
                # Top-level field
                if key not in config_dict and strict:
                    raise KeyError(f"Unknown configuration key: {key}")

                if key in config_dict:
                    # Coerce value based on current value type
                    if isinstance(config_dict[key], bool):
                        config_dict[key] = OverrideHandler.coerce_value(value, bool)
                    elif isinstance(config_dict[key], int):
                        config_dict[key] = OverrideHandler.coerce_value(value, int)
                    elif isinstance(config_dict[key], float):
                        config_dict[key] = OverrideHandler.coerce_value(value, float)
                    else:
                        config_dict[key] = value

        return config_instance.__class__(**config_dict)

    @staticmethod
    def from_cli_and_env(
        config_class: Type[T],
        cli_overrides: Optional[List[str]] = None,
        env_prefix: str = "CONFEE_",
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> T:
        """Create configuration from CLI arguments and environment variables.

        Priority order (highest to lowest):
        1. CLI arguments
        2. Explicit env_overrides parameter
        3. Environment variables with prefix
        4. Config class defaults

        Args:
            config_class: Configuration class to instantiate
            cli_overrides: List of "key=value" CLI arguments
            env_prefix: Environment variable prefix
            env_overrides: Explicit environment overrides dict

        Returns:
            Configuration instance with all overrides applied

        Examples:
            >>> config = OverrideHandler.from_cli_and_env(
            ...     AppConfig,
            ...     cli_overrides=["debug=true"],
            ...     env_prefix="CONFEE_"
            ... )
        """
        # Merge all overrides (highest to lowest priority)
        merged_overrides: Dict[str, Any] = {}

        # Start with environment variable overrides (lowest priority)
        if env_overrides:
            merged_overrides.update(env_overrides)
        else:
            env_dict = OverrideHandler.get_env_overrides(prefix=env_prefix)
            merged_overrides.update(env_dict)

        # Apply CLI overrides (highest priority, overwrites env)
        if cli_overrides:
            cli_dict = OverrideHandler.parse_overrides(cli_overrides)
            merged_overrides.update(cli_dict)

        # Create config with merged overrides
        return config_class(**merged_overrides)

    @staticmethod
    def _flatten_to_nested(flat_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert flat dictionary with dotted keys to nested dictionary.

        Examples:
            >>> flat = {"a.b.c": "value", "a.b.d": "value2", "x": "y"}
            >>> nested = OverrideHandler._flatten_to_nested(flat)
            >>> nested
            {'a': {'b': {'c': 'value', 'd': 'value2'}}, 'x': 'y'}
        """
        nested: Dict[str, Any] = {}

        for key, value in flat_dict.items():
            if "." not in key:
                nested[key] = value
            else:
                parts = key.split(".")
                current = nested

                # Navigate/create nested structure
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Set the value at the leaf
                current[parts[-1]] = value

        return nested

    @staticmethod
    def parse(
        config_class: Type[T],
        config_file: Optional[str] = None,
        cli_args: Optional[List[str]] = None,
        env_prefix: str = "CONFEE_",
        source_order: Optional[List[str]] = None,
        help_flags: Optional[List[str]] = None,
        strict: bool = True,
    ) -> T:
        """Parse configuration from multiple sources (file, environment, CLI).

        This is the primary entry point for configuration parsing.
        Combines configuration file, environment variables, and CLI arguments.

        Args:
            config_class: Configuration class to instantiate
            config_file: Path to configuration file (YAML/JSON). Optional.
            cli_args: Command-line arguments. Default: sys.argv[1:]
            env_prefix: Environment variable prefix. Default: "CONFEE_"
            source_order: Priority order for configuration sources.
                         Default: ["cli", "env", "file"]
                         Available: ["file", "env", "cli"]
            help_flags: Help command flags. Default: ["--help", "-h"]
            strict: If True, forbid extra fields and raise errors on validation failure

        Returns:
            Configuration instance

        Raises:
            SystemExit: If help is requested or validation fails in strict mode
            FileNotFoundError: If config_file doesn't exist and strict mode
            ValidationError: If validation fails and strict=True

        Examples:
            >>> # Simple parsing with all sources
            >>> config = OverrideHandler.parse(AppConfig)

            >>> # With config file and custom prefix
            >>> config = OverrideHandler.parse(
            ...     AppConfig,
            ...     config_file="config.yaml",
            ...     env_prefix="MYAPP_"
            ... )

            >>> # With custom source order (file only, no env/cli)
            >>> config = OverrideHandler.parse(
            ...     AppConfig,
            ...     config_file="config.yaml",
            ...     source_order=["file"]
            ... )

            >>> # With help command detection
            >>> config = OverrideHandler.parse(
            ...     AppConfig,
            ...     help_flags=["--help", "-h", "--info"]
            ... )
        """
        # Default values
        if cli_args is None:
            cli_args = sys.argv[1:]

        if source_order is None:
            source_order = ["cli", "env", "file"]

        if help_flags is None:
            help_flags = ["--help", "-h"]

        # Determine verbosity and color options from ENV/CLI
        env_verbosity = os.getenv("CONFEE_VERBOSITY")
        env_quiet = os.getenv("CONFEE_QUIET")
        no_color_env = os.getenv("NO_COLOR") or os.getenv("CONFEE_NO_COLOR")

        verbose_flag = False
        quiet_flag = False
        no_color_flag = False

        filtered_cli_args: List[str] = []

        # Check for help command and collect control flags
        for arg in cli_args:
            if is_help_command(arg, help_flags):
                HelpFormatter.print_help(config_class)
            elif arg in ("--quiet", "-q"):
                quiet_flag = True
            elif arg in ("--verbose", "-v"):
                verbose_flag = True
            elif arg in ("--no-color", "--no-colors"):
                no_color_flag = True
            else:
                filtered_cli_args.append(arg)

        # Resolve color enable
        Color.enable(not (bool(no_color_env) or no_color_flag))

        # Resolve verbosity style
        style = "compact"
        if env_verbosity:
            if env_verbosity.lower() in ("verbose", "rich", "detailed"):
                style = "verbose"
            elif env_verbosity.lower() in ("compact", "quiet", "minimal"):
                style = "compact"
        if env_quiet and env_quiet not in ("0", "false", "False"):
            style = "compact"
        if verbose_flag:
            style = "verbose"
        if quiet_flag:
            style = "compact"

        # Collect configurations from all sources
        configs_by_source: Dict[str, Dict[str, Any]] = {
            "file": {},
            "env": {},
            "cli": {},
        }

        # Load from file if specified
        if "file" in source_order and config_file:
            try:
                from .loaders import ConfigLoader

                configs_by_source["file"] = ConfigLoader.load(config_file, strict=strict)
            except FileNotFoundError:
                if strict:
                    # Re-raise in strict mode
                    raise
                # Lenient mode: print warning instead of raising
                print(f"Warning: {config_file} not found")
            except Exception as e:
                if strict:
                    raise
                # Lenient mode (strict=False): print warning instead of raising
                if style == "verbose":
                    print(f"Warning: Failed to load config file: {e}")
                else:
                    print(f"Warning: {str(e)}")

        # Load from environment variables if in source order
        if "env" in source_order:
            configs_by_source["env"] = OverrideHandler.get_env_overrides(prefix=env_prefix)

        # Parse CLI arguments if in source order
        if "cli" in source_order:
            configs_by_source["cli"] = OverrideHandler.parse_overrides(filtered_cli_args)

        # Merge configurations according to source_order (reverse order for priority)
        merged_config: Dict[str, Any] = {}
        for source in reversed(source_order):
            merged_config.update(configs_by_source[source])

        # Convert flat dotted keys to nested structure (a.b.c -> {a: {b: {c: value}}})
        merged_config = OverrideHandler._flatten_to_nested(merged_config)

        # Create configuration instance
        try:
            return config_class(**merged_config)
        except Exception as e:
            formatted = ErrorFormatter.format_validation_error(e, style=style)
            if strict:
                # Format and display friendly error message (single print)
                print("\n" + formatted + "\n")
                raise SystemExit(1)

            # Lenient mode (strict=False): print once. In compact style, prefix with Warning.
            if style == "compact":
                print("Warning: " + formatted)
            else:
                print("\n" + formatted + "\n")

            # Try falling back to defaults; if it still fails, exit silently (no duplicate print)
            try:
                return config_class()
            except Exception:
                raise SystemExit(1)
