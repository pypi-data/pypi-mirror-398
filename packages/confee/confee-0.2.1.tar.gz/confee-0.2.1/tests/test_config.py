"""Tests for confee.config module - Configuration base classes and features."""

import json

import pytest
from pydantic import ValidationError

from confee import ConfigBase


class SampleConfig(ConfigBase):
    """Sample configuration for testing."""

    name: str
    debug: bool = False
    workers: int = 4


class TestConfigBaseBasics:
    """Test basic ConfigBase functionality."""

    def test_config_creation(self):
        """Test basic config creation with defaults."""
        config = SampleConfig(name="test")
        assert config.name == "test"
        assert config.debug is False
        assert config.workers == 4

    def test_config_with_all_values(self):
        """Test config creation with all values specified."""
        config = SampleConfig(name="test", debug=True, workers=8)
        assert config.name == "test"
        assert config.debug is True
        assert config.workers == 8

    def test_config_missing_required_field(self):
        """Test that missing required field raises validation error."""
        with pytest.raises(ValidationError):
            SampleConfig(debug=True)

    def test_config_type_validation(self):
        """Test that invalid types raise validation error."""
        with pytest.raises(ValidationError):
            SampleConfig(name="test", workers="invalid")

    def test_config_type_coercion(self):
        """Test that compatible types are coerced."""
        config = SampleConfig(name="test", workers="8")
        assert config.workers == 8


class TestConfigConversion:
    """Test configuration conversion methods."""

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = SampleConfig(name="test", debug=True, workers=8)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "test"
        assert config_dict["debug"] is True
        assert config_dict["workers"] == 8

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {"name": "test", "debug": True, "workers": 8}
        config = SampleConfig.from_dict(data)

        assert config.name == "test"
        assert config.debug is True
        assert config.workers == 8

    def test_to_json(self):
        """Test converting config to JSON."""
        config = SampleConfig(name="test", debug=True, workers=8)
        json_str = config.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["name"] == "test"
        assert parsed["debug"] is True
        assert parsed["workers"] == 8

    def test_from_json(self):
        """Test creating config from JSON."""
        json_str = '{"name": "test", "debug": true, "workers": 8}'
        config = SampleConfig.from_json(json_str)

        assert config.name == "test"
        assert config.debug is True
        assert config.workers == 8


class TestNonStrictMode:
    """Test non-strict mode (strict=False)."""

    def test_non_strict_mode_ignores_extra_fields(self):
        """Test that non-strict mode ignores extra fields."""
        config = SampleConfig(name="test", extra_field="ignored")
        assert config.name == "test"
        assert not hasattr(config, "extra_field")

    def test_non_strict_mode_via_from_dict(self):
        """Test non-strict mode with from_dict."""
        data = {"name": "test", "unknown_field": "value"}
        config = SampleConfig.from_dict(data)
        assert config.name == "test"


class TestStrictMode:
    """Test strict mode."""

    def test_strict_mode_forbids_extra_fields(self):
        """Test that strict mode forbids extra fields."""

        class StrictConfig(ConfigBase):
            model_config = {"extra": "forbid"}
            name: str

        with pytest.raises(ValidationError):
            StrictConfig(name="test", extra_field="not allowed")


class TestConfigInheritance:
    """Test ConfigBase override_with functionality."""

    def test_override_with_basic(self):
        """Test basic override_with."""

        class AppConfig(ConfigBase):
            name: str
            debug: bool = False
            workers: int = 4

        defaults = AppConfig(name="default", debug=False, workers=2)
        custom = AppConfig(name="custom", debug=True, workers=4)

        merged = custom.override_with(defaults)

        # Custom values take precedence
        assert merged.name == "custom"
        assert merged.debug is True
        assert merged.workers == 4

    def test_override_with_partial(self):
        """Test that unset values use defaults."""

        class AppConfig(ConfigBase):
            name: str
            debug: bool = False
            workers: int = 4

        defaults = AppConfig(name="default", debug=False, workers=8)
        # Custom only overrides name
        custom = AppConfig(name="custom", debug=True, workers=16)

        merged = custom.override_with(defaults)

        # All custom values take precedence
        assert merged.name == "custom"
        assert merged.debug is True
        assert merged.workers == 16


class TestConfigModelSchema:
    """Test JSON schema generation."""

    def test_json_schema_generation(self):
        """Test that JSON schema can be generated."""
        schema = SampleConfig.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "debug" in schema["properties"]
        assert "workers" in schema["properties"]
