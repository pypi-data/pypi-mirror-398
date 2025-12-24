"""Tests for features 4-5: key modifiers and capture tooltips."""

import logging
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from textual_capture.capture import capture, execute_action, validate_config

logger = logging.getLogger(__name__)
logging.getLogger("textual_capture").setLevel(logging.DEBUG)


class TestKeyModifiers:
    """Tests for Feature #4: Key Modifier Combinations."""

    async def test_press_keys_list_syntax(self):
        """Press action with list syntax works."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "keys": ["tab", "ctrl+s", "enter"]}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        assert pilot.press.call_count == 3
        calls = [call[0][0] for call in pilot.press.call_args_list]
        assert calls == ["tab", "ctrl+s", "enter"]

    async def test_press_key_string_backwards_compat(self):
        """Press action with single key string (backwards compatible)."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "key": "ctrl+c"}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        pilot.press.assert_called_once_with("ctrl+c")

    async def test_press_key_comma_separated_backwards_compat(self):
        """Press action with comma-separated keys (backwards compatible)."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "key": "tab,ctrl+s,enter"}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        assert pilot.press.call_count == 3
        calls = [call[0][0] for call in pilot.press.call_args_list]
        assert calls == ["tab", "ctrl+s", "enter"]

    async def test_press_pause_between_custom(self):
        """Press action with custom pause_between duration."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "keys": ["tab", "tab"], "pause_between": 0.5}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        # Should pause with custom duration between keys
        pilot.pause.assert_called_once_with(0.5)

    async def test_press_pause_between_default(self):
        """Press action uses default pause_between (0.2s)."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "keys": ["tab", "enter"]}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        # Should pause with default 0.2s between keys
        pilot.pause.assert_called_once_with(0.2)

    async def test_press_no_pause_between_last_key(self):
        """Press action doesn't pause after the last key."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "keys": ["tab"]}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        # Single key - no pause
        pilot.pause.assert_not_called()

    async def test_press_keys_precedence_over_key(self):
        """When both 'keys' and 'key' present, 'keys' takes precedence."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "keys": ["enter"], "key": "tab"}
        config = {}
        await execute_action(pilot, action, config, {"count": 0})

        # Should use 'keys' (enter), not 'key' (tab)
        pilot.press.assert_called_once_with("enter")

    def test_validate_keys_must_be_list(self):
        """Validation fails if 'keys' is not a list."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "press", "keys": "not-a-list"}],
        }

        with pytest.raises(ValueError, match="'keys' must be a list"):
            validate_config(config)

    def test_validate_pause_between_must_be_numeric(self):
        """Validation fails if 'pause_between' is not numeric."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "press", "key": "tab", "pause_between": "not-a-number"}],
        }

        with pytest.raises(ValueError, match="'pause_between' must be a number"):
            validate_config(config)


class TestCaptureTooltips:
    """Tests for Feature #5: Capture Tooltips."""

    async def test_capture_tooltips_enabled_by_default(self, tmp_path: Path, temp_dir: Path):
        """Tooltips are captured by default with every capture."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "default"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Should create tooltip file by default
        assert (temp_dir / "default_tooltips.txt").exists()

    async def test_capture_tooltips_disabled_globally(self, tmp_path: Path, temp_dir: Path):
        """Tooltips can be disabled globally."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
capture_tooltips = false

[[step]]
type = "capture"
output = "no_tooltips"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Should NOT create tooltip file
        assert not (temp_dir / "no_tooltips_tooltips.txt").exists()

    async def test_capture_tooltips_per_step_override(self, tmp_path: Path, temp_dir: Path):
        """Per-step tooltip setting overrides global setting."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
capture_tooltips = false  # Global: disabled

[[step]]
type = "capture"
output = "override_enabled"
capture_tooltips = true  # Override: enabled
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Should create tooltip file (override)
        assert (temp_dir / "override_enabled_tooltips.txt").exists()

    async def test_capture_tooltips_file_format_and_content(self, tmp_path: Path, temp_dir: Path):
        """Tooltip file has correct format with header and widget data."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "formatted"
