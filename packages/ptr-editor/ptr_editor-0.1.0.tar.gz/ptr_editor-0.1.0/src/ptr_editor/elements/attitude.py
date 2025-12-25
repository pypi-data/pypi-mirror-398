from __future__ import annotations

from functools import singledispatchmethod
from typing import Literal, overload

import pandas as pd

# import pydantic as pd
from attrs_xml import attr, element, element_define, time_element
from attrs_xml.core.decorators_utils import classproperty
from ptr_editor.agm_validator.agm_config_validator import (
    is_known_agm_definition,
    normalize_agm_name,
)
from ptr_editor.context import from_defaults
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.directions import NamedDirection

from .directions import DIRECTIONS, LonLatDirection, NamedDirection, VectorDirection
from .offset import OFFSETS  # noqa: TC001
from .phase_angle import PHASE_ANGLES  # noqa: TC001
from .surface import RefSurface
from .values import Distance


class TargetSurfaceCompatibilityMixin:
    """Mixin providing target/surface compatibility for surface-based attitudes.

    This mixin provides a `target` property that wraps the `surface` attribute,
    allowing attitudes that use surface definitions to be accessed via a more
    intuitive target interface.

    Classes using this mixin must have a `surface` attribute of type RefSurface.
    """

    surface: RefSurface  # Type hint for the required attribute

    @property
    def target(self) -> NamedDirection:
        """Get the target body as a NamedDirection."""
        return NamedDirection(ref=self.surface.ref)

    @target.setter
    def target(self, value: str | NamedDirection) -> None:
        """Set the target body from a string or NamedDirection."""
        if isinstance(value, NamedDirection):
            self.surface.ref = value.ref
        else:
            self.surface.ref = value


@element_define
class BaseAttitude(PtrElement):
    """Base class for all basic pointings (attitudes)."""

    ref: str = attr(default="", kw_only=True)


@element_define
class Attitude(BaseAttitude):
    """Base class for all basic pointings (attitudes).

    For each basic pointing, a boresight is aligned with a target defined relative
    to the inertial frame. The boresight is the vector in the spacecraft frame that
    shall be pointed to the target. The phase angle fixes the degree of freedom
    around the boresight.

    Basic pointings can be combined with offset rotations to fine-tune the attitude.
    For offset rotations, it is often required to power-optimize the attitude after
    the offset is performed.

    Attributes:
        ref (str): The name of the basic pointing type. Must be specified in the
            ref-attribute of the attitude element.
        boresight (DIRECTIONS): Vector defined in SC frame that shall be pointed
            to the target (Direction Vector). Defaults to spacecraft nadir.
        phase_angle (PHASE_ANGLES): Rule that fixes the degree of freedom around
            the boresight. Defaults to power-optimized phase angle.
        offset_ref_axis (DIRECTIONS | None): Optional offset reference axis for
            applying angular offsets to the attitude.
        offset_angles (OFFSETS | None): Optional offset angles to apply relative
            to the offset_ref_axis.

    Note:
        This is an abstract base class. Use one of the concrete basic pointings:
        inertial, track, limb, velocity, specular, terminator, illuminatedPoint,
        or capture.

        For limb, specular, terminator, and illuminatedPoint pointings, the target
        surface is modeled as an ellipsoid. It is possible to use a user-defined
        ellipsoidal shape in the pointing.

    Example:
        >>> # Typically used through ObsBlock
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> block = ObsBlock(
        ...     attitude="track",
        ...     target="Jupiter",
        ... )
        >>> print(
        ...     type(
        ...         block.attitude
        ...     ).__name__
        ... )
        'TrackAttitude'
    """

    boresight: DIRECTIONS = element(
        factory=from_defaults("pointing.boresight"),
        validator=is_known_agm_definition("direction"),
        converter=normalize_agm_name("direction"),
    )
    phase_angle: PHASE_ANGLES = element(factory=from_defaults("pointing.phase_angle"))

    offset_ref_axis: DIRECTIONS | None = element(default=None)
    offset_angles: OFFSETS | None = element(default=None)

    def has_valid_offsets(self) -> bool:
        """Checks if the attitude has any valid offsets defined.

        Returns:
            True if both offset_ref_axis and offset_angles are defined, False otherwise.
        """
        return self.offset_ref_axis is not None and self.offset_angles is not None


