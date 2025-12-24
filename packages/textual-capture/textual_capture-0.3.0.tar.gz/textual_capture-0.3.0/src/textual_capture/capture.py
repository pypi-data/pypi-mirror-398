"""
Textual Capture - Sequenced screenshot capture for Textual TUI applications.

Automates interaction sequences (key presses, clicks, delays) and captures
multiple screenshots at key moments. Configured via TOML files.

Usage:
    textual-capture sequence.toml              # Quiet mode (errors only)
    textual-capture sequence.toml --verbose    # Show all actions
    textual-capture sequence.toml --quiet      # Suppress all output
    textual-capture sequence.toml --dry-run    # Validate without executing
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Python 3.10 compatibility - tomllib added in 3.11
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# Configure logging
logger = logging.getLogger("textual_capture")

# Valid output formats
VALID_FORMATS = ["svg", "txt"]


def _extract_tooltips(app: Any, selector: str, include_empty: bool, capture_name: str) -> str:
    """
    Extract tooltips from widgets matching selector.

    Args:
        app: Textual app instance
        selector: CSS selector for widgets
        include_empty: Include widgets without tooltips
        capture_name: Name of capture (for header)

    Returns:
        Formatted tooltip data as string
    """
    lines = [
        f"# Tooltips captured from: {capture_name}",
        f"# Selector: {selector}",
        f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    try:
        # Query returns a DOMQuery object, need to iterate through results
        query_result = app.query(selector)
        widgets = list(query_result.results())

        for widget in widgets:
            # Get widget identifier
            widget_type = widget.__class__.__name__
            widget_id = widget.id or "(no-id)"
            identifier = f"{widget_type}#{widget_id}"

            # Get tooltip
            tooltip = getattr(widget, "tooltip", None)

            # Handle Rich renderables
            if tooltip and not isinstance(tooltip, str):
                try:
                    from io import StringIO

                    from rich.console import Console

                    string_io = StringIO()
                    console = Console(file=string_io, force_terminal=False)
                    console.print(tooltip)
                    tooltip = string_io.getvalue().strip()
                except Exception:
                    tooltip = "(complex tooltip)"

            # Include or skip empty
            if tooltip or include_empty:
                tooltip_text = tooltip or "(no tooltip)"
                lines.append(f"{identifier}: {tooltip_text}")

        if len(lines) == 4:  # Only header, no widgets
            lines.append("# No widgets found matching selector")

    except Exception as e:
        lines.append(f"# Error extracting tooltips: {e}")

    return "\n".join(lines)


async def execute_action(
    pilot: Any, action: dict[str, Any], config: dict[str, Any], capture_counter: dict[str, int]
) -> None:
    """
    Execute a single action in the sequence.

    Args:
        pilot: Textual pilot instance for controlling the app
        action: Action configuration dict with 'type' and action-specific fields
        config: Full TOML configuration (for output_dir, formats, etc.)
        capture_counter: Mutable dict tracking number of captures (for auto-sequencing)

    Raises:
        ValueError: If action type is unknown or required fields are missing
    """
    action_type = action.get("type")

    if action_type == "press":
        # Support both 'keys' (list) and 'key' (string) for backwards compatibility
        keys_list = action.get("keys")

        if keys_list is None:
            # Fallback to 'key' field (comma-separated string)
            key_string = action.get("key", "")
            if not key_string:
                logger.warning("press action has no keys specified")
                return
            keys_list = [k.strip() for k in key_string.split(",") if k.strip()]

        pause_between = float(action.get("pause_between", 0.2))

        for i, key in enumerate(keys_list):
            await pilot.press(key)
            # Pause between keys (not after last key)
            if i < len(keys_list) - 1:
                await pilot.pause(pause_between)

        logger.info(f"Pressed keys: {keys_list}")

    elif action_type == "delay":
        seconds = float(action.get("seconds", 0.5))
        await pilot.pause(seconds)
        logger.info(f"Delayed {seconds}s")

    elif action_type == "click":
        label = action.get("label")
        if not label:
            raise ValueError("click action missing required 'label' field")

        try:
            # Textual button ID is ButtonLabel without spaces
            button_id = f"Button#{label.replace(' ', '')}"
            await pilot.click(button_id)
            logger.info(f"Clicked button: {label}")
        except Exception as e:
            logger.error(f"Could not click button '{label}': {e}")
            raise

    elif action_type == "capture":
        # Get output directory from config
        output_dir = Path(config.get("output_dir", "."))

        # Auto-sequencing: if output not specified, generate sequential name
        output = action.get("output")
        if not output:
            capture_counter["count"] += 1
            output = f"capture_{capture_counter['count']:03d}"

        # Get formats: per-step override or global default
        formats = action.get("formats", config.get("formats", VALID_FORMATS))

        # Save each requested format
        captured_outputs = []
        if formats:
            for fmt in formats:
                file_path = output_dir / f"{output}.{fmt}"
                pilot.app.save_screenshot(str(file_path))
            captured_outputs.append(f"formats=[{','.join(formats)}]")
            logger.info(f"Captured screenshots: {output}.{{{','.join(formats)}}} in {output_dir}")

        # Capture tooltips if enabled
        capture_tooltips = action.get("capture_tooltips", config.get("capture_tooltips", True))

        if capture_tooltips:
            selector = action.get("widget_selector", config.get("widget_selector", "*"))
            include_empty = action.get("tooltip_include_empty", config.get("tooltip_include_empty", False))

            tooltip_path = output_dir / f"{output}_tooltips.txt"
            tooltip_data = _extract_tooltips(pilot.app, selector, include_empty, output)
            tooltip_path.write_text(tooltip_data)
            captured_outputs.append("tooltips")
            logger.info(f"Captured tooltips: {tooltip_path}")

        logger.info(f"Capture '{output}' complete: {' + '.join(captured_outputs)}")

    else:
        raise ValueError(f"Unknown action type: {action_type}")


def validate_config(config: dict[str, Any]) -> None:
    """
    Validate TOML configuration before execution.

    Args:
        config: Parsed TOML configuration dict

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Required fields
    if "app_module" not in config:
        raise ValueError("TOML config missing required field: 'app_module'")
    if "app_class" not in config:
        raise ValueError("TOML config missing required field: 'app_class'")

    # Validate output_dir if specified
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cannot create output directory '{output_dir}': {e}") from e

    # Validate formats if specified
    if "formats" in config:
        formats = config["formats"]
        if not isinstance(formats, list):
            raise ValueError(f"'formats' must be a list, got {type(formats).__name__}")

        invalid_formats = set(formats) - set(VALID_FORMATS)
        if invalid_formats:
            raise ValueError(f"Invalid format(s): {invalid_formats}. Valid formats are: {VALID_FORMATS}")

    # Validate tooltip settings (global)
    if "capture_tooltips" in config and not isinstance(config["capture_tooltips"], bool):
        raise ValueError("'capture_tooltips' must be a boolean")

    if "widget_selector" in config and not isinstance(config["widget_selector"], str):
        raise ValueError("'widget_selector' must be a string")

    if "tooltip_include_empty" in config and not isinstance(config["tooltip_include_empty"], bool):
        raise ValueError("'tooltip_include_empty' must be a boolean")

    # Validate action steps
    steps = config.get("step", [])
    for i, step in enumerate(steps):
        if "type" not in step:
            raise ValueError(f"Step {i}: missing required 'type' field")

        step_type = step["type"]
        valid_types = {"press", "delay", "click", "capture"}
        if step_type not in valid_types:
            raise ValueError(f"Step {i}: invalid type '{step_type}'. Must be one of: {valid_types}")

        # Validate type-specific required fields
        if step_type == "click" and "label" not in step:
            raise ValueError(f"Step {i}: 'click' action missing required 'label' field")

        # Validate press action
        if step_type == "press":
            if "keys" in step and not isinstance(step["keys"], list):
                raise ValueError(f"Step {i}: 'keys' must be a list")

            if "pause_between" in step:
                try:
                    float(step["pause_between"])
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Step {i}: 'pause_between' must be a number") from e

        # Validate capture action
        if step_type == "capture":
            # Validate per-step formats if specified
            if "formats" in step:
                step_formats = step["formats"]
                if not isinstance(step_formats, list):
                    raise ValueError(f"Step {i}: 'formats' must be a list, got {type(step_formats).__name__}")

                invalid_formats = set(step_formats) - set(VALID_FORMATS)
                if invalid_formats:
                    raise ValueError(
                        f"Step {i}: Invalid format(s): {invalid_formats}. Valid formats are: {VALID_FORMATS}"
                    )

            # Validate per-step tooltip settings
            if "capture_tooltips" in step and not isinstance(step["capture_tooltips"], bool):
                raise ValueError(f"Step {i}: 'capture_tooltips' must be a boolean")

            if "widget_selector" in step and not isinstance(step["widget_selector"], str):
                raise ValueError(f"Step {i}: 'widget_selector' must be a string")

            if "tooltip_include_empty" in step and not isinstance(step["tooltip_include_empty"], bool):
                raise ValueError(f"Step {i}: 'tooltip_include_empty' must be a boolean")

            # Require at least one output
            formats = step.get("formats", config.get("formats", VALID_FORMATS))
            capture_tooltips = step.get("capture_tooltips", config.get("capture_tooltips", True))

            if not formats and not capture_tooltips:
                raise ValueError(
                    f"Step {i}: capture must produce at least one output. "
                    f"Either specify formats or enable capture_tooltips"
                )