tooltip_include_empty = true
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        tooltip_file = temp_dir / "formatted_tooltips.txt"
        assert tooltip_file.exists()

        content = tooltip_file.read_text()

        # Check header
        assert "# Tooltips captured from: formatted" in content
        assert "# Selector: *" in content
        assert "# Timestamp:" in content

        # Check widget entries (SimpleTestApp has buttons without tooltips)
        assert "Button#ClickMe:" in content
        assert "Button#AnotherButton:" in content
        # Since SimpleTestApp buttons don't have tooltips, should show "(no tooltip)"
        assert "(no tooltip)" in content

    async def test_capture_tooltips_custom_selector(self, tmp_path: Path, temp_dir: Path):
        """Custom selector filters which widgets are captured."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "buttons_only"
widget_selector = "Button"
tooltip_include_empty = true
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        tooltip_file = temp_dir / "buttons_only_tooltips.txt"
        content = tooltip_file.read_text()

        # Should show Button selector
        assert "# Selector: Button" in content

        # Should have button entries
        assert "Button#" in content
        assert "ClickMe" in content or "AnotherButton" in content

    async def test_capture_tooltips_include_empty_false(self, tmp_path: Path, temp_dir: Path):
        """By default, widgets without tooltips are excluded."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "exclude_empty"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        tooltip_file = temp_dir / "exclude_empty_tooltips.txt"
        content = tooltip_file.read_text()

        # SimpleTestApp has buttons without tooltips - they should be excluded
        # Count lines with widget data (not header/comments)
        widget_lines = [line for line in content.split("\n") if line and not line.startswith("#")]
        assert len(widget_lines) == 0
        # Should be 0 or minimal since SimpleTestApp buttons don't have tooltips by default
        # (This test verifies the default behavior)

    async def test_capture_tooltips_include_empty_true(self, tmp_path: Path, temp_dir: Path):
        """When include_empty=true, widgets without tooltips are shown."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "include_empty"
tooltip_include_empty = true
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        tooltip_file = temp_dir / "include_empty_tooltips.txt"
        content = tooltip_file.read_text()

        # Should include entries for all widgets
        assert "Button#ClickMe:" in content
        assert "Button#AnotherButton:" in content

        # Should show "(no tooltip)" for empty ones
        assert "(no tooltip)" in content

    async def test_capture_tooltips_with_output_dir(self, tmp_path: Path):
        """Tooltips respect output_dir setting."""
        output_dir = tmp_path / "captures"
        toml_content = f"""
app_module = "tests.conftest"
app_class = "SimpleTestApp"
output_dir = "{output_dir}"

[[step]]
type = "capture"
output = "in_subdir"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Should be in output_dir
        assert (output_dir / "in_subdir_tooltips.txt").exists()

    async def test_capture_tooltips_auto_sequence(self, tmp_path: Path, temp_dir: Path):
        """Auto-sequenced captures generate tooltip files with sequential names."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
# Auto: capture_001

[[step]]
type = "capture"
# Auto: capture_002
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        assert (temp_dir / "capture_001_tooltips.txt").exists()
        assert (temp_dir / "capture_002_tooltips.txt").exists()

    async def test_capture_formats_empty_with_tooltips_valid(self, tmp_path: Path, temp_dir: Path):
        """Empty formats list is valid when tooltips are enabled."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = []
capture_tooltips = true

[[step]]
type = "capture"
output = "tooltips_only"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Should create only tooltip file
        assert (temp_dir / "tooltips_only_tooltips.txt").exists()
        assert not (temp_dir / "tooltips_only.svg").exists()
        assert not (temp_dir / "tooltips_only.txt").exists()

    def test_capture_formats_empty_without_tooltips_invalid(self):
        """Empty formats with tooltips disabled is invalid (no output)."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "capture", "formats": [], "capture_tooltips": False}],
        }

        with pytest.raises(ValueError, match="must produce at least one output"):
            validate_config(config)

    def test_validate_capture_requires_at_least_one_output(self):
        """Validation requires at least one output from capture."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "formats": [],
            "capture_tooltips": False,
            "step": [{"type": "capture"}],
        }

        with pytest.raises(ValueError, match="must produce at least one output"):
            validate_config(config)

    def test_validate_capture_tooltips_bool(self):
        """Validation fails if capture_tooltips is not boolean."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "capture_tooltips": "yes",  # Should be bool
        }

        with pytest.raises(ValueError, match="'capture_tooltips' must be a boolean"):
            validate_config(config)

    def test_validate_widget_selector_string(self):
        """Validation fails if widget_selector is not string."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "widget_selector": 123,  # Should be string
        }

        with pytest.raises(ValueError, match="'widget_selector' must be a string"):
            validate_config(config)

    def test_validate_tooltip_include_empty_bool(self):
        """Validation fails if tooltip_include_empty is not boolean."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "tooltip_include_empty": "yes",  # Should be bool
        }

        with pytest.raises(ValueError, match="'tooltip_include_empty' must be a boolean"):
            validate_config(config)

    def test_validate_per_step_tooltip_settings(self):
        """Validation checks per-step tooltip settings."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "capture", "capture_tooltips": "not-bool"}],
        }

        with pytest.raises(ValueError, match="'capture_tooltips' must be a boolean"):
            validate_config(config)