@element_define
class TrackAttitude(Attitude):
    """Tracking attitude for pointing at solar system objects or landmarks.

    The spacecraft boresight tracks a specified target object throughout the
    observation. The target can be any solar system body (planet, moon, etc.)
    or a user-defined landmark on a body's surface.

    This is the most commonly used attitude type for observations of celestial
    bodies, as it automatically compensates for the relative motion between the
    spacecraft and target.

    Attributes:
        ref (Literal["track"]): Attitude type identifier. Value: "track"
        target (NamedDirection): Solar system object or landmark to track.
            Must be a valid AGM object definition (e.g., 'Jupiter', 'Ganymede',
            'Europa', 'Io', 'Callisto').
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> # Track Jupiter with default settings
        >>> block = ObsBlock(
        ...     attitude="track",
        ...     target="Jupiter",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )
        >>> print(
        ...     block.attitude.target.ref
        ... )
        'Jupiter'

        >>> # Track Ganymede with power-optimized phase angle
        >>> block2 = ObsBlock(
        ...     attitude="track",
        ...     target="Ganymede",
        ...     phase_angle="power_optimized",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )

    Note:
        The target name must be recognized by the AGM (Attitude Geometry Module)
        configuration. Common targets include: Jupiter, Ganymede, Europa, Io,
        Callisto, Sun, Earth, and other solar system bodies.
    """

    ref: Literal["track"] = attr(default="track", kw_only=True)
    target: NamedDirection = element(
        factory=from_defaults("pointing.target"),
        validator=is_known_agm_definition("object"),
        converter=normalize_agm_name("object"),
    )


@element_define
class InertialAttitude(Attitude):
    """Inertial basic pointing - boresight aligned with fixed inertial vector.

    The boresight is aligned with a fixed vector given relative to the inertial
    frame (typically J2000). The direction remains constant in inertial space,
    not following any moving object.

    This pointing type is commonly used for:
    - Star observations and calibrations
    - Deep space observations
    - Pointing at fixed celestial coordinates
    - Maintaining a specific orientation in inertial space

    Attributes:
        ref (Literal["inertial"]): Basic pointing type identifier. Value: "inertial"
        target (LonLatDirection | VectorDirection): Fixed vector defined relative
            to inertial frame (Direction Vector). Can be specified as
            longitude/latitude or as a 3D vector.
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ...     LonLatDirection,
        ... )
        >>> # Point to fixed celestial coordinates
        >>> block = ObsBlock.new(
        ...     id="STAR_OBS_001",
        ...     attitude="inertial",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T00:10:00",
        ... )
        >>> # Set target direction (lon=120°, lat=-45°)
        >>> block.attitude.target = LonLatDirection(
        ...     120, -45
        ... )

    Note:
        The target direction is expressed in the J2000 inertial reference frame
        unless otherwise specified in the AGM configuration.
    """

    ref: Literal["inertial"] = attr(default="inertial", kw_only=True)
    target: LonLatDirection | VectorDirection = element(
        factory=from_defaults("pointing.lon_lat_direction"),
    )

    @classmethod
    def create_from_spherical(
        cls,
        lon: float,
        lat: float,
        boresight: DIRECTIONS | str | None = None,
        phase_angle: PHASE_ANGLES | str | None = None,
        frame: str = 'EME2000'
    ) -> InertialAttitude:
        """Create an InertialAttitude using spherical coordinates (RA/Dec or Lon/Lat).

        Args:
            lon: Longitude (or Right Ascension) in degrees.
            lat: Latitude (or Declination) in degrees.
            boresight: Boresight direction. If None, uses context default.
            phase_angle: Phase angle setting. If None, uses context default.

        Returns:
            InertialAttitude: Configured inertial attitude with spherical target.

        Example:
            >>> # Create using RA/Dec (spherical coordinates in J2000)
            >>> att = InertialAttitude.create_from_spherical(
            ...     lon=120, lat=-45
            ... )
            >>> # With custom boresight
            >>> att2 = InertialAttitude.create_from_spherical(
            ...     lon=90,
            ...     lat=0,
            ...     boresight="SC_XAxis",
            ... )
        """
        target = LonLatDirection(lon=lon, lat=lat, frame=frame)

        kwargs = {"target": target}
        if boresight is not None:
            kwargs["boresight"] = boresight
        if phase_angle is not None:
            kwargs["phase_angle"] = phase_angle

        return cls(**kwargs)

    @classmethod
    def create_from_cartesian(
        cls,
        x: float,
        y: float,
        z: float,
        boresight: DIRECTIONS | None = None,
        phase_angle: PHASE_ANGLES | None = None,
    ) -> InertialAttitude:
        """Create an InertialAttitude using Cartesian coordinates (x, y, z vector).

        Args:
            x: X component of the inertial vector.
            y: Y component of the inertial vector.
            z: Z component of the inertial vector.
            boresight: Boresight direction. If None, uses context default.
            phase_angle: Phase angle setting. If None, uses context default.

        Returns:
            InertialAttitude: Configured inertial attitude with Cartesian vector target.

        Example:
            >>> # Create using Cartesian coordinates
            >>> att = InertialAttitude.create_from_cartesian(
            ...     x=1.0,
            ...     y=0.5,
            ...     z=0.2,
            ... )
            >>> # With custom boresight
            >>> att2 = InertialAttitude.create_from_cartesian(
            ...     x=1.0,
            ...     y=0.0,
            ...     z=0.0,
            ...     boresight="SC_YAxis",
            ... )
        """
        target = VectorDirection(x=x, y=y, z=z)

        kwargs = {"target": target}
        if boresight is not None:
            kwargs["boresight"] = boresight
        if phase_angle is not None:
            kwargs["phase_angle"] = phase_angle

        return cls(**kwargs)


