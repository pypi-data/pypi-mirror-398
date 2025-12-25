"""Centralized logging configuration for ptr_editor.

Provides a logging setup on top of loguru with:

* Theme-aware sinks for Jupyter notebooks (HTML or Rich)
* Console-friendly formatting for standard terminals
* Per-component filtering via :func:`set_logger_level`
* Environment/.env driven bootstrapping helpers
* Handles logging from some used modules like attrs_xml
"""

from __future__ import annotations

import html
import os
import sys
from textwrap import dedent
from typing import Any

from attrs import define
from loguru import logger as log

try:  # Optional dependency when running outside Jupyter
    from IPython.display import HTML, display
except ImportError:  # pragma: no cover - optional dependency
    HTML = None  # type: ignore[assignment]
    display = None  # type: ignore[assignment]

try:  # Optional dependency for rich sink
    from rich.console import Console
    from rich.text import Text
except ImportError:  # pragma: no cover - optional dependency
    Console = None  # type: ignore[assignment]
    Text = None  # type: ignore[assignment]

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore[assignment]

__all__ = ["IN_JUPYTER", "log", "set_logger_level", "setup_logger"]


# Disable logging by default for known modules. They will be re-enabled by setup_logger
for _module_name in ("ptr_editor", "attrs_xml", "ptr_solver", "time_segments"):
    log.disable(_module_name)


def _is_jupyter() -> bool:
    """Check if running in Jupyter/IPython environment."""
    try:
        _ = get_ipython  # type: ignore[name-defined]
    except NameError:
        return False
    else:
        log.info(
            "Detected Jupyter environment. Logging settings will be "
            "adjusted accordingly.",
        )
        return True


IN_JUPYTER = _is_jupyter()


def _normalize_level(level: str) -> str:
    """Return a validated uppercase log level supported by loguru."""

    level_name = level.upper()
    try:
        log.level(level_name)
    except ValueError as exc:  # pragma: no cover - defensive
        msg = f"Invalid log level: '{level}'"
        raise ValueError(msg) from exc
    return level_name


def _jupyter_html_sink(message):
    """
    Custom sink for Jupyter that outputs HTML-formatted log messages.

    This sink is called by loguru when a log message is emitted in Jupyter.
    It formats the message as HTML with color-coding for better readability.
    """
    # Lazy import to avoid dependency when not in Jupyter
    if HTML is None or display is None:
        # Graceful fallback to stderr if IPython not available
        sys.stderr.write(str(message))
        return

    record = message.record

    # Color scheme for different log levels - adjusted for dark/light mode compatibility
    # Using colors with good contrast in both themes
    colors = {
        "TRACE": "#9E9E9E",  # Gray - works in both
        "DEBUG": "#64B5F6",  # Light blue - good contrast in both
        "INFO": "#66BB6A",  # Green - readable in both
        "SUCCESS": "#9CCC65",  # Light green - works in both
        "WARNING": "#FFA726",  # Orange - good visibility in both
        "ERROR": "#EF5350",  # Red - works in both
        "CRITICAL": "#F44336",  # Bright red - works in both
    }

    level = record["level"].name
    color = colors.get(level, "#888888")

    # Safely escape HTML content
    level_str = html.escape(f"{level:<8}")
    location = html.escape(
        f"{record['name']}:{record['function']}:{record['line']}",
    )
    msg = html.escape(record["message"])

    # Format as HTML with theme-aware styles
    # Uses semi-transparent backgrounds and colors that work in both themes
    html_output = dedent(
        f"""
        <div style="font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 13px;
                    margin: 0px 0;
                    padding: 0px 8px;
                    border-left: 3px solid {color};
                    background-color: color-mix(in srgb, {color} 8%, transparent);">
            <span style="color: {color}; font-weight: bold;">{level_str}</span>
            <span style="opacity: 0.5;"> | </span>
            <span style="color: {color}; opacity: 0.8;
                         font-size: 11px;">{location}</span>
            <span style="opacity: 0.5;"> - </span>
            <span style="opacity: 0.9;">{msg}</span>
        </div>
        """,
    )

    display(HTML(html_output))


def _jupyter_rich_sink(message):
    """
    Custom sink for Jupyter that outputs Rich-formatted log messages.

    This sink uses the rich library to provide beautiful, styled console output
    directly in Jupyter notebooks with better theme support and formatting.
    """
    if Console is None or Text is None:
        # Fallback to HTML sink if rich not available
        _jupyter_html_sink(message)
        return

    record = message.record

    # Color scheme for different log levels using rich color names
    level_colors = {
        "TRACE": "bright_black",
        "DEBUG": "cyan",
        "INFO": "green",
        "SUCCESS": "bright_green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red",
    }

    level = record["level"].name
    color = level_colors.get(level, "white")

    # Create a Rich console that outputs to Jupyter
    console = Console(force_jupyter=True, width=120)

    # Build the formatted message using Rich Text
    text = Text()

    # Timestamp
    text.append(f"{record['time']:%Y-%m-%d %H:%M:%S.%f}"[:-3], style="dim green")
    text.append(" | ", style="dim")

    # Level
    text.append(f"{level:<8}", style=f"bold {color}")
    text.append(" | ", style="dim")

    # Location
    location = f"{record['name']}:{record['function']}:{record['line']}"
    text.append(location, style=f"dim {color}")
    text.append(" - ", style="dim")

    # Message
    text.append(record["message"], style=color)

    # Print using rich console
    console.print(text)