class TestDryRunNewFeatures:
    """Tests for dry-run display of new features."""

    def test_dry_run_shows_keys_list(self, tmp_path: Path, capsys):
        """Dry-run displays keys list syntax."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "press"
keys = ["tab", "ctrl+s"]
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(SystemExit) as exc_info:
            import sys

            from textual_capture.capture import main

            sys.argv = ["textual-capture", str(toml_file), "--dry-run"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "keys=['tab', 'ctrl+s']" in captured.out

    def test_dry_run_shows_pause_between(self, tmp_path: Path, capsys):
        """Dry-run displays custom pause_between."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "press"
keys = ["tab"]
pause_between = 0.5
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(SystemExit) as exc_info:
            import sys

            from textual_capture.capture import main

            sys.argv = ["textual-capture", str(toml_file), "--dry-run"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "pause_between=0.5s" in captured.out

    def test_dry_run_shows_tooltip_settings(self, tmp_path: Path, capsys):
        """Dry-run displays tooltip configuration."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
capture_tooltips = true
widget_selector = "Button"

[[step]]
type = "capture"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(SystemExit) as exc_info:
            import sys

            from textual_capture.capture import main

            sys.argv = ["textual-capture", str(toml_file), "--dry-run"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Capture Tooltips: True" in captured.out
        assert "Tooltip Selector: Button" in captured.out

    def test_dry_run_shows_tooltips_in_capture_step(self, tmp_path: Path, capsys):
        """Dry-run shows tooltip info for capture steps."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "test"
widget_selector = "Button"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(SystemExit) as exc_info:
            import sys

            from textual_capture.capture import main

            sys.argv = ["textual-capture", str(toml_file), "--dry-run"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "tooltips=Button" in captured.out

    def test_dry_run_shows_tooltip_only_capture(self, tmp_path: Path, capsys):
        """Dry-run displays tooltip-only captures correctly."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = []
capture_tooltips = true

[[step]]
type = "capture"
output = "tooltips_only"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(SystemExit) as exc_info:
            import sys

            from textual_capture.capture import main

            sys.argv = ["textual-capture", str(toml_file), "--dry-run"]
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Should show empty formats and tooltips enabled
        assert 'output="tooltips_only"' in captured.out
        assert "tooltips=*" in captured.out


class TestIntegrationNewFeatures:
    """Integration tests combining new features."""

    async def test_keys_list_with_modifiers_integration(self, tmp_path: Path, temp_dir: Path):
        """Complete sequence using keys list with modifiers."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "press"
keys = ["tab", "ctrl+a"]

[[step]]
type = "capture"
output = "after_keys"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        # Should not raise
        await capture(str(toml_file))

        assert (temp_dir / "after_keys.svg").exists()
        assert (temp_dir / "after_keys_tooltips.txt").exists()

    async def test_mixed_formats_and_tooltips(self, tmp_path: Path, temp_dir: Path):
        """Different captures with different format and tooltip settings."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "full"
formats = ["svg", "txt"]
capture_tooltips = true

[[step]]
type = "capture"
output = "visual_only"
formats = ["svg"]
capture_tooltips = false

[[step]]
type = "capture"
output = "metadata_only"
formats = []
capture_tooltips = true
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Full capture
        assert (temp_dir / "full.svg").exists()
        assert (temp_dir / "full.txt").exists()
        assert (temp_dir / "full_tooltips.txt").exists()

        # Visual only
        assert (temp_dir / "visual_only.svg").exists()
        assert not (temp_dir / "visual_only.txt").exists()
        assert not (temp_dir / "visual_only_tooltips.txt").exists()

        # Metadata only
        assert not (temp_dir / "metadata_only.svg").exists()
        assert not (temp_dir / "metadata_only.txt").exists()
        assert (temp_dir / "metadata_only_tooltips.txt").exists()