@element_define
class TerminatorAttitude(Attitude, TargetSurfaceCompatibilityMixin):
    """Terminator basic pointing - boresight pointed at the day-night boundary.

    Points the boresight to the point on the terminator that is in the
    target-sun-SC plane and visible from the SC. The terminator is the boundary
    between the day and night sides of the target body.

    For terminator pointing, the surface of the target is modeled as an ellipsoid.
    It is possible to use a user-defined ellipsoidal shape in the pointing.

    Attributes:
        ref (Literal["terminator"]): Basic pointing type. Value: "terminator"
        surface (RefSurface): Surface (ellipsoid) for which the terminator is
            calculated. Defaults to the context target body.
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> # Observe the terminator on Ganymede
        >>> block = ObsBlock(
        ...     attitude="terminator",
        ...     target="Ganymede",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )

    Note:
        The selected terminator point must be in the target-sun-SC plane and
        visible from the spacecraft.
    """

    ref: Literal["terminator"] = attr(default="terminator", kw_only=True)
    surface: RefSurface = element(factory=from_defaults("pointing.target"))


@element_define
class LimbAttitude(Attitude, TargetSurfaceCompatibilityMixin):
    """Limb basic pointing - boresight pointed at the target's limb.

    Points the boresight to a user-selected point relative to the limb of the
    target body. The limb is the apparent edge/horizon of the body as seen
    from the spacecraft.

    For limb pointing, the surface of the target is modeled as an ellipsoid.
    It is possible to use a user-defined ellipsoidal shape in the pointing.

    This pointing is commonly used for:
    - Atmospheric observations (e.g., stellar occultations)
    - Horizon/limb imaging
    - Altitude-referenced observations
    - Tangent height observations

    Attributes:
        ref (Literal["limb"]): Basic pointing type identifier. Value: "limb"
        target_dir (DIRECTIONS): The selected point on the limb lies in the
            half-plane defined by the target-to-SC direction and the positive
            direction towards target_dir (Direction Vector). This determines
            which side of the limb to observe.
        height (Distance): The boresight is pointed towards the point that lies
            the specified height along the local normal of the selected point
            on the limb. Positive values point outward from the surface.
            Default: 0 km (points directly at the limb).
        surface (RefSurface): Surface (ellipsoid) for which the limb is
            calculated. Defaults to the context target body.
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ...     Distance,
        ... )
        >>> # Observe Ganymede's limb at 100 km above surface
        >>> block = ObsBlock.new(
        ...     id="LIMB_OBS_001",
        ...     attitude="limb",
        ...     target="Ganymede",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )
        >>> block.attitude.height = Distance(
        ...     100, "km"
        ... )

    Note:
        The target_dir parameter determines which point on the limb circle is
        selected, as the limb forms a circle as seen from the spacecraft.
    """

    ref: Literal["limb"] = attr(default="limb", kw_only=True)
    target_dir: DIRECTIONS = element(
        factory=from_defaults("pointing.limb_target_dir"),
    )
    #: Height above the limb along the local normal. Positive values point outward from the surface.
    #: Although is not well documented, it is optional.
    height: Distance | None = element(default=Distance(0, "km"))
    surface: RefSurface = element(factory=from_defaults("pointing.target"))


