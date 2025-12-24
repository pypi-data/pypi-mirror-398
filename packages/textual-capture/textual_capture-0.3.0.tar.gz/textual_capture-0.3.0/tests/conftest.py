"""Pytest fixtures for textual-capture tests."""

import tempfile
from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Label


class SimpleTestApp(App[None]):
    """Minimal Textual app for testing capture functionality."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Label("Test Application")
        yield Button("Click Me", id="ClickMe")
        yield Button("Another Button", id="AnotherButton")


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp dir so captures are created there
        import os

        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def simple_toml_config(tmp_path: Path) -> Path:
    """Create a simple valid TOML configuration file."""
    toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"
screen_width = 80
screen_height = 24

[[step]]
type = "press"
key = "tab"

[[step]]
type = "delay"
seconds = 0.1

[[step]]
type = "capture"
output = "test_screenshot"
"""
    toml_file = tmp_path / "test_config.toml"
    toml_file.write_text(toml_content)
    return toml_file


@pytest.fixture
def auto_sequence_toml_config(tmp_path: Path) -> Path:
    """Create TOML config with multiple captures using auto-sequencing."""
    toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
# No output specified - should auto-generate capture_001

[[step]]
type = "delay"
seconds = 0.1

[[step]]
type = "capture"
# No output specified - should auto-generate capture_002

[[step]]
type = "capture"
output = "named_capture"

[[step]]
type = "capture"
# Should auto-generate capture_003 (counter continues)
"""
    toml_file = tmp_path / "auto_sequence.toml"
    toml_file.write_text(toml_content)
    return toml_file


@pytest.fixture
def minimal_toml_config(tmp_path: Path) -> Path:
    """Create a minimal TOML config with only required fields."""
    toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "capture"
output = "minimal"
"""
    toml_file = tmp_path / "minimal.toml"
    toml_file.write_text(toml_content)
    return toml_file


@pytest.fixture
def invalid_toml_config(tmp_path: Path) -> Path:
    """Create an invalid TOML config (missing required fields)."""
    toml_content = """
app_module = "tests.conftest"
# Missing app_class

[[step]]
type = "capture"
"""
    toml_file = tmp_path / "invalid.toml"
    toml_file.write_text(toml_content)
    return toml_file


@pytest.fixture
def click_test_toml_config(tmp_path: Path) -> Path:
    """Create TOML config that tests button clicking."""
    toml_content = """
app_module = "tests.conftest"
app_class = "SimpleTestApp"

[[step]]
type = "click"
label = "Click Me"

[[step]]
type = "capture"
output = "after_click"
"""
    toml_file = tmp_path / "click_test.toml"
    toml_file.write_text(toml_content)
    return toml_file
