"""Factory functions for creating PTR attitudes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ptr_editor.elements.attitude import (
        CaptureAttitude,
        IlluminatedPointAttitude,
        InertialAttitude,
        LimbAttitude,
        SpecularAttitude,
        TerminatorAttitude,
        TrackAttitude,
        VelocityAttitude,
    )
    from ptr_editor.elements.directions import DIRECTIONS
    from ptr_editor.elements.offset import OFFSETS
    from ptr_editor.elements.phase_angle import PHASE_ANGLES
    from ptr_editor.elements.surface import RefSurface
    from ptr_editor.elements.values import Distance


def create_track_attitude(
    target: str | None = None,
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> TrackAttitude:
    """Create a tracking attitude for pointing at solar system objects.

    The spacecraft boresight tracks a specified target object throughout the
    observation. This is the most commonly used attitude type for observations
    of celestial bodies.

    Args:
        target: Solar system object or landmark to track (e.g., 'Jupiter',
            'Ganymede', 'Europa'). If None, uses the value from pointing context.
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        TrackAttitude: A new tracking attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_track_attitude,
        ... )
        >>> attitude = create_track_attitude(
        ...     target="Jupiter",
        ...     phase_angle="power_optimized",
        ... )
    """
    from ptr_editor.elements.attitude import TrackAttitude
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()
    if target is not None:
        ctx = ctx.evolve(target=target)

    kwargs = {}
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        attitude = TrackAttitude(**kwargs)

    return attitude


def create_inertial_attitude(
    target: str | tuple[float, float] | None = None,
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> InertialAttitude:
    """Create an inertial attitude with fixed boresight direction.

    The boresight is aligned with a fixed vector given relative to the inertial
    frame (typically J2000). Useful for star observations and deep space pointing.

    Args:
        target: Fixed inertial direction. Can be:
            - Tuple of (longitude, latitude) in degrees
            - String reference to a direction
            - None to use value from pointing context
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        InertialAttitude: A new inertial attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_inertial_attitude,
        ... )
        >>> # Point to celestial coordinates (lon=120°, lat=-45°)
        >>> attitude = create_inertial_attitude(
        ...     target=(120, -45),
        ... )
    """
    from ptr_editor.elements.attitude import InertialAttitude
    from ptr_editor.elements.directions import LonLatDirection
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()
    if target is not None and isinstance(target, tuple):
        from ptr_editor.elements.directions import LonLatDirection

        ctx = ctx.evolve(lon_lat_direction=LonLatDirection(target[0], target[1]))
    elif target is not None:
        ctx = ctx.evolve(lon_lat_direction=target)

    kwargs = {}
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return InertialAttitude(**kwargs)


def create_limb_attitude(
    surface: RefSurface | str | None = None,
    *,
    target_dir: DIRECTIONS | str | None = None,
    height: Distance | float = 0.0,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> LimbAttitude:
    """Create a limb attitude for horizon/limb observations.

    Points the boresight to a user-selected point relative to the limb of the
    target body. Commonly used for atmospheric observations and altitude-referenced
    observations.

    Args:
        surface: Surface (ellipsoid) for limb calculation. If None, uses
            the value from pointing context.
        target_dir: Direction that defines which point on the limb to observe.
            If None, uses the value from pointing context.
        height: Height above the limb along local normal. Can be:
            - Distance object with value and units
            - Float value (interpreted as km)
            Default: 0.0 (points directly at the limb)
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        LimbAttitude: A new limb attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_limb_attitude,
        ... )
        >>> # Observe Ganymede's limb at 100 km altitude
        >>> attitude = create_limb_attitude(
        ...     surface="Ganymede",
        ...     height=100.0,  # km
        ... )
    """
    from ptr_editor.elements.attitude import LimbAttitude
    from ptr_editor.elements.values import Distance
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()
    if surface is not None:
        ctx = ctx.evolve(target=surface)

    # Convert height to Distance if it's a float
    if isinstance(height, (int, float)):
        height = Distance(height, "km")

    kwargs = {"height": height}
    if target_dir is not None:
        kwargs["target_dir"] = target_dir
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return LimbAttitude(**kwargs)


def create_terminator_attitude(
    surface: RefSurface | str | None = None,
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> TerminatorAttitude:
    """Create a terminator attitude for day-night boundary observations.

    Points the boresight to the point on the terminator that is in the
    target-sun-SC plane and visible from the spacecraft.

    Args:
        surface: Surface (ellipsoid) for terminator calculation. If None, uses
            the value from pointing context.
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        TerminatorAttitude: A new terminator attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_terminator_attitude,
        ... )
        >>> attitude = create_terminator_attitude(
        ...     surface="Ganymede",
        ... )
    """
    from ptr_editor.elements.attitude import TerminatorAttitude
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()
    if surface is not None:
        ctx = ctx.evolve(target=surface)

    kwargs = {}
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return TerminatorAttitude(**kwargs)


def create_velocity_attitude(
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> VelocityAttitude:
    """Create a velocity attitude along spacecraft motion direction.

    Points the boresight along the velocity vector of the spacecraft relative
    to the target body. Useful for ram direction observations.

    Args:
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        VelocityAttitude: A new velocity attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_velocity_attitude,
        ... )
        >>> attitude = create_velocity_attitude()
    """
    from ptr_editor.elements.attitude import VelocityAttitude
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()

    kwargs = {}
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return VelocityAttitude(**kwargs)


def create_specular_attitude(
    surface: RefSurface | str | None = None,
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> SpecularAttitude:
    """Create a specular attitude for mirror reflection observations.

    Points the boresight to the specular point with respect to Earth on an
    elliptical surface. Useful for studying surface reflectance properties.

    Args:
        surface: Elliptical surface for specular point calculation. If None,
            uses the value from pointing context.
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        SpecularAttitude: A new specular attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_specular_attitude,
        ... )
        >>> attitude = create_specular_attitude(
        ...     surface="Ganymede",
        ... )
    """
    from ptr_editor.elements.attitude import SpecularAttitude
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()
    if surface is not None:
        ctx = ctx.evolve(target=surface)

    kwargs = {}
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return SpecularAttitude(**kwargs)


def create_illuminated_point_attitude(
    surface: RefSurface | str | None = None,
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> IlluminatedPointAttitude:
    """Create an illuminated point attitude for partial illumination observations.

    Points the boresight to an illuminated point on the target surface. The
    illuminated point is the mid-point between a point on the terminator and
    the illuminated limb in the target-sun-SC plane.

    Args:
        surface: Surface for illuminated point calculation. If None, uses
            the value from pointing context.
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        IlluminatedPointAttitude: A new illuminated point attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_illuminated_point_attitude,
        ... )
        >>> attitude = create_illuminated_point_attitude(
        ...     surface="Europa",
        ... )
    """
    from ptr_editor.elements.attitude import IlluminatedPointAttitude
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()
    if surface is not None:
        ctx = ctx.evolve(target=surface)

    kwargs = {}
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return IlluminatedPointAttitude(**kwargs)


def create_capture_attitude(
    capture_time: str | pd.Timestamp | None = None,
    *,
    boresight: DIRECTIONS | str | None = None,
    phase_angle: PHASE_ANGLES | str | None = None,
    offset_ref_axis: DIRECTIONS | str | None = None,
    offset_angles: OFFSETS | None = None,
) -> CaptureAttitude:
    """Create a capture attitude for spacecraft capture/insertion maneuvers.

    Specialized attitude mode used during orbital capture or insertion operations.
    Rarely used for science observations.

    Args:
        capture_time: The specific time of the capture maneuver. Can be:
            - ISO format string
            - pd.Timestamp object
            - None (no specific capture time)
        boresight: Vector in SC frame to point at the target. If None, uses
            the value from pointing context.
        phase_angle: Rule that fixes the degree of freedom around the boresight.
            If None, uses the value from pointing context.
        offset_ref_axis: Optional offset reference axis for angular offsets.
        offset_angles: Optional offset angles to apply relative to offset_ref_axis.

    Returns:
        CaptureAttitude: A new capture attitude instance.

    Example:
        >>> from ptr_editor.factory.attitudes import (
        ...     create_capture_attitude,
        ... )
        >>> attitude = create_capture_attitude(
        ...     capture_time="2032-01-01T00:30:00",
        ... )
    """
    from ptr_editor.elements.attitude import CaptureAttitude
    from ptr_editor.services.quick_access import get_pointing_context

    ctx = get_pointing_context()

    kwargs = {}
    if capture_time is not None:
        kwargs["capture_time"] = capture_time
    if boresight is not None:
        kwargs["boresight"] = boresight
    if phase_angle is not None:
        kwargs["phase_angle"] = phase_angle
    if offset_ref_axis is not None:
        kwargs["offset_ref_axis"] = offset_ref_axis
    if offset_angles is not None:
        kwargs["offset_angles"] = offset_angles

    with ctx:
        return CaptureAttitude(**kwargs)
