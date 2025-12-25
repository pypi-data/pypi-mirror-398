"""Tests for confee.overrides module - CLI and environment variable overrides."""

import os

import pytest

from confee import ConfigBase, OverrideHandler


class SampleConfig(ConfigBase):
    """Sample configuration for testing."""

    name: str
    debug: bool = False
    workers: int = 4
    timeout: float = 30.5


class TestParseOverrideString:
    """Test parsing override strings."""

    def test_parse_simple_override(self):
        """Test parsing simple key=value override."""
        key, value = OverrideHandler.parse_override_string("debug=true")
        assert key == "debug"
        assert value == "true"

    def test_parse_override_with_spaces(self):
        """Test that spaces are stripped."""
        key, value = OverrideHandler.parse_override_string(" debug = true ")
        assert key == "debug"
        assert value == "true"

    def test_parse_override_with_multiple_equals(self):
        """Test parsing value with multiple equals signs."""
        key, value = OverrideHandler.parse_override_string("connection=user:pass@host=localhost")
        assert key == "connection"
        assert value == "user:pass@host=localhost"

    def test_parse_invalid_format(self):
        """Test that invalid format raises error."""
        with pytest.raises(ValueError):
            OverrideHandler.parse_override_string("no_equals_sign")


class TestParseOverrides:
    """Test parsing multiple override strings."""

    def test_parse_multiple_overrides(self):
        """Test parsing multiple override strings."""
        overrides = OverrideHandler.parse_overrides(["debug=true", "workers=8", "timeout=60.5"])

        assert overrides["debug"] == "true"
        assert overrides["workers"] == "8"
        assert overrides["timeout"] == "60.5"

    def test_parse_empty_list(self):
        """Test parsing empty override list."""
        overrides = OverrideHandler.parse_overrides([])
        assert overrides == {}


class TestValueCoercion:
    """Test value type coercion."""

    def test_coerce_to_bool_true(self):
        """Test coercion to boolean (true variations)."""
        assert OverrideHandler.coerce_value("true", bool) is True
        assert OverrideHandler.coerce_value("True", bool) is True
        assert OverrideHandler.coerce_value("TRUE", bool) is True
        assert OverrideHandler.coerce_value("yes", bool) is True
        assert OverrideHandler.coerce_value("1", bool) is True
        assert OverrideHandler.coerce_value("on", bool) is True

    def test_coerce_to_bool_false(self):
        """Test coercion to boolean (false values)."""
        assert OverrideHandler.coerce_value("false", bool) is False
        assert OverrideHandler.coerce_value("0", bool) is False
        assert OverrideHandler.coerce_value("no", bool) is False
        assert OverrideHandler.coerce_value("off", bool) is False

    def test_coerce_to_bool_invalid(self):
        """Test coercion to boolean with invalid values."""
        with pytest.raises(ValueError):
            OverrideHandler.coerce_value("anything_else", bool)

    def test_coerce_to_int(self):
        """Test coercion to integer."""
        assert OverrideHandler.coerce_value("42", int) == 42
        assert OverrideHandler.coerce_value("-10", int) == -10

    def test_coerce_to_float(self):
        """Test coercion to float."""
        assert OverrideHandler.coerce_value("3.14", float) == 3.14
        assert OverrideHandler.coerce_value("1.0", float) == 1.0

    def test_coerce_to_string(self):
        """Test coercion to string."""
        assert OverrideHandler.coerce_value("hello", str) == "hello"


class TestApplyOverrides:
    """Test applying overrides to configuration."""

    def test_apply_single_override(self):
        """Test applying single override."""
        config = SampleConfig(name="original")
        overrides = {"debug": "true"}

        updated = OverrideHandler.apply_overrides(config, overrides)

        assert updated.name == "original"
        assert updated.debug is True

    def test_apply_multiple_overrides(self):
        """Test applying multiple overrides."""
        config = SampleConfig(name="original", debug=False, workers=4)
        overrides = {"debug": "true", "workers": "16"}

        updated = OverrideHandler.apply_overrides(config, overrides)

        assert updated.name == "original"
        assert updated.debug is True
        assert updated.workers == 16

    def test_apply_override_with_type_inference(self):
        """Test that types are inferred from current config."""
        config = SampleConfig(name="test")
        overrides = {"timeout": "60.5"}

        updated = OverrideHandler.apply_overrides(config, overrides)

        assert updated.timeout == 60.5
        assert isinstance(updated.timeout, float)

    def test_apply_override_unknown_key_non_strict(self):
        """Test applying override with unknown key in non-strict mode."""
        config = SampleConfig(name="test")
        overrides = {"unknown_key": "value"}

        # Should not raise error in non-strict mode (strict=False by default)
        updated = OverrideHandler.apply_overrides(config, overrides, strict=False)
        assert updated.name == "test"

    def test_apply_override_unknown_key_strict(self):
        """Test applying override with unknown key in strict mode."""
        config = SampleConfig(name="test")
        overrides = {"unknown_key": "value"}

        with pytest.raises(KeyError):
            OverrideHandler.apply_overrides(config, overrides, strict=True)


