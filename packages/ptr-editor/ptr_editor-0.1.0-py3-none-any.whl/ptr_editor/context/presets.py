"""
Pre-configured defaults for common ptr-editor use cases.

This module provides convenience functions that return pre-configured
DefaultsConfig instances for common scenarios.

Examples:
    >>> # Use JANUS mission defaults
    >>> with janus_defaults():
    ...     obs = ObsBlock()  # Uses JANUS configuration
"""

from __future__ import annotations

from ptr_editor.context.defaults import (
    DefaultsConfig,
    PointingDefaults,
    set_defaults_config,
)

__all__ = [
    "janus_defaults",
    "set_janus_defaults",
]


def janus_defaults() -> DefaultsConfig:
    """
    Create a DefaultsConfig preset for JANUS mission.

    Returns:
        DefaultsConfig configured for JANUS

    Example:
        >>> with janus_defaults():
        ...     obs = ObsBlock()  # Uses JANUS defaults
    """
    return DefaultsConfig(
        pointing=PointingDefaults(
            target="Jupiter",
            boresight="JANUS_boresight",
            designer="JANUS",
        ),
    )


def set_janus_defaults() -> None:
    """
    Set JANUS defaults as the global default configuration.

    This applies JANUS defaults to the current context permanently
    (or until explicitly changed).

    Example:
        >>> set_janus_defaults()
        >>> obs = ObsBlock()  # Uses JANUS defaults
    """
    set_defaults_config(janus_defaults())
