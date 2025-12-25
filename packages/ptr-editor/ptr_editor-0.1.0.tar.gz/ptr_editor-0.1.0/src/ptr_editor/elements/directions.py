from __future__ import annotations

from typing import Literal

import numpy as np
from loguru import logger as log

from attrs_xml import attr, element, element_define
from ptr_editor.agm_validator.agm_config_validator import (
    is_known_agm_definition,
    normalize_agm_name,
)
from ptr_editor.core.ptr_element import PtrElement

from .values import Angle


@element_define
class Direction(PtrElement):
    """Base class for all direction vector representations.

    Direction vectors are used throughout PTR to specify pointing directions,
    reference axes, and geometric relationships. They can be defined in either
    the spacecraft (SC) frame or in a frame defined relative to the inertial
    frame (typically EME2000 or J2000).

    Supported direction vector representations:
    - Coordinates: Fixed direction from cartesian or spherical coordinates
    - Origin and Target: Direction from one state vector to another
    - Reference: Named reference to predefined or previously defined directions
    - Rotated: Direction obtained by rotating another direction vector

    Attributes:
        name (str | None): Optional name for the direction, used for storing
            in config files or referencing later.

    Note:
        Direction vectors defined from coordinates can use either SC frame or
        inertial frames (EME2000, CG). Directions from state vectors (origin
        and target) are always defined relative to inertial frame.
    """

    name: str | None = attr(
        default=None,
        kw_only=True,
    )  # direction can be named, e.g. to be stored in config files.

    @classmethod
    def from_string(
        cls,
        value: str | DIRECTIONS | None,
    ) -> DIRECTIONS | None:
        if value is None:
            return None

        if isinstance(value, Direction):
            return value

        if isinstance(value, str):
            return NamedDirection(ref=value)

        msg = f"Cannot convert {value} to Direction"
        log.exception(msg)
        raise ValueError(msg)


@element_define
class NamedDirection(Direction):
    """Reference to a known direction vector by name.

    This representation allows direction vectors to be defined by referencing
    direction vectors that were previously defined and assigned a name, or
    predefined direction vectors available in the AGM configuration.

    Common predefined directions include:
    - SC_Xaxis, SC_Yaxis, SC_Zaxis: Spacecraft frame axes
    - Sun, Earth, Jupiter, etc.: Celestial body directions
    - Other AGM-configured directions

    Attributes:
        ref (str): Name of the direction vector to reference. Must be either
            a predefined AGM direction or a previously defined named direction.

    Example:
        >>> # Reference a predefined spacecraft axis
        >>> dir_x = NamedDirection(
        ...     ref="SC_Xaxis"
        ... )
        >>>
        >>> # Reference a celestial body
        >>> dir_sun = (
        ...     NamedDirection(
        ...         ref="Sun"
        ...     )
        ... )
        >>>
        >>> # In XML form
        >>> # <dirVector ref="SC_Xaxis" />

    Note:
        The referenced direction must exist in the AGM configuration or have
        been previously defined in the PTR/PDFM document.
    """

    ref: str = attr(
        validator=is_known_agm_definition(["direction", "object"]),
        converter=normalize_agm_name(["direction", "object"]),
    )

    def __repr__(self) -> str:
        if self.name:
            return f"NamedDirection(name={self.name}, ref={self.ref})"
        return f"NamedDirection(ref={self.ref})"

    def __str__(self) -> str:
        return self.ref
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, str):
            return self.ref.lower() == value.lower()
        return super().__eq__(value)


