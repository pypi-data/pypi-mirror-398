"""Tests for new features: dry-run, output_dir, selective formats."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from textual_capture.capture import capture, execute_action, main, validate_config


class TestOutputDirectory:
    """Tests for output_dir configuration (Feature #2)."""

    async def test_output_dir_created_automatically(self, tmp_path: Path, simple_toml_config: Path):
        """Output directory is created if it doesn't exist."""
        # Add output_dir to config
        config_content = simple_toml_config.read_text()
        output_dir = tmp_path / "screenshots"
        config_content = f'output_dir = "{output_dir}"\n' + config_content

        new_config = tmp_path / "with_output_dir.toml"
        new_config.write_text(config_content)

        await capture(str(new_config))

        # Check directory was created
        assert output_dir.exists()
        assert output_dir.is_dir()

        # Check files were placed in that directory
        assert (output_dir / "test_screenshot.svg").exists()
        assert (output_dir / "test_screenshot.txt").exists()

    async def test_output_dir_nested_path(self, tmp_path: Path, minimal_toml_config: Path):
        """Nested output directories are created with parents=True."""
        config_content = minimal_toml_config.read_text()
        output_dir = tmp_path / "deeply" / "nested" / "screenshots"
        config_content = f'output_dir = "{output_dir}"\n' + config_content

        new_config = tmp_path / "nested_config.toml"
        new_config.write_text(config_content)

        await capture(str(new_config))

        assert output_dir.exists()
        assert (output_dir / "minimal.svg").exists()

    def test_invalid_output_dir_raises_error(self, tmp_path: Path):
        """Invalid output directory path raises ValueError during validation."""
        # Create a file where we want the directory
        blocking_file = tmp_path / "blocking_file"
        blocking_file.write_text("block")

        config = {
            "app_module": "test",
            "app_class": "Test",
            "output_dir": str(blocking_file / "subdir"),  # Can't create dir under file
        }

        with pytest.raises(ValueError, match="Cannot create output directory"):
            validate_config(config)

    async def test_default_output_dir_is_cwd(self, tmp_path: Path, minimal_toml_config: Path, temp_dir: Path):
        """Default output directory is current working directory."""
        await capture(str(minimal_toml_config))

        # Files should be in temp_dir (CWD for tests via temp_dir fixture)
        assert (temp_dir / "minimal.svg").exists()
        assert (temp_dir / "minimal.txt").exists()


class TestSelectiveFormats:
    """Tests for selective format configuration (Feature #3)."""

    async def test_global_formats_svg_only(self, tmp_path: Path, temp_dir: Path):
        """Global formats=['svg'] produces only SVG files."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = ["svg"]

[[step]]
type = "capture"
output = "svg_only"
"""
        toml_file = tmp_path / "svg_only.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        assert (temp_dir / "svg_only.svg").exists()
        assert not (temp_dir / "svg_only.txt").exists()

    async def test_global_formats_txt_only(self, tmp_path: Path, temp_dir: Path):
        """Global formats=['txt'] produces only TXT files."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = ["txt"]

[[step]]
type = "capture"
output = "txt_only"
"""
        toml_file = tmp_path / "txt_only.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        assert (temp_dir / "txt_only.txt").exists()
        assert not (temp_dir / "txt_only.svg").exists()

    async def test_per_step_format_override(self, tmp_path: Path, temp_dir: Path):
        """Per-step formats override global default."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = ["svg", "txt"]  # Global default

[[step]]
type = "capture"
output = "uses_global"
# Should use global: svg and txt

[[step]]
type = "capture"
output = "overrides_to_svg"
formats = ["svg"]  # Override
"""
        toml_file = tmp_path / "override.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # First capture uses global
        assert (temp_dir / "uses_global.svg").exists()
        assert (temp_dir / "uses_global.txt").exists()

        # Second capture overrides
        assert (temp_dir / "overrides_to_svg.svg").exists()
        assert not (temp_dir / "overrides_to_svg.txt").exists()

    async def test_auto_sequence_with_formats(self, tmp_path: Path, temp_dir: Path):
        """Auto-sequenced captures respect format settings."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = ["svg"]

[[step]]
type = "capture"
# Auto-sequence with svg only

[[step]]
type = "capture"
# Auto-sequence with svg only
"""
        toml_file = tmp_path / "auto_formats.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        assert (temp_dir / "capture_001.svg").exists()
        assert not (temp_dir / "capture_001.txt").exists()
        assert (temp_dir / "capture_002.svg").exists()
        assert not (temp_dir / "capture_002.txt").exists()

    def test_invalid_format_in_global_config(self):
        """Invalid format in global config raises ValueError."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "formats": ["svg", "invalid_format"],
        }

        with pytest.raises(ValueError, match="Invalid format.*invalid_format"):
            validate_config(config)

    def test_invalid_format_in_step(self):
        """Invalid format in step raises ValueError."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "capture", "formats": ["html"]}],
        }

        with pytest.raises(ValueError, match="Invalid format.*html"):
            validate_config(config)

    def test_formats_must_be_list(self):
        """formats field must be a list, not a string."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "formats": "svg",  # Should be ["svg"]
        }

        with pytest.raises(ValueError, match="'formats' must be a list"):
            validate_config(config)

    def test_step_formats_must_be_list(self):
        """Step formats must be a list."""
        config = {
            "app_module": "test",
            "app_class": "Test",
            "step": [{"type": "capture", "formats": "svg"}],  # Should be ["svg"]
        }

        with pytest.raises(ValueError, match="'formats' must be a list"):
            validate_config(config)

    async def test_default_formats_both_svg_and_txt(self, tmp_path: Path, temp_dir: Path):
        """Default formats (if not specified) are svg and txt."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
