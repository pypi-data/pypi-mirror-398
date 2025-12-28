"""Extended tests to increase coverage for verbosity, color handling,
and edge branches in OverrideHandler.parse and helpers.
"""

import io
import sys

import pytest

from confee import ConfigBase, HelpFormatter, OverrideHandler


class _Cfg(ConfigBase):
    name: str
    debug: bool = False


def test_errorformatter_validation_verbose_and_compact(monkeypatch):
    """Cover verbose and compact formatting branches for validation errors."""
    from confee.overrides import Color, ErrorFormatter

    # Create a Pydantic validation error by instantiating without required field
    with pytest.raises(Exception) as ei:
        _Cfg()  # type: ignore[call-arg]
    err = ei.value

    # Compact style: should return single-line summary
    msg_compact = ErrorFormatter.format_validation_error(err, style="compact")
    assert "Config error:" in msg_compact

    # Verbose style: multi-line with red header and hint block
    Color.enable(True)
    msg_verbose = ErrorFormatter.format_validation_error(err, style="verbose")
    assert "Configuration Validation Error" in msg_verbose
    assert "How to fix" in msg_verbose
    # Color reset code appears when color enabled
    assert "\x1b[0m" in msg_verbose

    # Disable color and ensure color codes disappear for non-validation error too
    Color.enable(False)
    non_validation = RuntimeError("boom")
    msg_nv_verbose = ErrorFormatter.format_validation_error(non_validation, style="verbose")
    # When color is disabled, the verbose path for non-validation uses RED without reset
    # but our implementation returns colored text only when style != compact; ensure string contains message
    assert "boom" in msg_nv_verbose


def test_helpformatter_required_omits_default_and_factory_and_none(monkeypatch):
    """Ensure default segment omitted for required, and present for factory/None values."""
    from typing import Optional

    from pydantic import Field

    class CF(ConfigBase):
        req: str
        opt: int = 3
        maybe: Optional[str] = None
        factory: int = Field(default_factory=lambda: 7)

    txt = HelpFormatter.generate_help(CF)
    assert "--req" in txt and "[default:" not in txt.split("--req")[1][:80]
    assert "--opt" in txt and "[default:" in txt.split("--opt")[1]
    assert "--maybe" in txt and "[default: None]" in txt
    # For default_factory, implementation may render the callable name (could be "<lambda>")
    # Ensure the field is present and default segment is shown
    assert "--factory" in txt and "[default:" in txt.split("--factory")[1]


def test_parse_env_cli_verbosity_and_no_color(monkeypatch):
    """CLI should override ENV for verbosity and color; exercise warning paths."""
    # Prepare fake argv flags and ENV
    monkeypatch.setenv("CONFEE_VERBOSITY", "verbose")
    monkeypatch.setenv("NO_COLOR", "1")  # would disable color if not overridden by CLI

    # Create a missing file to trigger warning path; strict=False should not raise
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    try:
        cfg = OverrideHandler.parse(
            _Cfg,
            config_file="this_file_should_not_exist.yaml",
            cli_args=[
                "--verbose",
                "name=test",
            ],  # CLI verbose overrides ENV; also ensures color enabled unless --no-color present
            source_order=["file", "cli"],
            strict=False,
        )
    finally:
        sys.stdout = old_stdout

    out = buffer.getvalue()
    # Should contain concise warning about missing file
    assert "Warning:" in out and "not found" in out
    assert cfg.name == "test"


def test_parse_warning_verbose_on_loader_error(monkeypatch):
    """Mock loader error (non-ENOENT) to cover verbose/compact warning branches."""
    # Mock ConfigLoader.load to raise ValueError
    from confee import loaders

    def _boom(*args, **kwargs):
        raise ValueError("bad-format")

    monkeypatch.setattr(loaders.ConfigLoader, "load", staticmethod(_boom))

    # verbose branch
    buf_v = io.StringIO()
    old = sys.stdout
    sys.stdout = buf_v
    try:
        OverrideHandler.parse(
            _Cfg,
            config_file="any.yaml",
            cli_args=["--verbose", "name=x"],
            source_order=["file", "cli"],
            strict=False,
        )
    finally:
        sys.stdout = old
    out_v = buf_v.getvalue()
    assert "Warning: Failed to load config file:" in out_v

    # compact branch
    buf_c = io.StringIO()
    sys.stdout = buf_c
    try:
        OverrideHandler.parse(
            _Cfg,
            config_file="any.yaml",
            cli_args=["name=y"],
            source_order=["file", "cli"],
            strict=False,
        )
    finally:
        sys.stdout = old
    out_c = buf_c.getvalue()
    assert "Warning: bad-format" in out_c


