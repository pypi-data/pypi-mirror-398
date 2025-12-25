"""Tests for confee.parser module - Advanced configuration parsing with Hydra-like features."""

import tempfile
from pathlib import Path

import pytest
import yaml

from confee import ConfigBase
from confee.parser import ConfigParser


class SampleConfig(ConfigBase):
    """Sample configuration for testing."""

    name: str
    debug: bool = False
    workers: int = 4


class TestConfigParser:
    """Test ConfigParser functionality."""

    def test_parser_initialization(self):
        """Test parser initialization with config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir)
            assert parser.config_dir == Path(temp_dir)
            assert parser.strict is False

    def test_parser_strict_mode(self):
        """Test parser initialization with strict mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir, strict=True)
            assert parser.strict is True

    def test_load_config_file_yaml(self):
        """Test loading YAML config file from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create YAML config file
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump({"name": "test", "debug": True}, f)

            parser = ConfigParser(temp_dir)
            data = parser.load_config_file("config")

            assert data["name"] == "test"
            assert data["debug"] is True

    def test_load_config_file_json(self):
        """Test loading JSON config file from directory."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create JSON config file
            config_path = Path(temp_dir) / "config.json"
            with open(config_path, "w") as f:
                json.dump({"name": "test", "workers": 8}, f)

            parser = ConfigParser(temp_dir)
            data = parser.load_config_file("config")

            assert data["name"] == "test"
            assert data["workers"] == 8

    def test_load_config_file_not_found(self):
        """Test that loading nonexistent file raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir)

            with pytest.raises(FileNotFoundError):
                parser.load_config_file("nonexistent")

    def test_parse_simple_config(self):
        """Test parsing simple config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump({"name": "myapp", "debug": True, "workers": 8}, f)

            parser = ConfigParser(temp_dir)
            config = parser.parse("config", SampleConfig)

            assert config.name == "myapp"
            assert config.debug is True
            assert config.workers == 8


class TestConfigParserDefaults:
    """Test Hydra-style defaults resolution."""

    def test_resolve_defaults_simple(self):
        """Test resolving simple defaults list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config
            base_path = Path(temp_dir) / "base.yaml"
            with open(base_path, "w") as f:
                yaml.dump({"workers": 4, "timeout": 30}, f)

            parser = ConfigParser(temp_dir)

            config_dict = {"defaults": ["base"], "name": "myapp", "debug": True}

            resolved = parser.resolve_defaults(config_dict)

            assert resolved["name"] == "myapp"
            assert resolved["debug"] is True
            assert resolved["workers"] == 4
            assert resolved["timeout"] == 30

    def test_resolve_defaults_with_self(self):
        """Test defaults with _self_ directive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config
            base_path = Path(temp_dir) / "base.yaml"
            with open(base_path, "w") as f:
                yaml.dump({"workers": 4, "debug": False}, f)

            parser = ConfigParser(temp_dir)

            config_dict = {
                "defaults": ["base", "_self_"],
                "name": "myapp",
                "debug": True,  # Overrides base
            }

            resolved = parser.resolve_defaults(config_dict)

            assert resolved["name"] == "myapp"
            assert resolved["debug"] is True  # From _self_ (current config)
            assert resolved["workers"] == 4  # From base

    def test_resolve_defaults_order_matters(self):
        """Test that order of defaults matters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create configs
            base1_path = Path(temp_dir) / "base1.yaml"
            with open(base1_path, "w") as f:
                yaml.dump({"workers": 4}, f)

            base2_path = Path(temp_dir) / "base2.yaml"
            with open(base2_path, "w") as f:
                yaml.dump({"workers": 8}, f)

            parser = ConfigParser(temp_dir)

            config_dict = {
                "defaults": ["base1", "base2"],  # base2 overrides base1
                "name": "myapp",
            }

            resolved = parser.resolve_defaults(config_dict)

            assert resolved["workers"] == 8  # From base2 (later)

    def test_resolve_defaults_missing_lenient(self):
        """Test that missing defaults are ignored in lenient mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = ConfigParser(temp_dir, strict=False)

            config_dict = {"defaults": ["missing"], "name": "myapp"}

            # Should not raise error in lenient mode
            resolved = parser.resolve_defaults(config_dict)
            assert resolved["name"] == "myapp"


class TestConfigParserEdgeCases:
    """Test edge cases in parser."""

    def test_load_config_with_extension_variants(self):
        """Test loading with .yml variant."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .yml file (variant of .yaml)
            config_path = Path(temp_dir) / "config.yml"
            with open(config_path, "w") as f:
                yaml.dump({"name": "test"}, f)

            parser = ConfigParser(temp_dir)
            data = parser.load_config_file("config")

            assert data["name"] == "test"

    def test_parse_empty_config_file(self):
        """Test parsing empty config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty config file
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                f.write("")

            parser = ConfigParser(temp_dir)

            # Should handle gracefully (empty YAML returns None)
            data = parser.load_config_file("config")
            assert data is None or data == {}