def dry_run(config: dict[str, Any], toml_path: str) -> None:
    """
    Perform a dry run - validate config and print execution plan without running.

    Args:
        config: Parsed TOML configuration
        toml_path: Path to TOML file (for display)
    """
    print(f"Configuration: {toml_path}")
    print(f"App: {config['app_module']}.{config['app_class']}")
    print(f"Screen: {config.get('screen_width', 80)}x{config.get('screen_height', 40)}")
    print(f"Output Directory: {config.get('output_dir', '.')}")
    print(f"Default Formats: {', '.join(config.get('formats', VALID_FORMATS))}")
    print(f"Capture Tooltips: {config.get('capture_tooltips', True)}")
    if config.get("capture_tooltips", True):
        print(f"Tooltip Selector: {config.get('widget_selector', '*')}")
    print(f"Initial Delay: {config.get('initial_delay', 1.0)}s")
    print(f"Scroll to Top: {config.get('scroll_to_top', True)}")

    steps = config.get("step", [])
    print(f"\nPlanned Steps ({len(steps)} total):")

    capture_counter = 0
    for i, step in enumerate(steps, 1):
        step_type = step.get("type")
        details = []

        if step_type == "press":
            # Show keys (list or string)
            keys = step.get("keys")
            if keys:
                details.append(f"keys={keys}")
            else:
                details.append(f'key="{step.get("key", "")}"')

            pause_between = step.get("pause_between")
            if pause_between is not None and pause_between != 0.2:
                details.append(f"pause_between={pause_between}s")

        elif step_type == "delay":
            details.append(f"{step.get('seconds', 0.5)}s")

        elif step_type == "click":
            details.append(f'label="{step.get("label", "")}"')

        elif step_type == "capture":
            output = step.get("output")
            if not output:
                capture_counter += 1
                output = f"capture_{capture_counter:03d}"

            formats = step.get("formats", config.get("formats", VALID_FORMATS))
            capture_tooltips = step.get("capture_tooltips", config.get("capture_tooltips", True))

            details.append(f'output="{output}"')

            if formats:
                details.append(f"formats=[{', '.join(formats)}]")

            if capture_tooltips:
                selector = step.get("widget_selector", config.get("widget_selector", "*"))
                details.append(f"tooltips={selector}")

        detail_str = ", ".join(details) if details else ""
        print(f"  {i}. {step_type}: {detail_str}")

    # Test dynamic import (without running)
    print("\nValidating module import...")
    try:
        module_path = config.get("module_path")
        if module_path:
            sys.path.insert(0, str(Path(module_path).resolve()))

        app_module = config["app_module"]
        app_class_name = config["app_class"]

        module = __import__(app_module, fromlist=[app_class_name])
        getattr(module, app_class_name)
        print(f"✓ Successfully imported {app_class_name} from {app_module}")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        sys.exit(1)
    except AttributeError as e:
        print(f"✗ Class not found: {e}")
        sys.exit(1)

    print("\n✓ Configuration valid and ready to execute")