@define
class _LoggingState:
    component_levels: dict[str, str]
    enabled_modules: set[str]
    use_rich_sink: bool
    sink_id: int | None


_STATE = _LoggingState(
    component_levels={"": "WARNING"},
    enabled_modules=set(),
    use_rich_sink=False,
    sink_id=None,
)


def _filter_func(record):
    """Filter function to control log levels per component."""
    # Use the logger name to determine the level
    name = record["name"]
    # Find the most specific match
    for component in sorted(_STATE.component_levels, key=len, reverse=True):
        if component and not name.startswith(component):
            continue
        configured_level = _STATE.component_levels.get(
            component,
            _STATE.component_levels[""],
        )
        return record["level"].no >= log.level(configured_level).no

    return record["level"].no >= log.level(_STATE.component_levels[""]).no


def _build_sink() -> tuple[Any, dict[str, Any]]:
    """Return sink target and kwargs based on environment."""

    if IN_JUPYTER:
        sink = _jupyter_rich_sink if _STATE.use_rich_sink else _jupyter_html_sink
        kwargs: dict[str, Any] = {
            "level": "DEBUG",
            "format": "{message}",
            "colorize": False,
            "backtrace": True,
            "diagnose": True,
            "filter": _filter_func,
        }
        return sink, kwargs

    sink = sys.stderr
    kwargs = {
        "level": "TRACE",
        "format": (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        "colorize": True,
        "backtrace": True,
        "diagnose": True,
        "filter": _filter_func,
    }
    return sink, kwargs


def _apply_logger_configuration() -> None:
    """Refresh loguru sinks with the latest configuration."""

    # Remove all existing sinks to avoid duplicates
    log.remove()
    _STATE.sink_id = None

    if not _STATE.enabled_modules:
        return

    # Re-enable all configured modules (important for modules like attrs_xml
    # that disable themselves on import)
    for module in _STATE.enabled_modules:
        log.enable(module)

    sink, kwargs = _build_sink()
    _STATE.sink_id = log.add(sink, **kwargs)


def set_logger_level(level: str, component: str = "") -> None:
    """
    Set the logging level for a specific component or globally.

    Args:
        level: The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR")
        component: The component name (e.g., "ptr_editor.validator").
                   Empty string means global default.

    Example:
        >>> from ptr_editor.core.logging import (
        ...     set_logger_level,
        ... )
        >>> set_logger_level(
        ...     "DEBUG"
        ... )  # Set global level
        >>> set_logger_level(
        ...     "TRACE",
        ...     "ptr_editor.validator",
        ... )  # Component-specific
    """
    normalized = _normalize_level(level)
    _STATE.component_levels[component] = normalized
    _apply_logger_configuration()


def setup_logger(
    level: str = "INFO",
    module: str | list[str] | tuple[str, ...] = "ptr_editor",
    *,
    use_rich: bool | None = None,
) -> None:
    """
    Configure the logger with appropriate handlers for the environment.

    Args:
        level: Default logging level
        module: Module name to enable logging for
        use_rich: If True, use Rich-based sink in Jupyter (requires rich library)

    This function:
    - Removes existing handlers
    - Enables logging for the specified module
    - Adds appropriate handler (HTML/Rich for Jupyter, stderr otherwise)
    - Configures formatting and filtering
    """
    normalized = _normalize_level(level)
    _STATE.component_levels[""] = normalized

    modules = [module] if isinstance(module, str) else list(module)
    if not modules:
        modules = ["ptr_editor"]
    _STATE.enabled_modules.update(modules)

    if use_rich is not None:
        _STATE.use_rich_sink = bool(use_rich)
    elif not IN_JUPYTER:
        _STATE.use_rich_sink = False

    _apply_logger_configuration()


LOG_MODULES = ["ptr_editor", "attrs_xml", "ptr_solver", "time_segments"]


def _load_env_log_level() -> str:
    """Load log level from environment variables or .env file."""
    log_level = os.environ.get("PTR_EDITOR_LOG_LEVEL")
    if log_level is None and load_dotenv is not None:
        load_dotenv()
        log_level = os.environ.get("PTR_EDITOR_LOG_LEVEL")

    # Validate and return the log level
    if log_level:
        return _normalize_level(log_level)

    return "WARNING"


def bootstrap_logging(init_to: str | None = None) -> None:
    """Bootstrap logging for ptr_editor and related modules."""
    # Determine the log level to use
    log_level = init_to if init_to is not None else _load_env_log_level()

    # Setup default configuration
    if IN_JUPYTER:
        setup_logger(log_level, module=LOG_MODULES, use_rich=False)
        log.info(
            "Jupyter detected. Setting up logging for notebook environment...",
        )
        return

    # In non-Jupyter, setup if explicit level provided or env present
    # Otherwise use WARNING as default to ensure modules are at least enabled
    if init_to is not None or os.environ.get("PTR_EDITOR_LOG_LEVEL"):
        setup_logger(log_level, module=LOG_MODULES)
    else:
        # Still need to enable modules even if no explicit logging configuration
        # Use WARNING level by default to avoid spam but keep modules enabled
        setup_logger("WARNING", module=LOG_MODULES)
