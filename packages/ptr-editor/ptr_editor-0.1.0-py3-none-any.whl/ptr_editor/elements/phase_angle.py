from typing import Literal

import pandas as pd

from attrs_xml import attr, element, element_define, time_element
from ptr_editor.context import from_defaults
from ptr_editor.core.ptr_element import PtrElement

from .directions import DIRECTIONS
from .values import Angle


@element_define(defname="phaseAngle")
class PhaseAngle(PtrElement):
    """Base class for phase angle definitions.

    The phase angle fixes the degree of freedom around the boresight axis in
    a basic pointing. It determines the rotation (roll) around the pointing
    direction.

    The derived pointing phaseAngle allows modification of the phaseAngle of
    an attitude. This is typically needed if an offset rotation is required
    for the boresight, but the attitude shall be power-optimized.

    To modify the phaseAngle, the attribute ref="phaseAngle" must be specified.

    Attributes:
        ref (str): Phase angle type identifier. Specifies which phase angle
            strategy to use.

    Note:
        This is an abstract base class. Use one of the concrete phase angle
        types: aligned, powerOptimised, or flip.

        When using the derived pointing phaseAngle with offset rotations, the
        boresight defined in the phaseAngle element must be identical to the
        boresight used in the basic pointing of the attitude element.

    See Also:
        AlignedPhaseAngle: Aligns spacecraft axis with inertial axis
        PowerOptimizedPhaseAngle: Optimizes solar panel orientation
        FlipPhaseAngle: Periodic flips at specified times
    """
    ref: str = attr(default="", kw_only=True, repr=False)


@element_define
class AlignedPhaseAngle(PhaseAngle):
    """Aligned phase angle - aligns spacecraft axis with inertial direction.

    This phase angle type constrains the spacecraft orientation by aligning a
    specified spacecraft axis with a specified inertial direction. This is
    useful for maintaining a fixed orientation relative to inertial space.

    The alignment is achieved by rotating around the boresight until the
    spacecraft axis points in the desired inertial direction.

    Attributes:
        ref (Literal["align"]): Phase angle type identifier. Value: "align"
        sc_axis (DIRECTIONS): Spacecraft axis to be aligned (Direction Vector).
            Defined relative to the SC frame.
        inertial_axis (DIRECTIONS): Inertial direction to align with
            (Direction Vector). The SC axis will be aligned with this direction.

    Example:
        >>> from ptr_editor import ObsBlock
        >>> # Create observation with aligned phase angle
        >>> block = ObsBlock(
        ...     attitude='track',
        ...     target='Jupiter',
        ...     phase_angle='aligned',
        ...     start='2032-01-01T00:00:00',
        ...     end='2032-01-01T01:00:00'
        ... )

    Note:
        The alignment constraint is maintained throughout the observation by
        continuously adjusting the roll angle around the boresight.
    """
    ref: Literal["align"] = attr(default="align", kw_only=True, repr=False)
    sc_axis: DIRECTIONS = element(tag="SCAxis", factory=from_defaults("pointing.align_axis"))
    inertial_axis: DIRECTIONS = element(tag="inertialAxis", factory=from_defaults("pointing.inertial_align_axis"))


@element_define
class PowerOptimizedPhaseAngle(PhaseAngle):
    """Power-optimized phase angle - optimizes solar panel orientation.

    This phase angle type automatically adjusts the spacecraft roll angle to
    optimize solar panel illumination, maximizing power generation while
    maintaining the boresight pointing. This is the most commonly used phase
    angle strategy for nominal operations.

    The optimization can be biased towards either the positive or negative
    Y-axis direction of the spacecraft, and can include a fixed angular offset.

    Attributes:
        ref (Literal["powerOptimised"]): Phase angle type. Value: "powerOptimised"
        y_dir (bool): Direction for power optimization. If True, optimizes
            towards positive Y-axis direction; if False, towards negative
            Y-axis direction. Default: True
        angle (Angle): Fixed angular offset to apply to the power-optimized
            angle. Specified as a real value with units (degrees or radians).
            Default: 90 degrees

    Example:
        >>> from ptr_editor import ObsBlock, Angle
        >>> # Use default power optimization
        >>> block = ObsBlock(
        ...     attitude='track',
        ...     target='Ganymede',
        ...     phase_angle='power_optimized',
        ...     start='2032-01-01T00:00:00',
        ...     end='2032-01-01T01:00:00'
        ... )
        
        >>> # Customize power optimization with offset
        >>> block.attitude.phase_angle.angle = Angle(45, 'deg')
        >>> block.attitude.phase_angle.y_dir = False

    Note:
        This is the default phase angle type for most observations. The
        power optimization continuously adjusts the roll angle throughout
        the observation to track the sun position optimally.

        The boresight around which the roll is performed must be identical
        to the boresight used in the basic pointing of the attitude element.
    """
    ref: Literal["powerOptimised"] = attr(
        default="powerOptimised",
        kw_only=True,
        repr=False,
    )
    y_dir: bool = element(default=True, kw_only=True)

    angle: Angle | None = element(
        default=Angle(90.0, "deg"),
    )

    def __str__(self) -> str:
        direction = "+" if self.y_dir else "-"
        return f"{self.angle} [{direction}]"


FLIP_PHASE_ANGLE_TYPES = ["pyPosRot", "pyNegRot", "myPosRot", "myNegRot"]


@element_define
class FlipPhaseAngle(PhaseAngle):
    """Flip phase angle - periodic spacecraft flips at specified times.

    This phase angle type implements periodic 180-degree flips (rotations)
    around the boresight axis. Flips are used to balance thermal loads,
    manage momentum, or redistribute wear on spacecraft components.

    The flip type determines the rotation axis and direction:
    - pyPosRot: Positive rotation around +Y axis
    - pyNegRot: Negative rotation around +Y axis
    - myPosRot: Positive rotation around -Y axis
    - myNegRot: Negative rotation around -Y axis

    Attributes:
        ref (Literal["flip"]): Phase angle type identifier. Value: "flip"
        flip_start_time (pd.Timestamp | None): The time when the first flip
            occurs. If None, flips are not time-constrained. Optional.
        flip_type (Literal["pyPosRot", "pyNegRot", "myPosRot", "myNegRot"]):
            Type of flip rotation to perform. Specifies the rotation axis
            and direction. Default: "pyPosRot"

    Example:
        >>> from ptr_editor import ObsBlock
        >>> import pandas as pd
        >>> # Create observation with flip phase angle
        >>> block = ObsBlock(
        ...     attitude='track',
        ...     target='Jupiter',
        ...     phase_angle='flip',
        ...     start='2032-01-01T00:00:00',
        ...     end='2032-01-01T02:00:00'
        ... )
        >>> # Set flip time and type
        >>> block.attitude.phase_angle.flip_start_time = pd.Timestamp(
        ...     '2032-01-01T01:00:00'
        ... )
        >>> block.attitude.phase_angle.flip_type = 'pyPosRot'

    Note:
        Flips are 180-degree rotations that reverse the spacecraft orientation
        around the boresight while maintaining the pointing direction. The
        flip occurs at the specified time(s) during the observation.
    """
    ref: Literal["flip"] = attr(default="flip", repr=False)
    flip_start_time: pd.Timestamp | None = time_element(default=None)
    flip_type: Literal[*FLIP_PHASE_ANGLE_TYPES] = element(
        default="pyPosRot",
    )


PHASE_ANGLES = AlignedPhaseAngle | PowerOptimizedPhaseAngle | FlipPhaseAngle
