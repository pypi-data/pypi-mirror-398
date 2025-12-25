import re
from typing import Optional

import pytest

from confee import ConfigBase, HelpFormatter
from confee.overrides import ErrorFormatter


class HelpSample(ConfigBase):
    name: str  # required — should NOT show [default: ...]
    debug: bool = False
    workers: int = 4
    note: Optional[str] = None  # should show [default: None]


def _line_for_option(help_text: str, option: str) -> str:
    # Find the line that starts with the option flag, e.g., "  --name"
    for line in help_text.splitlines():
        if re.match(rf"\s*--{re.escape(option)}\b", line.strip()):
            return line
        # help formatter prints with indentation and color codes; be tolerant
        if f"--{option}" in line:
            return line
    return ""


class TestHelpFormatterDefaults:
    def test_required_field_hides_default_segment(self):
        text = HelpFormatter.generate_help(HelpSample)
        line = _line_for_option(text, "name")
        assert "--name" in line
        assert "[default:" not in line  # no default segment for required fields

    def test_none_default_is_rendered(self):
        text = HelpFormatter.generate_help(HelpSample)
        line = _line_for_option(text, "note")
        assert "--note" in line
        assert "[default: None]" in line

    def test_concrete_defaults_are_rendered(self):
        text = HelpFormatter.generate_help(HelpSample)
        debug_line = _line_for_option(text, "debug")
        workers_line = _line_for_option(text, "workers")
        assert "[default: False]" in debug_line
        assert "[default: 4]" in workers_line


class TestErrorFormatter:
    def test_compact_missing_field_message(self):
        class X(ConfigBase):
            name: str

        # Trigger validation error by omitting required field
        with pytest.raises(Exception) as ei:
            X()
        msg = ErrorFormatter.format_validation_error(ei.value, style="compact")
        # Either explicit field or generic validation failed message
        assert "missing required field 'name'" in msg or msg == "Config error: validation failed"

    def test_compact_non_validation_error(self):
        err = RuntimeError("boom")
        msg = ErrorFormatter.format_validation_error(err, style="compact")
        assert msg == "Error: boom"
