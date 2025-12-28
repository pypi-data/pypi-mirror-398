"""Tests for confee.loaders module - Configuration file loading and parsing."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from confee import ConfigBase, load_config, load_from_file
from confee.loaders import ConfigLoader


class SampleConfig(ConfigBase):
    """Sample configuration for testing."""

    name: str
    debug: bool = False
    workers: int = 4


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def test_detect_yaml_format(self):
        """Test YAML format detection."""
        assert ConfigLoader.detect_format("config.yaml") == ".yaml"
        assert ConfigLoader.detect_format("config.yml") == ".yml"

    def test_detect_json_format(self):
        """Test JSON format detection."""
        assert ConfigLoader.detect_format("config.json") == ".json"

    def test_detect_unsupported_format(self):
        """Test that unsupported formats raise error."""
        with pytest.raises(ValueError):
            ConfigLoader.detect_format("config.toml")

    def test_load_yaml_file(self):
        """Test loading YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"name": "test", "debug": True, "workers": 8}, f)
            temp_path = f.name

        try:
            data = ConfigLoader.load_yaml(temp_path)
            assert data["name"] == "test"
            assert data["debug"] is True
            assert data["workers"] == 8
        finally:
            Path(temp_path).unlink()

    def test_load_json_file(self):
        """Test loading JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "test", "debug": True, "workers": 8}, f)
            temp_path = f.name

        try:
            data = ConfigLoader.load_json(temp_path)
            assert data["name"] == "test"
            assert data["debug"] is True
            assert data["workers"] == 8
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_yaml("/nonexistent/path/config.yaml")

    def test_load_invalid_yaml(self):
        """Test that invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                ConfigLoader.load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_auto_detects_format(self):
        """Test that load() auto-detects file format."""
        # Test YAML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"name": "yaml_test"}, f)
            yaml_path = f.name

        try:
            data = ConfigLoader.load(yaml_path)
            assert data["name"] == "yaml_test"
        finally:
            Path(yaml_path).unlink()

        # Test JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "json_test"}, f)
            json_path = f.name

        try:
            data = ConfigLoader.load(json_path)
            assert data["name"] == "json_test"
        finally:
            Path(json_path).unlink()

    def test_load_lenient_mode_ignores_errors(self):
        """Test that lenient mode (strict=False) ignores loading errors."""
        data = ConfigLoader.load("/nonexistent/path.yaml", strict=False)
        assert data == {}


class TestLoadFromFile:
    """Test load_from_file function."""

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"name": "test", "debug": True, "workers": 8}, f)
            temp_path = f.name

        try:
            config = load_from_file(temp_path, SampleConfig)
            assert config.name == "test"
            assert config.debug is True
            assert config.workers == 8
        finally:
            Path(temp_path).unlink()

    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "test", "debug": False, "workers": 2}, f)
            temp_path = f.name

        try:
            config = load_from_file(temp_path, SampleConfig)
            assert config.name == "test"
            assert config.debug is False
            assert config.workers == 2
        finally:
            Path(temp_path).unlink()

    def test_load_from_file_lenient_mode(self):
        """Test lenient mode (strict=False) handles validation errors gracefully."""

        class OptionalConfig(ConfigBase):
            """Config with all optional fields."""

            debug: bool = False
            workers: int = 4

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # Provide invalid type for field with default
            yaml.dump({"debug": "invalid_bool"}, f)
            temp_path = f.name

        try:
            # In lenient mode (strict=False), should return instance with defaults when validation fails
            config = load_from_file(temp_path, OptionalConfig, strict=False)
            assert isinstance(config, OptionalConfig)
            # Should have defaults since validation failed
            assert config.debug is False
            assert config.workers == 4
        finally:
            Path(temp_path).unlink()


class TestLoadConfig:
    """Test load_config function for merging multiple files."""

    def test_load_multiple_files(self):
        """Test loading and merging multiple configuration files."""
        # Create base config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"name": "base", "debug": False, "workers": 2}, f)
            base_path = f.name

        # Create override config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"debug": True, "workers": 8}, f)
            override_path = f.name

        try:
            config = load_config(base_path, override_path, config_class=SampleConfig)

            # Base config values
            assert config.name == "base"
            # Override config values (later files override earlier)
            assert config.debug is True
            assert config.workers == 8
        finally:
            Path(base_path).unlink()
            Path(override_path).unlink()

    def test_load_multiple_files_merge_order(self):
        """Test that files are merged in correct order."""
        # Create three config files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"workers": 1}, f)
            file1 = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"workers": 2, "name": "config"}, f)
            file2 = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"workers": 3}, f)
            file3 = f.name

        try:
            config = load_config(file1, file2, file3, config_class=SampleConfig)

            # Last file wins
            assert config.workers == 3
            # From file2
            assert config.name == "config"
        finally:
            Path(file1).unlink()
            Path(file2).unlink()
            Path(file3).unlink()


class TestFileEdgeCases:
    """Test edge cases in file handling."""

    def test_empty_yaml_file(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            # Empty YAML returns None, which ConfigLoader should handle
            data = ConfigLoader.load(temp_path, strict=False)
            assert data == {} or data is None
        finally:
            Path(temp_path).unlink()

    def test_yaml_with_comments(self):
        """Test loading YAML with comments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
# This is a comment
name: test  # inline comment
debug: true
""")
            temp_path = f.name

        try:
            data = ConfigLoader.load_yaml(temp_path)
            assert data["name"] == "test"
            assert data["debug"] is True
        finally:
            Path(temp_path).unlink()