@element_define
class VectorDirection(Direction):
    """Fixed direction vector defined by Cartesian coordinates.

    A fixed direction vector can be defined directly from Cartesian coordinates
    (x, y, z) relative to either the SC frame or an inertial frame. The actual
    direction corresponds to the normalization of the vector, so the components
    must not all be zero.

    Attributes:
        x (float): X component of the direction vector.
        y (float): Y component of the direction vector.
        z (float): Z component of the direction vector.
        frame (str): Reference frame for the direction vector. Possible values
            are "SC" (spacecraft), "EME2000" (inertial), or "CG" (comet-centered).
            Default: "EME2000"

    Example:
        >>> # Fixed direction along SC X-axis
        >>> dir_sc_x = (
        ...     VectorDirection(
        ...         x=1.0,
        ...         y=0.0,
        ...         z=0.0,
        ...         frame="SC",
        ...     )
        ... )
        >>>
        >>> # Direction in inertial frame
        >>> dir_inertial = VectorDirection(
        ...     x=0.0,
        ...     y=1.0,
        ...     z=0.0,
        ...     frame="EME2000",
        ... )
        >>>
        >>> # Convert to numpy array
        >>> vec_array = dir_sc_x.as_numpy()
        >>>
        >>> # In XML form:
        >>> # <dirVector frame="SC">
        >>> #   <x> 1. </x>
        >>> #   <y> 0. </y>
        >>> #   <z> 0. </z>
        >>> # </dirVector>

    Note:
        The vector components must not all be zero. The direction is the
        normalized vector, so [1,0,0] and [2,0,0] represent the same direction.
    """

    x: float = element(converter=float)
    y: float = element(converter=float)
    z: float = element(converter=float)
    frame: str = attr(
        default="EME2000",
        validator=is_known_agm_definition("frame"),
    )

    def as_numpy(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def __str__(self) -> str:
        return f"""[{self.x}, {self.y}, {self.z}]@{self.frame}"""


@element_define
class LonLatDirection(Direction):
    """Fixed direction vector defined by spherical coordinates.

    A fixed direction vector can be defined from spherical coordinates
    (longitude, latitude) relative to either the SC frame or an inertial frame.

    The Cartesian components of the vector are computed as:
        x = cos(lat) * cos(lon)
        y = cos(lat) * sin(lon)
        z = sin(lat)

    Attributes:
        lon (Angle): Longitude angle with units specified (e.g., degrees, radians).
        lat (Angle): Latitude angle with units specified (e.g., degrees, radians).
        frame (str): Reference frame for the direction vector. Possible values
            are "SC" (spacecraft), "EME2000" (inertial), or "CG" (comet-centered).
            Default: "EME2000"

    Example:
        >>> from ptr_editor import (
        ...     Angle,
        ... )
        >>> # Direction at 90° longitude, 0° latitude in inertial frame
        >>> dir_sph = LonLatDirection(
        ...     lon=Angle(
        ...         90, "deg"
        ...     ),
        ...     lat=Angle(
        ...         0, "deg"
        ...     ),
        ...     frame="EME2000",
        ... )
        >>>
        >>> # In XML form:
        >>> # <dirVector frame="EME2000">
        >>> #   <lon units="deg"> 90. </lon>
        >>> #   <lat units="deg"> 0. </lat>
        >>> # </dirVector>

    Note:
        The units attribute must be provided for both lon and lat, and must
        contain a dimension of an angle (see angle units table in PTR spec).
    """

    lon: Angle = element()
    lat: Angle = element()
    frame: str = attr(default="EME2000")  # override the default

    def __str__(self) -> str:
        return f"""[{self.lon}, {self.lat}]@{self.frame}"""


@element_define
class OriginTargetDirection(Direction):
    """Direction vector from origin to target state vectors.

    This representation defines a direction vector from two state vectors
    (origin and target). Because state vectors are always defined relative
    to the inertial frame, the resulting direction vector is always defined
    relative to the inertial frame.

    The direction points from the origin body/object toward the target
    body/object at each instant in time.

    Attributes:
        origin (NamedDirection): Reference to the origin object (starting point).
        target (NamedDirection): Reference to the target object (end point).

    Example:
        >>> # Direction from Sun to Earth
        >>> sun_to_earth = OriginTargetDirection(
        ...     origin=NamedDirection(
        ...         ref="Sun"
        ...     ),
        ...     target=NamedDirection(
        ...         ref="Earth"
        ...     ),
        ... )
        >>>
        >>> # In XML form:
        >>> # <dirVector>
        >>> #   <origin ref="Sun" />
        >>> #   <target ref="Earth" />
        >>> # </dirVector>

    Note:
        The origin and target must be valid AGM object references (celestial
        bodies, spacecraft, or other defined objects with state vectors).
    """

    # operator: Literal["derivative"] | None = attr(default=None, kw_only=True)
    origin: NamedDirection = element()
    target: NamedDirection = element()

    def __str__(self) -> str:
        return f"{self.origin} ⇾ {self.target}"


SIMPLE_DIRECTIONS = (
    NamedDirection | VectorDirection | LonLatDirection | OriginTargetDirection
)


@element_define
class RotatedDirection(Direction):
    """Direction vector obtained by rotation of another direction.

    This representation defines a direction vector by right-handed rotation
    of a direction vector (axis) around another direction vector (rotationAxis)
    by a specified angle (rotationAngle).

    Both the axis and rotationAxis must be defined in the same reference frame
    (either both in SC frame or both in inertial frame).

    Attributes:
        ref (Literal["rotate"]): Type identifier, always "rotate".
        axis (SIMPLE_DIRECTIONS): The direction vector to be rotated.
        rotation_axis (SIMPLE_DIRECTIONS): The axis around which to rotate.
        rotation_angle (Angle): The rotation angle (right-handed). Default: 0°

    Example:
        >>> from ptr_editor import (
        ...     Angle,
        ... )
        >>> # Rotate SC X-axis 90° around SC Z-axis (results in SC Y-axis)
        >>> rotated_dir = RotatedDirection(
        ...     axis=NamedDirection(
        ...         ref="SC_Xaxis"
        ...     ),
        ...     rotation_axis=NamedDirection(
        ...         ref="SC_Zaxis"
        ...     ),
        ...     rotation_angle=Angle(
        ...         90, "deg"
        ...     ),
        ... )
        >>>
        >>> # In XML form:
        >>> # <dirVector ref="rotate">
        >>> #   <axis ref="SC_Xaxis" />
        >>> #   <rotationAxis ref="SC_Zaxis" />
        >>> #   <rotationAngle units="deg"> 90. </rotationAngle>
        >>> # </dirVector>

    Note:
        The rotation follows the right-hand rule: if the thumb points along
        the rotation axis, fingers curl in the direction of positive rotation.
    """

    ref: Literal["rotate"] = attr(default="rotate", kw_only=True)
    axis: SIMPLE_DIRECTIONS = element()
    rotation_axis: SIMPLE_DIRECTIONS = element()
    rotation_angle: Angle = element(default=Angle(value=0.0, units="deg"))

    def __str__(self) -> str:
        return (
            f"Rot({self.axis}, around {self.rotation_axis}, by {self.rotation_angle})"
        )


@element_define
class DerivedDirection(Direction):
    """Base class for direction vectors derived from other directions."""
    operator: str = attr()


@element_define
class VelocityDirection(Direction):
    """Direction vector origin to target.

    This is mostly used in AGM config.
    """

    operator: Literal["derivative"] = attr(default="derivative", kw_only=True)
    origin: NamedDirection = element()
    target: NamedDirection = element()

    def __str__(self) -> str:
        return f"Derivative ({self.origin} ⇾ {self.target})"


@element_define
class CrossProductDirection(DerivedDirection):
    """
    Direction vector obtained by the cross product of two direction vectors.

    This is mostly used in AGM config.
    """
    operator: Literal["cross"] = attr(kw_only=True, default="cross")
    dir_vectors: list[SIMPLE_DIRECTIONS] = element(tag="dirVector")

    @property
    def dir1(self) -> NamedDirection:
        if len(self.dir_vectors) != 2:
            msg = "CrossProductDirection requires exactly two direction vectors."
            raise ValueError(msg)
        return self.dir_vectors[0]

    @property
    def dir2(self) -> NamedDirection:
        if len(self.dir_vectors) != 2:
            msg = "CrossProductDirection requires exactly two direction vectors."
            raise ValueError(msg)
        return self.dir_vectors[1]

    def __str__(self) -> str:
        return f"{self.dir1} ⨯ {self.dir2}"


@element_define
class ProjectedVectorToPlaneDirection(DerivedDirection):
    """Direction vector projected onto a plane.

    This is mostly used in AGM config.
    """
    operator: Literal["proj_vector_to_plane"] = attr(
        kw_only=True,
        default="proj_vector_to_plane",
    )
    dir_vector: NamedDirection = element()
    normal_vector: NamedDirection = element()

    def __str__(self) -> str:
        return f"Proj(v={self.dir_vector}, normal={self.normal_vector})" 


DERIVED_DIRECTIONS = (
    VelocityDirection
    | RotatedDirection
    | CrossProductDirection
    | ProjectedVectorToPlaneDirection
    | OriginTargetDirection
)

DIRECTIONS = SIMPLE_DIRECTIONS | DERIVED_DIRECTIONS


AGM_CONFIG_DIRECTIONS = (
    OriginTargetDirection
    | VectorDirection
    | LonLatDirection
    | RotatedDirection
    | CrossProductDirection
    | ProjectedVectorToPlaneDirection
    | OriginTargetDirection
)