def test_help_flag_triggers_help_and_exit(monkeypatch):
    """Cover help flag path inside OverrideHandler.parse()."""
    # Capture stdout and expect SystemExit when help is printed
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    with pytest.raises(SystemExit):
        try:
            OverrideHandler.parse(_Cfg, cli_args=["--help"], source_order=["cli"], strict=False)
        finally:
            sys.stdout = old


def test_configbase_set_strict_mode_toggles_model_config():
    """Exercise ConfigBase.set_strict_mode True/False branches."""

    class C(ConfigBase):
        a: int = 1

    # Enable strict mode
    C.set_strict_mode(True)
    assert C.model_config.get("extra") == "forbid"

    # Disable strict mode
    C.set_strict_mode(False)
    assert C.model_config.get("extra") == "ignore"


class TestVerbosityFlags:
    """Test verbosity and color flags in OverrideHandler."""

    def test_quiet_flag_forces_compact_on_validation_error(self, monkeypatch):
        """--quiet should force compact style regardless of ENV verbosity."""
        from confee import ConfigBase, OverrideHandler

        class Cfg(ConfigBase):
            name: str
            debug: bool = False

        monkeypatch.setenv("CONFEE_VERBOSITY", "verbose")
        import io

        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            # Trigger validation error by omitting required 'name'
            with pytest.raises(SystemExit):
                OverrideHandler.parse(Cfg, cli_args=["--quiet"], source_order=["cli"], strict=False)
        finally:
            sys.stdout = old
        out = buf.getvalue()
        # Expect a compact single-line style mention
        assert "Config error:" in out or "validation failed" in out

    def test_env_quiet_compact_and_cli_verbose_precedence(self, monkeypatch):
        """CLI --verbose overrides CONFEE_QUIET=1 compact style."""
        from confee import ConfigBase, OverrideHandler

        class Cfg(ConfigBase):
            name: str
            debug: bool = False

        monkeypatch.setenv("CONFEE_QUIET", "1")
        import io

        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            # Missing name to produce validation output once in verbose
            with pytest.raises(SystemExit):
                OverrideHandler.parse(
                    Cfg, cli_args=["--verbose"], source_order=["cli"], strict=False
                )
        finally:
            sys.stdout = old
        out = buf.getvalue()
        # Verbose header should appear because CLI wins
        assert "Configuration Validation Error" in out

    def test_no_colors_alias_flag(self):
        """--no-colors alias should disable color in outputs."""
        from confee import ConfigBase, OverrideHandler

        class Cfg(ConfigBase):
            name: str
            debug: bool = False

        import io

        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            # cause validation error and disable colors via alias
            with pytest.raises(SystemExit):
                OverrideHandler.parse(
                    Cfg, cli_args=["--no-colors"], source_order=["cli"], strict=False
                )
        finally:
            sys.stdout = old
        out = buf.getvalue()
        # Should not contain ANSI reset code when colors disabled
        assert "\x1b[0m" not in out

    def test_strict_mode_raises_on_missing_file(self):
        """When strict=True, missing file should raise FileNotFoundError (branch coverage)."""
        from confee import ConfigBase, OverrideHandler

        class Cfg(ConfigBase):
            name: str
            debug: bool = False

        with pytest.raises(FileNotFoundError):
            OverrideHandler.parse(
                Cfg,
                config_file="missing-config.yaml",
                cli_args=["name=x"],
                source_order=["file", "cli"],
                strict=True,
            )

    def test_color_property_reset_and_enable(self):
        """Cover Color._maybe/Color.reset property branch paths."""
        from confee.overrides import Color

        Color.enable(True)
        # When enabled, reset property returns the escape code
        c = Color()
        assert c.reset == "\x1b[0m"

        Color.enable(False)
        # When disabled, reset property returns empty string
        assert c.reset == ""
