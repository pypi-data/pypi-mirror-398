"""Tests for advanced features: file references, parsing configuration, help formatter, and unified parse()."""

import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest
import yaml

from confee import (
    ConfigBase,
    ConfigLoader,
    ConfigParser,
    HelpFormatter,
    OverrideHandler,
)


class SampleConfig(ConfigBase):
    """Sample configuration for testing."""

    name: str
    debug: bool = False
    workers: int = 4


class TestFileReferences:
    """Test file reference resolution in configuration values."""

    def test_resolve_file_reference(self):
        """Test resolving @file: references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a config file with file reference
            config_dir = Path(temp_dir)
            secret_file = config_dir / "secret.txt"
            secret_file.write_text("my-secret-key")

            config_file = config_dir / "config.yaml"
            config_data = {
                "name": "test",
                "api_key": "@file:secret.txt",
                "debug": False,
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Load and check if reference is resolved
            data = ConfigLoader.load(config_file)
            assert data["api_key"] == "my-secret-key"

    def test_resolve_file_reference_not_found(self):
        """Test handling of missing referenced files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_file = config_dir / "config.yaml"
            config_data = {
                "name": "test",
                "api_key": "@file:missing.txt",
                "debug": False,
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # In non-strict mode (strict=False), should keep original value
            data = ConfigLoader.load(config_file, strict=False)
            assert data["api_key"] == "@file:missing.txt"

    def test_resolve_nested_file_reference(self):
        """Test resolving file references in nested structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            secret_file = config_dir / "db_password.txt"
            secret_file.write_text("secure-password-123")

            config_file = config_dir / "config.yaml"
            config_data = {
                "name": "test",
                "database": {
                    "host": "localhost",
                    "password": "@file:db_password.txt",
                },
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            data = ConfigLoader.load(config_file)
            assert data["database"]["password"] == "secure-password-123"

    def test_resolve_yaml_file_reference(self):
        """Test resolving YAML file references with @config:."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create child YAML file
            child_file = config_dir / "child.yaml"
            child_data = {
                "name": "child-config",
                "debug": True,
                "workers": 8,
            }
            with open(child_file, "w") as f:
                yaml.dump(child_data, f)

            # Create parent config
            config_file = config_dir / "config.yaml"
            config_data = {
                "name": "parent",
                "debug": False,
                "child": "@config:child.yaml",
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Load and check
            data = ConfigLoader.load(config_file)
            assert data["child"]["name"] == "child-config"
            assert data["child"]["debug"] is True
            assert data["child"]["workers"] == 8

    def test_resolve_config_file_reference(self):
        """Test resolving @config: file references (alias for @yaml:)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create child YAML file
            child_file = config_dir / "db.yaml"
            child_data = {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
            }
            with open(child_file, "w") as f:
                yaml.dump(child_data, f)

            # Create parent config with @config: reference
            config_file = config_dir / "config.yaml"
            config_data = {
                "name": "myapp",
                "database": "@config:db.yaml",
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Load and check
            data = ConfigLoader.load(config_file)
            assert data["database"]["host"] == "localhost"
            assert data["database"]["port"] == 5432
            assert data["database"]["username"] == "admin"

    def test_nested_yaml_with_file_reference(self):
        """Test YAML file that contains @file: references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create password file
            password_file = config_dir / "password.txt"
            password_file.write_text("secret123")

            # Create database config with @file: reference
            db_file = config_dir / "database.yaml"
            db_data = {
                "host": "db.example.com",
                "port": 5432,
                "password": "@file:password.txt",
            }
            with open(db_file, "w") as f:
                yaml.dump(db_data, f)

            # Create main config with @config: reference
            config_file = config_dir / "config.yaml"
            config_data = {
                "name": "myapp",
                "database": "@config:database.yaml",
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Load and check - both references should be resolved
            data = ConfigLoader.load(config_file)
            assert data["database"]["host"] == "db.example.com"
            assert data["database"]["password"] == "secret123"


class TestParsingConfiguration:
    """Test parsing order configuration."""

    def test_parser_with_default_source_order(self):
        """Test parser with default source order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir)
            assert parser.source_order == ["cli", "env", "file"]

    def test_parser_with_custom_source_order(self):
        """Test parser with custom source order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir, source_order=["file", "env"])
            assert parser.source_order == ["file", "env"]

    def test_parser_with_invalid_source(self):
        """Test parser raises error for invalid source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Unsupported source"):
                ConfigParser(temp_dir, source_order=["invalid"])

    def test_parser_with_file_only_source(self):
        """Test parser with file-only source order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir, source_order=["file"])
            assert parser.source_order == ["file"]


class TestHelpFormatter:
    """Test help text generation and display."""

    def test_generate_help(self):
        """Test generating help text."""
        help_text = HelpFormatter.generate_help(SampleConfig)
        assert "Usage:" in help_text
        assert "Options:" in help_text
        assert "--name" in help_text
        assert "--debug" in help_text
        assert "--workers" in help_text

    def test_generate_help_with_custom_program_name(self):
        """Test help text with custom program name."""
        help_text = HelpFormatter.generate_help(SampleConfig, program_name="myapp")
        assert "myapp" in help_text

    def test_generate_help_with_description(self):
        """Test help text with custom description."""
        help_text = HelpFormatter.generate_help(
            SampleConfig, description="My application configuration"
        )
        assert "My application configuration" in help_text


class TestUnifiedParse:
    """Test unified parse() function."""

    def test_parse_with_cli_args(self):
        """Test parse with CLI arguments."""
        config = OverrideHandler.parse(
            SampleConfig, cli_args=["name=production", "debug=true", "workers=16"]
        )
        assert config.name == "production"
        assert config.debug is True
        assert config.workers == 16

    def test_parse_with_config_file(self):
        """Test parse with config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text(yaml.dump({"name": "from-file", "workers": 8}))

            config = OverrideHandler.parse(SampleConfig, config_file=str(config_file), cli_args=[])
            assert config.name == "from-file"
            assert config.workers == 8

    def test_parse_with_env_variables(self, monkeypatch):
        """Test parse with environment variables."""
        monkeypatch.setenv("CONFEE_NAME", "from-env")
        monkeypatch.setenv("CONFEE_WORKERS", "12")

        config = OverrideHandler.parse(SampleConfig, cli_args=[])
        assert config.name == "from-env"
        assert config.workers == 12

    def test_parse_cli_overrides_env(self, monkeypatch):
        """Test that CLI args override environment variables."""
        monkeypatch.setenv("CONFEE_DEBUG", "false")
        monkeypatch.setenv("CONFEE_NAME", "env-name")

        config = OverrideHandler.parse(SampleConfig, cli_args=["debug=true"])
        assert config.debug is True

    def test_parse_with_custom_env_prefix(self, monkeypatch):
        """Test parse with custom environment prefix."""
        monkeypatch.setenv("MYAPP_NAME", "custom-prefix")

        config = OverrideHandler.parse(SampleConfig, env_prefix="MYAPP_", cli_args=[])
        assert config.name == "custom-prefix"

    def test_parse_with_custom_source_order(self):
        """Test parse with custom source order."""
        # File-only source order (no env/cli)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text(yaml.dump({"name": "from-file", "workers": 8}))

            config = OverrideHandler.parse(
                SampleConfig,
                config_file=str(config_file),
                cli_args=["workers=16"],  # This should be ignored
                source_order=["file"],
            )
            assert config.name == "from-file"
            assert config.workers == 8  # Not overridden by CLI

    def test_parse_with_help_flag(self):
        """Test parse with help flag exits."""
        with pytest.raises(SystemExit):
            # Suppress stdout to avoid test output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                OverrideHandler.parse(SampleConfig, cli_args=["--help"])
            finally:
                sys.stdout = old_stdout

    def test_parse_non_strict_mode(self):
        """Test parse in non-strict mode (strict=False)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text(
                yaml.dump({"name": "test", "invalid_field": "should_be_ignored"})
            )

            # Should not raise error in non-strict mode (strict=False)
            config = OverrideHandler.parse(
                SampleConfig, config_file=str(config_file), cli_args=[], strict=False
            )
            assert config.name == "test"

    def test_parse_with_boolean_coercion(self):
        """Test parse with various boolean formats."""
        test_cases = [
            (["name=test", "debug=true"], True),
            (["name=test", "debug=yes"], True),
            (["name=test", "debug=on"], True),
            (["name=test", "debug=1"], True),
            (["name=test", "debug=false"], False),
            (["name=test", "debug=no"], False),
            (["name=test", "debug=off"], False),
            (["name=test", "debug=0"], False),
        ]

        for args, expected in test_cases:
            config = OverrideHandler.parse(SampleConfig, cli_args=args, source_order=["cli"])
            assert config.debug == expected, f"Failed for {args}"


class TestNestedFieldOverride:
    """Test nested field override using dot notation."""

    def test_nested_field_override_via_cli(self):
        """Test overriding nested fields via CLI using dot notation."""

        class DatabaseConfig(ConfigBase):
            host: str = "localhost"
            port: int = 5432
            username: str = "user"

        class AppConfig(ConfigBase):
            name: str
            debug: bool = False
            database: DatabaseConfig

        # Create default config
        default_config = AppConfig(name="myapp", debug=False, database=DatabaseConfig())

        # Apply nested overrides
        overrides = {
            "database.host": "prod.example.com",
            "database.port": "3306",
        }

        config = OverrideHandler.apply_overrides(default_config, overrides)

        assert config.database.host == "prod.example.com"
        assert config.database.port == 3306
        assert config.name == "myapp"

    def test_nested_field_via_parse(self):
        """Test nested field override via OverrideHandler.parse()."""

        class DatabaseConfig(ConfigBase):
            host: str = "localhost"
            port: int = 5432

        class AppConfig(ConfigBase):
            name: str
            database: DatabaseConfig

        # Parse with nested CLI overrides
        config = OverrideHandler.parse(
            AppConfig,
            cli_args=["name=production", "database.host=db.example.com", "database.port=3306"],
            source_order=["cli"],
        )

        assert config.name == "production"
        assert config.database.host == "db.example.com"
        assert config.database.port == 3306