@element_define
class CaptureAttitude(BaseAttitude):
    """Capture attitude for spacecraft capture/insertion maneuvers.

    It is required if an attitude that is not exactly known at MTP
    needs to be flown again at a later time within the same MTP. The
    capture pointing allows to implement a fixed attitude that was
    implemented in the same PTR at an earlier time.

    Attributes:
        ref (Literal["capture"]): Attitude type identifier. Value: "capture"
        capture_time (pd.Timestamp | None): The specific time of the capture
            maneuver. Optional.
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> import pandas as pd
        >>> # Define capture attitude at specific time
        >>> block = ObsBlock(
        ...     attitude="capture",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )
        >>> block.attitude.capture_time = pd.Timestamp(
        ...     "2032-01-01T00:30:00"
        ... )

    Note:
        This attitude type is typically defined by mission operations rather
        than science planning teams.
    """

    ref: Literal["capture"] = attr(default="capture", kw_only=True)
    capture_time: pd.Timestamp | None = time_element(default=None)
    capture_block_ref: str | None = element(default=None)

    @classproperty
    def element_type(cls) -> str:
        """Return the attitude type identifier."""
        return "capture"


@element_define
class VelocityAttitude(Attitude):
    """Velocity basic pointing - boresight along spacecraft velocity vector.

    Points the boresight along the velocity vector of the SC relative to the
    target body. The velocity vector points in the direction of motion.

    This pointing is useful for:
    - Ram direction observations (particles/atmosphere in flight direction)
    - Wake observations (opposite to flight direction, with offsets)
    - Velocity-aligned experiments

    No target-specific parameters are required; the velocity vector is
    automatically computed from the spacecraft ephemeris relative to the
    target body.

    Attributes:
        ref (Literal["velocity"]): Basic pointing type. Value: "velocity"
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> # Point along velocity vector
        >>> block = ObsBlock(
        ...     attitude="velocity",
        ...     target="Ganymede",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )

    Note:
        The velocity vector is computed relative to the target body specified
        in the observation context or parent ObsBlock.
    """

    ref: Literal["velocity"] = attr(default="velocity", kw_only=True)


@element_define
class SpecularAttitude(Attitude, TargetSurfaceCompatibilityMixin):
    """Specular basic pointing - boresight pointed at specular reflection point.

    Points the boresight to the specular point with respect to Earth on an
    elliptical surface defined relative to the centre of the target. The
    specular point is where light from Earth would reflect off the surface
    toward the spacecraft, like a mirror.

    For specular pointing, the surface of the target is modeled as an ellipsoid.
    It is possible to use a user-defined ellipsoidal shape in the pointing.

    This pointing is useful for studying surface reflectance properties and
    photometric behavior at specific viewing geometries.

    Attributes:
        ref (Literal["specular"]): Basic pointing type. Value: "specular"
        surface (RefSurface): Elliptical surface for which the specular point
            is calculated. Defaults to the context target body.
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> # Observe specular point on Ganymede
        >>> block = ObsBlock(
        ...     attitude="specular",
        ...     target="Ganymede",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )

    Note:
        The specular point calculation requires knowledge of the Earth (or
        illumination source) position, computed from SPICE kernels.
    """

    ref: Literal["specular"] = attr(default="specular", kw_only=True)
    surface: RefSurface = element(factory=from_defaults("pointing.target"))


@element_define
class IlluminatedPointAttitude(Attitude, TargetSurfaceCompatibilityMixin):
    """IlluminatedPoint basic pointing - boresight at partially illuminated region.

    Points the boresight to an illuminated point of the target surface. The
    illuminated point is the mid-point (in terms of angle as seen from the SC)
    between a point on the terminator and the illuminated limb. The point on the
    terminator and limb are chosen in the target-sun-SC plane.

    For illuminatedPoint pointing, the surface of the target is modeled as an
    ellipsoid. It is possible to use a user-defined ellipsoidal shape in the
    pointing.

    This pointing provides an intermediate illumination condition between the
    terminator and the fully illuminated disk, useful for observations at
    intermediate phase angles.

    Attributes:
        ref (Literal["illuminatedPoint"]): Basic pointing type identifier.
            Value: "illuminatedPoint"
        surface (RefSurface): Surface for which the illuminated point is
            calculated. Defaults to the context target body.
        boresight (DIRECTIONS): Inherited from Attitude.
        phase_angle (PHASE_ANGLES): Inherited from Attitude.

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ... )
        >>> # Observe illuminated point on Europa
        >>> block = ObsBlock(
        ...     attitude="illuminated_point",
        ...     target="Europa",
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )

    Note:
        The illuminated point lies in the target-sun-SC plane and represents
        a geometrically well-defined intermediate illumination condition.
    """

    ref: Literal["illuminatedPoint"] = attr(default="illuminatedPoint", kw_only=True)
    surface: RefSurface = element(factory=from_defaults("pointing.target"))


ATTITUDES = (
    LimbAttitude
    | TrackAttitude
    | TerminatorAttitude
    | InertialAttitude
    | CaptureAttitude
    | VelocityAttitude
    | SpecularAttitude
    | IlluminatedPointAttitude
)
