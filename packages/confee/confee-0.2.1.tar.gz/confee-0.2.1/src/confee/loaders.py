"""Configuration loaders for YAML, JSON, and other formats."""

import json
from pathlib import Path
from typing import Any, Dict, Type, TypeVar, Union

import yaml  # type: ignore[import-untyped]

from .config import ConfigBase

T = TypeVar("T", bound=ConfigBase)


class ConfigLoader:
    """Flexible configuration file loader with automatic format detection.

    Supports YAML and JSON formats. Automatically detects format based on file extension.
    """

    SUPPORTED_FORMATS = {".yaml", ".yml", ".json"}

    @staticmethod
    def detect_format(file_path: Union[str, Path]) -> str:
        """Detect configuration file format from extension."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in ConfigLoader.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {ConfigLoader.SUPPORTED_FORMATS}"
            )
        return suffix

    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML configuration file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                # YAML can return None for empty files
                return data if isinstance(data, dict) else ({} if data is None else {})
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML file: {file_path}\nError: {e}")

    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON configuration file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON file: {file_path}\nError: {e}")

    @staticmethod
    def load(file_path: Union[str, Path], strict: bool = True) -> Dict[str, Any]:
        """Load configuration file with automatic format detection.

        Args:
            file_path: Path to configuration file
            strict: If True, raise error on invalid format. If False, return empty dict.

        Returns:
            Configuration dictionary
        """
        try:
            file_format = ConfigLoader.detect_format(file_path)

            if file_format in {".yaml", ".yml"}:
                data = ConfigLoader.load_yaml(file_path)
            elif file_format == ".json":
                data = ConfigLoader.load_json(file_path)
            else:
                return {}

            # Resolve file references in the loaded data
            base_dir = Path(file_path).parent
            data = ConfigLoader.resolve_file_references(data, base_dir)
            return data

        except (FileNotFoundError, ValueError) as e:
            if strict:
                raise
            print(f"Warning: Failed to load config file: {e}")
            return {}

    @staticmethod
    def resolve_file_references(
        data: Dict[str, Any],
        base_dir: Path,
        file_prefix: str = "@file:",
    ) -> Dict[str, Any]:
        """Resolve file references in configuration values.

        File references use multiple formats:
        - "@file:path/to/file" - 파일 내용을 문자열로 로드
        - "@config:path/to/file.yaml" - YAML 파일을 딕셔너리로 로드

        Paths are resolved relative to base_dir.

        Args:
            data: Configuration dictionary
            base_dir: Base directory for relative path resolution
            file_prefix: Prefix for file references (default: "@file:")

        Returns:
            Configuration dictionary with file references resolved

        Examples:
            # 텍스트 파일 로드
            # secret_key: "@file:secrets/api_key.txt"
            >>> data = {"key": "@file:values.txt"}
            >>> resolved = ConfigLoader.resolve_file_references(data, Path("."))
            >>> resolved["key"]  # Contents of values.txt

            # YAML 파일 로드
            # database: "@config:config/db.yaml"
            >>> data = {"db": "@config:config/db.yaml"}
            >>> resolved = ConfigLoader.resolve_file_references(data, Path("."))
            >>> resolved["db"]  # {'host': 'localhost', 'port': 5432, ...}
        """
        resolved: Dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, str) and ("@" in value and ":" in value):
                # 접두사 추출
                prefix_match = None
                file_path_value = None

                if value.startswith("@file:"):
                    prefix_match = "@file:"
                    file_path_value = value[len("@file:") :]
                elif value.startswith("@config:"):
                    prefix_match = "@config:"
                    file_path_value = value[len("@config:") :]

                if prefix_match and file_path_value:
                    file_full_path = base_dir / file_path_value

                    try:
                        if not file_full_path.exists():
                            raise FileNotFoundError(f"Referenced file not found: {file_full_path}")

                        if prefix_match == "@file:":
                            # 텍스트 파일 로드
                            with open(file_full_path, encoding="utf-8") as f:
                                resolved[key] = f.read().strip()

                        elif prefix_match == "@config:":
                            # YAML 파일 로드
                            yaml_data = ConfigLoader.load_yaml(file_full_path)
                            # 재귀적으로 참조 해석
                            resolved[key] = ConfigLoader.resolve_file_references(
                                yaml_data, file_full_path.parent, file_prefix
                            )

                    except Exception as e:
                        print(f"Warning: Failed to resolve file reference {value}: {e}")
                        resolved[key] = value  # Keep original value on error
                else:
                    resolved[key] = value

            elif isinstance(value, dict):
                # Recursively resolve nested dictionaries
                resolved[key] = ConfigLoader.resolve_file_references(value, base_dir, file_prefix)
            else:
                resolved[key] = value

        return resolved


def load_from_file(
    file_path: Union[str, Path],
    config_class: Type[T],
    strict: bool = True,
) -> T:
    """Load configuration from file into specified config class.

    Args:
        file_path: Path to configuration file (YAML or JSON)
        config_class: Pydantic config class to load into
        strict: If True, raise error on validation failure. If False, use defaults or partial config.

    Returns:
        Instance of config_class

    Examples:
        >>> class AppConfig(ConfigBase):
        ...     name: str
        ...     debug: bool = False

        >>> config = load_from_file("config.yaml", AppConfig)
    """
    data = ConfigLoader.load(file_path, strict=strict)

    try:
        return config_class(**data)
    except Exception as e:
        if strict:
            raise
        print(f"Warning: Failed to validate config: {e}")
        # In non-strict mode (strict=False), try to create with partial data if possible
        # If that fails, raise error (can't instantiate with missing required fields)
        try:
            # Try with empty dict if all fields have defaults
            return config_class()
        except Exception:
            # If that fails too, re-raise the original error since non-strict mode
            # cannot create instance without required fields
            raise e


def load_config(
    *file_paths: Union[str, Path],
    config_class: Type[T],
    strict: bool = True,
) -> T:
    """Load and merge multiple configuration files.

    Later files override earlier files. All files must be compatible with config_class.

    Args:
        *file_paths: Paths to configuration files
        config_class: Pydantic config class to load into
        strict: If True, raise error on validation failure

    Returns:
        Merged configuration instance

    Examples:
        >>> config = load_config(
        ...     "defaults.yaml",
        ...     "config.yaml",
        ...     config_class=AppConfig
        ... )
    """
    merged_data: Dict[str, Any] = {}

    for file_path in file_paths:
        data = ConfigLoader.load(file_path, strict=strict)
        merged_data.update(data)

    try:
        return config_class(**merged_data)
    except Exception as e:
        if strict:
            raise
        print(f"Warning: Failed to validate merged config: {e}")
        return config_class()
