"""Comprehensive tests for textual-capture."""

import contextlib
import logging
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from textual_capture.capture import capture, execute_action, main, validate_config


class TestTOMLLoading:
    """Tests for TOML file loading and parsing."""

    async def test_valid_toml_loads(self, simple_toml_config: Path, temp_dir: Path):
        """Valid TOML file loads and parses correctly."""
        # Should not raise
        await capture(str(simple_toml_config))
        # Check output files were created
        assert (temp_dir / "test_screenshot.svg").exists()
        assert (temp_dir / "test_screenshot.txt").exists()

    async def test_missing_file_raises_error(self):
        """Missing TOML file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="TOML file not found"):
            await capture("nonexistent.toml")

    async def test_invalid_toml_syntax(self, tmp_path: Path):
        """Invalid TOML syntax raises ValueError."""
        bad_toml = tmp_path / "bad.toml"
        bad_toml.write_text("[unclosed section")

        with pytest.raises(ValueError, match="Failed to parse TOML"):
            await capture(str(bad_toml))

    def test_missing_required_field_app_module(self):
        """Missing app_module raises ValueError."""
        config = {"app_class": "SomeClass"}
        with pytest.raises(ValueError, match="missing required field: 'app_module'"):
            validate_config(config)

    def test_missing_required_field_app_class(self):
        """Missing app_class raises ValueError."""
        config = {"app_module": "some.module"}
        with pytest.raises(ValueError, match="missing required field: 'app_class'"):
            validate_config(config)


class TestActionExecution:
    """Tests for individual action execution."""

    async def test_press_action_single_key(self):
        """Press action with single key works."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "key": "tab"}
        await execute_action(pilot, action, {}, {"count": 0})

        pilot.press.assert_called_once_with("tab")

    async def test_press_action_multiple_keys(self):
        """Press action with comma-separated keys works."""
        pilot = Mock()
        pilot.press = AsyncMock()
        pilot.pause = AsyncMock()

        action = {"type": "press", "key": "tab,enter,down"}
        await execute_action(pilot, action, {}, {"count": 0})

        assert pilot.press.call_count == 3
        calls = [call[0][0] for call in pilot.press.call_args_list]
        assert calls == ["tab", "enter", "down"]

    async def test_delay_action(self):
        """Delay action pauses correctly."""
        pilot = Mock()
        pilot.pause = AsyncMock()

        action = {"type": "delay", "seconds": 1.5}
        await execute_action(pilot, action, {}, {"count": 0})

        pilot.pause.assert_called_once_with(1.5)

    async def test_delay_action_default(self):
        """Delay action uses default if seconds not specified."""
        pilot = Mock()
        pilot.pause = AsyncMock()

        action = {"type": "delay"}
        await execute_action(pilot, action, {}, {"count": 0})

        pilot.pause.assert_called_once_with(0.5)

    async def test_click_action(self):
        """Click action finds and clicks button."""
        pilot = Mock()
        pilot.click = AsyncMock()

        action = {"type": "click", "label": "Click Me"}
        await execute_action(pilot, action, {}, {"count": 0})

        pilot.click.assert_called_once_with("Button#ClickMe")

    async def test_click_action_missing_label(self):
        """Click action without label raises ValueError."""
        pilot = Mock()
        action = {"type": "click"}

        with pytest.raises(ValueError, match="missing required 'label' field"):
            await execute_action(pilot, action, {}, {"count": 0})

    async def test_capture_action_with_explicit_name(self, temp_dir: Path):
        """Capture action with explicit output name saves files."""
        pilot = Mock()
        pilot.app = Mock()
        pilot.app.save_screenshot = Mock()

        action = {"type": "capture", "output": "my_screenshot"}
        await execute_action(pilot, action, {}, {"count": 0})

        assert pilot.app.save_screenshot.call_count == 2
        calls = [call[0][0] for call in pilot.app.save_screenshot.call_args_list]
        assert "my_screenshot.svg" in calls
        assert "my_screenshot.txt" in calls

    async def test_capture_action_auto_sequence(self, temp_dir: Path):
        """Capture action without output auto-generates sequential names."""
        pilot = Mock()
        pilot.app = Mock()
        pilot.app.save_screenshot = Mock()

        counter = {"count": 0}
        action = {"type": "capture"}

        # First capture
        await execute_action(pilot, action, {}, counter)
        calls = [call[0][0] for call in pilot.app.save_screenshot.call_args_list]
        assert "capture_001.svg" in calls
        assert "capture_001.txt" in calls

        # Reset mock
        pilot.app.save_screenshot.reset_mock()

        # Second capture
        await execute_action(pilot, action, {}, counter)
        calls = [call[0][0] for call in pilot.app.save_screenshot.call_args_list]
        assert "capture_002.svg" in calls
        assert "capture_002.txt" in calls

    async def test_unknown_action_type_raises_error(self):
        """Unknown action type raises ValueError."""
        pilot = Mock()
        action = {"type": "unknown_action"}

        with pytest.raises(ValueError, match="Unknown action type: unknown_action"):
            await execute_action(pilot, action, {}, {"count": 0})


class TestDynamicImport:
    """Tests for dynamic module/class importing."""

    async def test_valid_import(self, minimal_toml_config: Path, temp_dir: Path):
        """Valid module and class imports successfully."""
        # Should not raise - uses SimpleTestApp from conftest
        await capture(str(minimal_toml_config))

    async def test_invalid_module_name(self, tmp_path: Path):
        """Invalid module name raises ImportError."""
        toml_content = """
app_module = "nonexistent_module"
app_class = "SomeClass"
"""
        toml_file = tmp_path / "bad_module.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(ImportError, match="Failed to import module"):
            await capture(str(toml_file))

    async def test_invalid_class_name(self, tmp_path: Path):
        """Invalid class name raises AttributeError."""
        toml_content = """
app_module = "tests.conftest"
app_class = "NonexistentClass"
"""
        toml_file = tmp_path / "bad_class.toml"
        toml_file.write_text(toml_content)

        with pytest.raises(AttributeError, match="has no class"):
            await capture(str(toml_file))