# No formats specified - should default to both

[[step]]
type = "capture"
output = "default_formats"
"""
        toml_file = tmp_path / "default.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        assert (temp_dir / "default_formats.svg").exists()
        assert (temp_dir / "default_formats.txt").exists()


class TestDryRun:
    """Tests for dry-run mode (Feature #1)."""

    def test_dry_run_shows_configuration(self, simple_toml_config: Path, capsys):
        """Dry-run displays configuration summary."""
        with patch("sys.argv", ["textual-capture", str(simple_toml_config), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = captured.out

            # Check key information is displayed
            assert "Configuration:" in output
            assert "App: tests.conftest.SimpleTestApp" in output
            assert "Screen: 80x24" in output
            assert "Planned Steps" in output

    def test_dry_run_shows_steps(self, simple_toml_config: Path, capsys):
        """Dry-run lists all planned steps."""
        with patch("sys.argv", ["textual-capture", str(simple_toml_config), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = captured.out

            # Check steps are listed
            assert "1. press:" in output
            assert "2. delay:" in output
            assert "3. capture:" in output

    def test_dry_run_validates_import(self, simple_toml_config: Path, capsys):
        """Dry-run tests module import without running app."""
        with patch("sys.argv", ["textual-capture", str(simple_toml_config), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = captured.out

            assert "Validating module import" in output
            assert "Successfully imported SimpleTestApp from tests.conftest" in output

    def test_dry_run_catches_invalid_module(self, tmp_path: Path, capsys):
        """Dry-run catches import errors."""
        toml_content = """
app_module = "nonexistent_module"
app_class = "SomeClass"
"""
        toml_file = tmp_path / "bad.toml"
        toml_file.write_text(toml_content)

        with patch("sys.argv", ["textual-capture", str(toml_file), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            output = captured.out

            assert "Import failed" in output

    def test_dry_run_catches_invalid_class(self, tmp_path: Path, capsys):
        """Dry-run catches class not found errors."""
        toml_content = """
app_module = "tests.conftest"
app_class = "NonexistentClass"
"""
        toml_file = tmp_path / "bad.toml"
        toml_file.write_text(toml_content)

        with patch("sys.argv", ["textual-capture", str(toml_file), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            output = captured.out

            assert "Class not found" in output

    def test_dry_run_catches_config_errors(self, invalid_toml_config: Path, caplog):
        """Dry-run catches configuration validation errors."""
        with patch("sys.argv", ["textual-capture", str(invalid_toml_config), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            assert "Configuration error" in caplog.text or "app_class" in caplog.text

    def test_dry_run_shows_auto_sequenced_names(self, auto_sequence_toml_config: Path, capsys):
        """Dry-run shows auto-generated capture names."""
        with patch("sys.argv", ["textual-capture", str(auto_sequence_toml_config), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = captured.out

            # Should show auto-generated names in plan
            assert "capture_001" in output
            assert "capture_002" in output
            assert "named_capture" in output
            assert "capture_003" in output

    def test_dry_run_shows_output_dir(self, tmp_path: Path, capsys):
        """Dry-run displays output directory setting."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
output_dir = "./screenshots"

[[step]]
type = "capture"
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with patch("sys.argv", ["textual-capture", str(toml_file), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = captured.out

            assert "Output Directory: ./screenshots" in output

    def test_dry_run_shows_formats(self, tmp_path: Path, capsys):
        """Dry-run displays format settings."""
        toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
formats = ["svg"]

[[step]]
type = "capture"
output = "test"
formats = ["txt"]
"""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(toml_content)

        with patch("sys.argv", ["textual-capture", str(toml_file), "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = captured.out

            assert "Default Formats: svg" in output
            assert "formats=[txt]" in output  # Per-step override shown


class TestExecuteActionWithConfig:
    """Tests that execute_action properly uses config parameter."""

    async def test_execute_action_uses_output_dir_from_config(self, tmp_path: Path):
        """execute_action respects output_dir from config."""
        output_dir = tmp_path / "screenshots"
        output_dir.mkdir()

        pilot = Mock()
        pilot.app = Mock()
        pilot.app.save_screenshot = Mock()

        config = {"output_dir": str(output_dir), "formats": ["svg", "txt"]}
        action = {"type": "capture", "output": "test"}

        await execute_action(pilot, action, config, {"count": 0})

        # Check that save_screenshot was called with paths in output_dir
        calls = [call[0][0] for call in pilot.app.save_screenshot.call_args_list]
        assert str(output_dir / "test.svg") in calls
        assert str(output_dir / "test.txt") in calls

    async def test_execute_action_uses_global_formats(self, tmp_path: Path):
        """execute_action uses global formats from config if not overridden."""
        pilot = Mock()
        pilot.app = Mock()
        pilot.app.save_screenshot = Mock()

        config = {"formats": ["svg"]}  # Only SVG globally
        action = {"type": "capture", "output": "test"}

        await execute_action(pilot, action, config, {"count": 0})

        # Should only save SVG
        calls = [call[0][0] for call in pilot.app.save_screenshot.call_args_list]
        assert any("test.svg" in call for call in calls)
        assert not any("test.txt" in call for call in calls)

    async def test_execute_action_per_step_format_overrides_global(self, tmp_path: Path):
        """execute_action uses per-step formats over global config."""
        pilot = Mock()
        pilot.app = Mock()
        pilot.app.save_screenshot = Mock()

        config = {"formats": ["svg", "txt"]}  # Global default
        action = {"type": "capture", "output": "test", "formats": ["txt"]}  # Override

        await execute_action(pilot, action, config, {"count": 0})

        # Should only save TXT (override)
        calls = [call[0][0] for call in pilot.app.save_screenshot.call_args_list]
        assert any("test.txt" in call for call in calls)
        assert not any("test.svg" in call for call in calls)


class TestIntegrationNewFeatures:
    """Integration tests combining multiple new features."""

    async def test_output_dir_with_selective_formats(self, tmp_path: Path):
        """Output directory and selective formats work together."""
        output_dir = tmp_path / "captures"
        toml_content = f"""
app_module = "tests.conftest"
app_class = "SimpleTestApp"
output_dir = "{output_dir}"
formats = ["svg"]

[[step]]
type = "capture"
output = "svg_only"

[[step]]
type = "capture"
output = "txt_only"
formats = ["txt"]
"""
        toml_file = tmp_path / "combined.toml"
        toml_file.write_text(toml_content)

        await capture(str(toml_file))

        # Check output_dir was created
        assert output_dir.exists()

        # Check format selection worked
        assert (output_dir / "svg_only.svg").exists()
        assert not (output_dir / "svg_only.txt").exists()

        assert (output_dir / "txt_only.txt").exists()
        assert not (output_dir / "txt_only.svg").exists()
