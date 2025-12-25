"""
Default configuration system for ptr-editor.

This module provides immutable, context-managed default values for creating
PTR elements. Defaults are thread-safe using contextvars and can be temporarily
overridden using context managers.

Examples:
    >>> # Using defaults with context management
    >>> with PointingDefaults(target="Mars"):
    ...     obs = ObservationRequest()  # Uses Mars as target
    >>> # Automatically restored after context
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

from attrs import NOTHING, define, evolve, field
from loguru import logger as log

from ptr_editor.factory.blocks import NothingType




if TYPE_CHECKING:
    from types import TracebackType

    from ptr_editor.elements.attitude import Attitude
    from ptr_editor.elements.directions import Direction
    from ptr_editor.elements.phase_angle import PhaseAngle


# Global context variable for defaults
_defaults: ContextVar[DefaultsConfig | None] = ContextVar("_defaults", default=None)


__all__ = [
    "DefaultsConfig",
    "PointingDefaults",
    "get_defaults_config",
    "set_defaults_config",
    "from_defaults",
]


# ============================================================================
# Default Value Factories
# ============================================================================


def _make_default_att() -> Attitude:
    from ptr_editor.elements.attitude import TrackAttitude

    return TrackAttitude()


def _make_default_phase_angle() -> PhaseAngle:
    from ptr_editor.elements.phase_angle import PowerOptimizedPhaseAngle

    return PowerOptimizedPhaseAngle()


def _make_default_limb_target_dir() -> Direction:
    from ptr_editor.elements.directions import NamedDirection, RotatedDirection
    from ptr_editor.elements.values import Angle
    from ptr_editor.services.quick_access import get_agm_configuration

    agm_config = get_agm_configuration()
    ptctx = get_defaults_config().pointing
    target = ptctx.target

    n_pole = agm_config.north_pole_direction(target)
    rot_axis = agm_config.sc_target_direction(target)

    return RotatedDirection(
        axis=NamedDirection(ref=n_pole),
        rotation_axis=NamedDirection(ref=rot_axis),
        rotation_angle=Angle(value=0.0, units="deg"),
    )


def _make_default_lonlat_direction() -> Direction:
    from ptr_editor.elements.directions import LonLatDirection
    from ptr_editor.elements.values import Angle

    return LonLatDirection(
        lon=Angle(value=0.0, units="deg"),
        lat=Angle(value=0.0, units="deg"),
    )


def _make_default_inertial_align_axis() -> Direction:
    from ptr_editor.elements.directions import RotatedDirection
    from ptr_editor.services.quick_access import get_agm_configuration

    agm_config = get_agm_configuration()
    ptctx = get_defaults_config().pointing
    target = ptctx.target

    n_pole = agm_config.north_pole_direction(target)
    sc_to_target = agm_config.sc_target_direction(target)

    return RotatedDirection(
        axis=n_pole,
        rotation_axis=sc_to_target,
        rotation_angle="0 deg",
    )


# ============================================================================
# Default Configuration Classes
# ============================================================================


@define(frozen=True, kw_only=True)
class PointingDefaults:
    """
    Immutable configuration for pointing defaults.

    This is pure configuration - no behavior, just data.
    Use as a context manager to temporarily override defaults.
    
    When used in a nested context, only explicitly specified fields
    override the parent; unspecified fields (NOTHING) are inherited.

    Attributes:
        target: Default target body name
        boresight: Default boresight reference
        align_axis: Default alignment axis reference
        designer: Default designer/instrument name
        attitude: Factory for creating default attitude
        phase_angle: Factory for creating default phase angle
        limb_target_dir: Factory for creating default limb target direction
        lon_lat_direction: Factory for creating default lon/lat direction
        inertial_align_axis: Factory for creating default inertial align axis

    Example:
        >>> defaults = PointingDefaults(target="Mars", designer="JANUS")
        >>> with defaults:
        ...     # All objects created here use Mars as default target
        ...     obs = ObservationRequest()
    """

    target: str | NothingType = field(factory=lambda: NOTHING)
    boresight: str | NothingType = field(factory=lambda: NOTHING)
    align_axis: str | NothingType = field(factory=lambda: NOTHING)
    designer: str | None | NothingType = field(factory=lambda: NOTHING)

    # Lazy-evaluated defaults (callables that return instances)
    attitude: Callable[[], Attitude] | None | NothingType = field(
        factory=lambda: NOTHING,
    )
    phase_angle: Callable[[], PhaseAngle] | None | NothingType = field(
        factory=lambda: NOTHING,
    )
    limb_target_dir: Callable[[], Direction] | None | NothingType = field(
        factory=lambda: NOTHING,
    )
    lon_lat_direction: Callable[[], Direction] | None | NothingType = field(
        factory=lambda: NOTHING,
    )
    inertial_align_axis: Callable[[], Direction] | None | NothingType = field(
        factory=lambda: NOTHING,
    )
    _token: Token[DefaultsConfig | None] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    
    @staticmethod
    def get_root_defaults() -> PointingDefaults:
        """Get root-level defaults with actual values (not NOTHING).
        
        This is used when initializing the system or when all values
        are NOTHING (e.g., when parent context doesn't exist).
        """
        return PointingDefaults(
            target="Jupiter",
            boresight="JUICE_SPACECRAFT_NADIR",
            align_axis="SC_YAxis",
            designer=None,
            attitude=_make_default_att,
            phase_angle=_make_default_phase_angle,
            limb_target_dir=_make_default_limb_target_dir,
            lon_lat_direction=_make_default_lonlat_direction,
            inertial_align_axis=_make_default_inertial_align_axis,
        )

    def with_target(self, target: str) -> PointingDefaults:
        """Create new config with different target."""
        return evolve(self, target=target)

    def with_designer(self, designer: str) -> PointingDefaults:
        """Create new config with different designer."""
        return evolve(self, designer=designer)

    def evolve(self, **kwargs) -> PointingDefaults:
        """Create new config with modified fields.
        
        Filters out NOTHING values to avoid overwriting existing defaults
        with the NOTHING sentinel.
        
        Args:
            **kwargs: Fields to update in the new config.
            
        Returns:
            New PointingDefaults instance with updated fields.
        """
        # Filter out NOTHING values - they should not override existing defaults
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not NOTHING}
        new_instance = evolve(self, **filtered_kwargs)
        # Ensure the new instance has no token (avoid reusing tokens in nested contexts)
        object.__setattr__(new_instance, "_token", None)
        return new_instance

    def __enter__(self) -> PointingDefaults:
        """Apply these pointing defaults temporarily.
        
        Merges with parent context by inheriting unspecified values.
        Only fields that were explicitly set (not NOTHING) will override
        parent values; others inherit from parent context.
        """
        parent = get_defaults_config()
        parent_pointing = parent.pointing
        
        # If parent has NOTHING values, use root defaults as base
        if parent_pointing.target is NOTHING:
            parent_pointing = PointingDefaults.get_root_defaults()
        
        # Build dict of only the fields that were explicitly set (not NOTHING)
        override_values = {}
        for field_name in [
            "target",
            "boresight",
            "align_axis",
            "designer",
            "attitude",
            "phase_angle",
            "limb_target_dir",
            "lon_lat_direction",
            "inertial_align_axis",
        ]:
            value = getattr(self, field_name)
            if value is not NOTHING:
                override_values[field_name] = value
        
        # Merge with parent using the evolve method
        merged_pointing = parent_pointing.evolve(**override_values)
        
        # Create new config with merged pointing defaults
        new_config = evolve(parent, pointing=merged_pointing)
        # Clear the token on the new config to avoid reusing parent's token
        object.__setattr__(new_config, "_token", None)
        token = _defaults.set(new_config)
        # Store token for restoration
        log.debug(
            f"PointingDefaults.__enter__: id={id(self)}, "
            f"token={id(token)}, overrides={override_values}",
        )
        object.__setattr__(self, "_token", token)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Restore previous defaults."""
        log.debug(f"PointingDefaults.__exit__: id={id(self)}, token={id(self._token) if self._token else None}, target={self.target}, designer={self.designer}")
        if self._token:
            _defaults.reset(self._token)


@define(frozen=True)
class DefaultsConfig:
    """
    Top-level immutable configuration for all defaults.

    This is the complete default configuration for the application.
    Use as a context manager to temporarily override all defaults.

    Attributes:
        pointing: Pointing-specific defaults
        enabled: Whether default factories should provide values (default: True)

    Example:
        >>> config = DefaultsConfig(pointing=PointingDefaults(target="Mars"))
        >>> with config:
        ...     # All objects created here use this config
        ...     obs = ObservationRequest()
    """

    pointing: PointingDefaults = field(factory=PointingDefaults.get_root_defaults)
    enabled: bool = field(default=True, kw_only=True)
    _token: Token[DefaultsConfig | None] | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def with_pointing(self, **kwargs) -> DefaultsConfig:
        """Create new config with modified pointing defaults."""
        new_pointing = evolve(self.pointing, **kwargs)
        # Clear token on the new pointing to avoid token reuse
        object.__setattr__(new_pointing, "_token", None)
        new_config = evolve(self, pointing=new_pointing)
        # Clear token on the new config to avoid token reuse
        object.__setattr__(new_config, "_token", None)
        return new_config

    def __enter__(self) -> DefaultsConfig:
        """Apply these defaults temporarily."""
        token = _defaults.set(self)
        # Store token for restoration
        object.__setattr__(self, "_token", token)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Restore previous defaults."""
        if self._token:
            _defaults.reset(self._token)

    @contextmanager
    def disabled(self):
        """Context manager to temporarily disable default factories.

        When disabled, factories created with from_defaults() will not provide
        default values, allowing attrs to use its own default handling.

        This is useful during XML loading where defaults should come from the
        XML content, not from the context.

        Example:
            >>> config = get_defaults_config()
            >>> with config.disabled():
            ...     # Default factories won't provide values here
            ...     obj = load_from_xml(xml_content)
        """
        disabled_config = evolve(self, enabled=False)
        token = _defaults.set(disabled_config)
        try:
            yield disabled_config
        finally:
            _defaults.reset(token)


# ============================================================================
# Context Access Functions
# ============================================================================


def get_defaults_config() -> DefaultsConfig:
    """
    Get the current defaults configuration.

    This is context-aware and thread-safe using contextvars.

    Returns:
        The current defaults configuration for this context

    Example:
        >>> config = get_defaults_config()
        >>> print(config.pointing.target)  # "Jupiter" (default)
    """
    config = _defaults.get()
    if config is None:
        config = DefaultsConfig()
        _defaults.set(config)
    return config


def set_defaults_config(config: DefaultsConfig) -> None:
    """
    Set the defaults configuration (affects current context only).

    Args:
        config: The defaults configuration to set

    Example:
        >>> config = DefaultsConfig(pointing=PointingDefaults(target="Mars"))
        >>> set_defaults_config(config)
    """
    _defaults.set(config)


# ============================================================================
# Field Factory
# ============================================================================


def from_defaults(attribute_path: str):
    """
    Create a factory that retrieves defaults from current context.

    This is for attrs fields that should get their default values
    from the current DefaultsConfig.

    Args:
        attribute_path: Dot-separated path like "pointing.target"

    Returns:
        A factory function suitable for attrs.field(factory=...)

    Example:
        >>> from attrs import define, field
        >>> @define
        ... class ObsRequest:
        ...     target: str = field(factory=from_defaults("pointing.target"))
        ...
        >>> # Uses default from context
        >>> with PointingDefaults(target="Mars"):
        ...     obs = ObsRequest()  # obs.target == "Mars"
    """

    def factory():
        config = get_defaults_config()
        
        # If defaults are disabled, return None to indicate no default
        if not config.enabled:
            # from attrs import NOTHING
            return None
        
        parts = attribute_path.split(".")
        value = config
        for part in parts:
            value = getattr(value, part)

        # If it's a callable factory, call it
        if callable(value):
            return value()

        return value

    factory.__name__ = f"from_defaults({attribute_path!r})"
    return factory