class TestIntegration:
    """End-to-end integration tests."""

    async def test_complete_sequence(self, simple_toml_config: Path, temp_dir: Path):
        """Complete sequence runs end-to-end."""
        await capture(str(simple_toml_config))

        # Verify output files exist
        assert (temp_dir / "test_screenshot.svg").exists()
        assert (temp_dir / "test_screenshot.txt").exists()

    async def test_multiple_captures_in_sequence(self, auto_sequence_toml_config: Path, temp_dir: Path):
        """Multiple captures in sequence work correctly."""
        await capture(str(auto_sequence_toml_config))

        # Check auto-sequenced captures
        assert (temp_dir / "capture_001.svg").exists()
        assert (temp_dir / "capture_001.txt").exists()
        assert (temp_dir / "capture_002.svg").exists()
        assert (temp_dir / "capture_002.txt").exists()

        # Check named capture
        assert (temp_dir / "named_capture.svg").exists()
        assert (temp_dir / "named_capture.txt").exists()

        # Check auto-sequence continues after named capture
        assert (temp_dir / "capture_003.svg").exists()
        assert (temp_dir / "capture_003.txt").exists()

    async def test_click_button_integration(self, click_test_toml_config: Path, temp_dir: Path):
        """Button clicking works in integration."""
        await capture(str(click_test_toml_config))

        # Should complete without errors
        assert (temp_dir / "after_click.svg").exists()


class TestErrorHandling:
    """Tests for error handling."""

    async def test_click_nonexistent_button(self, tmp_path: Path):
        """Clicking non-existent button raises appropriate error."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "click"
label = "Nonexistent Button"
"""
        toml_file = tmp_path / "bad_click.toml"
        toml_file.write_text(toml_content)

        # Should raise an error when clicking nonexistent button
        with pytest.raises((ValueError, KeyError, AttributeError, Exception)):
            await capture(str(toml_file))

    def test_step_missing_type_field(self):
        """Step without type field fails validation."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"action": "something"}],  # Missing 'type'
        }
        with pytest.raises(ValueError, match="missing required 'type' field"):
            validate_config(config)

    def test_invalid_step_type(self):
        """Step with invalid type fails validation."""
        config = {"app_module": "test", "app_class": "Test", "step": [{"type": "invalid_type"}]}
        with pytest.raises(ValueError, match="invalid type"):
            validate_config(config)

    def test_click_step_missing_label(self):
        """Click step without label fails validation."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "click"}],  # Missing label
        }
        with pytest.raises(ValueError, match="missing required 'label' field"):
            validate_config(config)


class TestCLIFlags:
    """Tests for CLI flag handling."""

    def test_verbose_flag_sets_info_logging(self):
        """--verbose flag enables INFO level logging."""
        with (
            patch("sys.argv", ["textual-capture", "test.toml", "--verbose"]),
            patch("asyncio.run"),
            patch("logging.basicConfig") as mock_basic_config,
            contextlib.suppress(SystemExit),
        ):
            main()
            # Check that INFO level was set
            mock_basic_config.assert_called_once()
            assert mock_basic_config.call_args[1]["level"] == logging.INFO

    def test_quiet_flag_sets_error_logging(self):
        """--quiet flag sets ERROR level logging."""
        with (
            patch("sys.argv", ["textual-capture", "test.toml", "--quiet"]),
            patch("asyncio.run"),
            patch("logging.basicConfig") as mock_basic_config,
            contextlib.suppress(SystemExit),
        ):
            main()
            # Check that ERROR level was set
            mock_basic_config.assert_called_once()
            assert mock_basic_config.call_args[1]["level"] == logging.ERROR

    def test_default_logging_level(self):
        """Default logging level is WARNING."""
        with (
            patch("sys.argv", ["textual-capture", "test.toml"]),
            patch("asyncio.run"),
            patch("logging.basicConfig") as mock_basic_config,
            contextlib.suppress(SystemExit),
        ):
            main()
            # Check that WARNING level was set (default)
            mock_basic_config.assert_called_once()
            assert mock_basic_config.call_args[1]["level"] == logging.WARNING


class TestConfigurationOptions:
    """Tests for TOML configuration options."""

    async def test_screen_size_configuration(self, tmp_path: Path, temp_dir: Path):
        """Screen width and height are applied correctly."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
screen_width = 120
screen_height = 50

[[step]]
type = "capture"
output = "sized"
"""
        toml_file = tmp_path / "sized.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))
        assert (temp_dir / "sized.svg").exists()

    async def test_scroll_to_top_disabled(self, tmp_path: Path, temp_dir: Path):
        """scroll_to_top can be disabled."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
scroll_to_top = false

[[step]]
type = "capture"
output = "no_scroll"
"""
        toml_file = tmp_path / "no_scroll.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))
        assert (temp_dir / "no_scroll.svg").exists()

    async def test_initial_delay_configuration(self, tmp_path: Path, temp_dir: Path):
        """initial_delay can be configured."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
initial_delay = 0.1

[[step]]
type = "capture"
output = "fast_start"
"""
        toml_file = tmp_path / "fast_start.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))
        assert (temp_dir / "fast_start.svg").exists()