async def capture(toml_path: str) -> None:
    """
    Main capture function - loads TOML config and executes sequence.

    Args:
        toml_path: Path to TOML configuration file

    Raises:
        FileNotFoundError: If TOML file doesn't exist
        ValueError: If TOML is invalid or config is malformed
    """
    # Load and parse TOML
    path = Path(toml_path)
    if not path.exists():
        raise FileNotFoundError(f"TOML file not found: {toml_path}")

    logger.info(f"Loading configuration from: {toml_path}")

    try:
        with open(path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse TOML file: {e}") from e

    # Validate configuration upfront (fail fast)
    validate_config(config)

    # Extract configuration (with defaults matching README)
    app_module = config["app_module"]
    app_class_name = config["app_class"]
    screen_width = config.get("screen_width", 80)
    screen_height = config.get("screen_height", 40)
    initial_delay = config.get("initial_delay", 1.0)
    scroll_to_top = config.get("scroll_to_top", True)
    module_path = config.get("module_path")
    steps = config.get("step", [])

    logger.info(f"App: {app_module}.{app_class_name}")
    logger.info(f"Screen size: {screen_width}x{screen_height}")
    logger.info(f"Steps: {len(steps)} action(s)")

    # Add module_path to sys.path if specified
    if module_path:
        sys.path.insert(0, str(Path(module_path).resolve()))
        logger.info(f"Added to module path: {module_path}")
    else:
        # Default: add parent directory for local imports
        sys.path.insert(0, str(Path(__file__).parent.parent))

    # Dynamic import
    try:
        module = __import__(app_module, fromlist=[app_class_name])
        AppClass = getattr(module, app_class_name)
        logger.info(f"Successfully imported {app_class_name} from {app_module}")
    except ImportError as e:
        raise ImportError(f"Failed to import module '{app_module}': {e}") from e
    except AttributeError as e:
        raise AttributeError(f"Module '{app_module}' has no class '{app_class_name}': {e}") from e

    # Instantiate and run app
    app = AppClass()

    async with app.run_test(size=(screen_width, screen_height)) as pilot:
        # Initial delay for rendering
        await pilot.pause(initial_delay)

        # Scroll to top if requested
        if scroll_to_top:
            await pilot.press("home")
            await pilot.pause(0.3)
            logger.info("Scrolled to top")

        # Execute action sequence
        capture_counter = {"count": 0}  # Mutable for auto-sequencing
        for i, step in enumerate(steps):
            logger.info(f"Executing step {i + 1}/{len(steps)}: {step.get('type')}")
            try:
                await execute_action(pilot, step, config, capture_counter)
            except Exception as e:
                logger.error(f"Step {i + 1} failed: {e}")
                raise

    logger.info("Sequence completed successfully")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="textual-capture",
        description="Sequenced screenshot capture for Textual TUI applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    textual-capture demo.toml              # Run with default logging (errors only)
    textual-capture demo.toml --verbose    # Show all actions as they execute
    textual-capture demo.toml --quiet      # Suppress all output except errors
    textual-capture demo.toml --dry-run    # Validate config and show plan

Configuration:
    Create a .toml file defining your app and interaction sequence.
    See https://github.com/eyecantell/textual-capture for examples.
        """,
    )

    parser.add_argument("toml_file", help="Path to TOML configuration file")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output (show all actions)")

    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress all output except errors")

    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Validate config and show execution plan without running"
    )

    args = parser.parse_args()

    # Configure logging based on flags
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s", stream=sys.stderr)

    # Handle dry-run mode
    if args.dry_run:
        try:
            path = Path(args.toml_file)
            if not path.exists():
                logger.error(f"TOML file not found: {args.toml_file}")
                sys.exit(1)

            with open(path, "rb") as f:
                config = tomllib.load(f)

            validate_config(config)
            dry_run(config, args.toml_file)
            sys.exit(0)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    # Run capture
    try:
        asyncio.run(capture(args.toml_file))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