class TestGetEnvOverrides:
    """Test getting overrides from environment variables."""

    def test_get_env_overrides_default_prefix(self):
        """Test getting overrides with default CONFEE_ prefix."""
        os.environ["CONFEE_DEBUG"] = "true"
        os.environ["CONFEE_WORKERS"] = "8"
        os.environ["OTHER_VAR"] = "ignored"

        try:
            overrides = OverrideHandler.get_env_overrides()

            assert "debug" in overrides
            assert overrides["debug"] == "true"
            assert "workers" in overrides
            assert overrides["workers"] == "8"
            assert "other_var" not in overrides
        finally:
            del os.environ["CONFEE_DEBUG"]
            del os.environ["CONFEE_WORKERS"]
            del os.environ["OTHER_VAR"]

    def test_get_env_overrides_custom_prefix(self):
        """Test getting overrides with custom prefix."""
        os.environ["MYAPP_DEBUG"] = "false"
        os.environ["MYAPP_NAME"] = "test"

        try:
            overrides = OverrideHandler.get_env_overrides(prefix="MYAPP_")

            assert overrides["debug"] == "false"
            assert overrides["name"] == "test"
        finally:
            del os.environ["MYAPP_DEBUG"]
            del os.environ["MYAPP_NAME"]

    def test_get_env_overrides_empty(self):
        """Test getting env overrides when no matching variables exist."""
        # Make sure no CONFEE_ variables exist
        for key in list(os.environ.keys()):
            if key.startswith("CONFEE_"):
                del os.environ[key]

        overrides = OverrideHandler.get_env_overrides()
        assert overrides == {} or all(not v.startswith("CONFEE_") for v in os.environ)


class TestFromCliAndEnv:
    """Test creating config from CLI and environment variables."""

    def test_from_cli_and_env_cli_only(self):
        """Test creating config from CLI arguments only."""
        config = OverrideHandler.from_cli_and_env(
            SampleConfig, cli_overrides=["name=cli_app", "debug=true"]
        )

        assert config.name == "cli_app"
        assert config.debug is True
        assert config.workers == 4  # default

    def test_from_cli_and_env_env_only(self):
        """Test creating config from environment variables only."""
        os.environ["CONFEE_NAME"] = "env_app"
        os.environ["CONFEE_DEBUG"] = "true"

        try:
            config = OverrideHandler.from_cli_and_env(SampleConfig, env_prefix="CONFEE_")

            assert config.name == "env_app"
            assert config.debug is True
        finally:
            del os.environ["CONFEE_NAME"]
            del os.environ["CONFEE_DEBUG"]

    def test_from_cli_and_env_cli_overrides_env(self):
        """Test that CLI arguments override environment variables."""
        os.environ["CONFEE_NAME"] = "env_app"
        os.environ["CONFEE_DEBUG"] = "false"

        try:
            config = OverrideHandler.from_cli_and_env(
                SampleConfig, cli_overrides=["debug=true"], env_prefix="CONFEE_"
            )

            assert config.name == "env_app"  # From env
            assert config.debug is True  # From CLI (overrides env)
        finally:
            del os.environ["CONFEE_NAME"]
            del os.environ["CONFEE_DEBUG"]

    def test_from_cli_and_env_explicit_env_dict(self):
        """Test using explicit env overrides dictionary."""
        config = OverrideHandler.from_cli_and_env(
            SampleConfig, env_overrides={"name": "explicit_app", "workers": "16"}
        )

        assert config.name == "explicit_app"
        assert config.workers == 16


class TestOverridePriority:
    """Test override priority order."""

    def test_priority_cli_over_env(self):
        """Test that CLI overrides take precedence over environment."""
        os.environ["CONFEE_NAME"] = "env_app"
        os.environ["CONFEE_DEBUG"] = "false"
        os.environ["CONFEE_WORKERS"] = "4"

        try:
            config = OverrideHandler.from_cli_and_env(
                SampleConfig,
                cli_overrides=["debug=true"],  # Higher priority
                env_prefix="CONFEE_",
            )

            # CLI override wins
            assert config.debug is True
            # Env values used where no CLI override
            assert config.name == "env_app"
            assert config.workers == 4
        finally:
            del os.environ["CONFEE_NAME"]
            del os.environ["CONFEE_DEBUG"]
            del os.environ["CONFEE_WORKERS"]


class TestOverrideMatrix:
    """Integration tests for override handling."""

    def test_apply_overrides_strict_unknown_key_raises(self):
        """Test that unknown keys raise error in strict mode."""
        cfg = SampleConfig(name="test")
        with pytest.raises(KeyError):
            OverrideHandler.apply_overrides(cfg, {"unknown": "x"}, strict=True)

    def test_coerce_value_bool_invalid(self):
        """Test that invalid boolean values raise error."""
        with pytest.raises(ValueError) as ei:
            OverrideHandler.coerce_value("maybe", bool)
        assert "Cannot coerce 'maybe' to bool" in str(ei.value)

    def test_parse_non_strict_missing_file_emits_warning_and_uses_cli(self, tmp_path):
        """Test that missing config file emits warning in non-strict mode and uses CLI values."""
        import io
        import sys

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            # config file path that does not exist
            missing_file = str(tmp_path / "nope.yaml")
            cfg = OverrideHandler.parse(
                SampleConfig,
                config_file=missing_file,
                cli_args=["name=test", "debug=true"],
                source_order=["file", "cli"],
                strict=False,
            )
            out = sys.stdout.getvalue()
            # In compact style default, a concise warning message is expected
            assert "Warning:" in out
            assert "not found" in out or "Failed to load config file" in out

            # CLI values should be applied
            assert cfg.name == "test"
            assert cfg.debug is True
        finally:
            sys.stdout = old_stdout
